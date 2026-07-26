#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importar_documento_externo.py — entrada de proposta, certidão, e-mail e afins.

    python scripts/gestao_documental/importar_documento_externo.py \
      --processo PA_031_2026 --arquivo proposta_fornecedor.pdf --categoria proposta

Documento externo não se mistura com o que o Charles gerou (item 17). O caminho
é sempre o mesmo, e passa por quarentena:

    98_QUARENTENA/ → hash → classificação → conferência de duplicidade e de
    pertencimento ao processo → nome padronizado → 03_DOCUMENTOS_EXTERNOS/<categoria>/

**O original nunca é alterado.** O arquivo entra por cópia — o que estava na
pasta de downloads continua lá, byte a byte igual —, o nome original fica
gravado no manifesto, e o conteúdo não é reformatado, convertido nem "limpo".

**Duas situações param o arquivo na quarentena**, com alerta, em vez de
classificá-lo: quando o documento aparenta ser de outro processo (item 21) e
quando a classificação não alcança confiança suficiente. Quarentena não é
castigo: é o lugar onde o arquivo espera decisão humana sem sujar a pasta
oficial.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from classificar_documento import Classificacao, classificar  # noqa: E402
from detectar_duplicados import duplicado_exato_no_processo  # noqa: E402
from hashes import sha256_arquivo  # noqa: E402
from manifesto import (  # noqa: E402
    AREA_EXTERNOS,
    AREA_QUARENTENA,
    OperacaoBloqueada,
    Processo,
    agora,
    evento,
    linha_log,
    preparar_console,
)
from nomes_arquivos import (  # noqa: E402
    CATEGORIAS_EXTERNAS,
    nome_externo,
    sanitizar_nome_arquivo,
)
from seguranca_repositorio import avaliar_destino  # noqa: E402
from transacoes import Transacao  # noqa: E402


@dataclass
class ResultadoImportacao:
    situacao: str = "pendente"  # classificado | em_quarentena | duplicado
    arquivo_original: str = ""
    destino: Optional[str] = None
    hash_sha256: str = ""
    classificacao: Optional[Classificacao] = None
    duplicado_de: Optional[str] = None
    alertas: list[str] = field(default_factory=list)
    pendencias: list[str] = field(default_factory=list)

    def texto(self) -> str:
        linhas = [f"situação: {self.situacao}", f"origem: {self.arquivo_original}"]
        if self.destino:
            linhas.append(f"destino: {self.destino}")
        if self.duplicado_de:
            linhas.append(f"idêntico ao já existente: {self.duplicado_de}")
        if self.classificacao:
            linhas.append(
                f"categoria: {self.classificacao.categoria} "
                f"({self.classificacao.confianca}, {self.classificacao.fonte_da_analise})"
            )
        for item in self.alertas:
            linhas.append(f"  [ALERTA] {item}")
        for item in self.pendencias:
            linhas.append(f"  [PENDÊNCIA] {item}")
        return "\n".join(linhas)


def metadados_externos(
    classificacao: Classificacao,
    *,
    nome_original: str,
    nome_padronizado: Optional[str],
    numero_processo: str,
    hash_sha256: str,
    fonte: Optional[str],
    email_origem: Optional[str],
    classificacao_sigilo: str,
    status_validacao: str,
    caminho_relativo: Optional[str],
    observacoes: str = "",
) -> dict[str, Any]:
    """Registro do item 19. Campo ausente é `null` + pendência, nunca invenção."""
    return {
        "documento_id": f"EXT_{hash_sha256[:12]}",
        "nome_original": nome_original,
        "nome_padronizado": nome_padronizado,
        "arquivo": caminho_relativo,
        "tipo": classificacao.tipo,
        "categoria": classificacao.categoria,
        "origem": classificacao.origem,
        "cnpj": classificacao.cnpj,
        "data_documento": classificacao.data_documento,
        "data_recebimento": datetime.now().date().isoformat(),
        "processo": numero_processo,
        "processos_citados": classificacao.processos_citados,
        "hash_sha256": hash_sha256,
        "fonte": fonte,
        "email_origem": email_origem,
        "classificacao": classificacao_sigilo,
        "status_validacao": status_validacao,
        "confianca_classificacao": classificacao.confianca,
        "fonte_da_analise": classificacao.fonte_da_analise,
        "texto_legivel": classificacao.texto_legivel,
        "pendencias": classificacao.pendencias,
        "alertas": classificacao.alertas,
        "observacoes": observacoes,
        "registrado_em": agora(),
    }


def importar(
    identificador: str,
    arquivo: Path | str,
    *,
    categoria: Optional[str] = None,
    origem: Optional[str] = None,
    fonte: Optional[str] = None,
    email_origem: Optional[str] = None,
    descricao: Optional[str] = None,
    observacoes: str = "",
    classificacao_sigilo: str = "uso_interno",
    responsavel: str = "Charles",
    base: Optional[Path | str] = None,
    forcar: bool = False,
) -> ResultadoImportacao:
    """Importa um documento externo. O arquivo de origem permanece intacto."""
    processo = Processo.abrir(identificador, base)
    origem_arquivo = Path(arquivo)
    if not origem_arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {origem_arquivo}")

    dados_processo = processo.ler_processo()
    numero_processo = dados_processo.get("numero") or processo.identificador
    digest = sha256_arquivo(origem_arquivo)

    resultado = ResultadoImportacao(
        arquivo_original=str(origem_arquivo), hash_sha256=digest
    )

    # -- 1. duplicidade exata (item 20) ------------------------------------ #
    ja_existe = duplicado_exato_no_processo(processo, origem_arquivo)
    if ja_existe and not forcar:
        with open(processo.arquivo_log, "a", encoding="utf-8", newline="\n") as log:
            log.write(linha_log(evento(
                "duplicado_descartado",
                arquivo=ja_existe,
                hash_sha256=digest,
                responsavel=responsavel,
                motivo=f"tentativa de importar novamente {origem_arquivo.name}",
            )) + "\n")
        resultado.situacao = "duplicado"
        resultado.duplicado_de = ja_existe
        resultado.alertas.append(
            f"arquivo idêntico já consta do processo em {ja_existe}; nada foi copiado"
        )
        return resultado

    # -- 2. classificação -------------------------------------------------- #
    analise = classificar(
        origem_arquivo,
        numero_processo=numero_processo,
        categoria_informada=categoria,
        origem_informada=origem,
    )
    resultado.classificacao = analise
    resultado.pendencias = list(analise.pendencias)
    resultado.alertas = list(analise.alertas)

    manda_para_quarentena = bool(analise.alertas) or (
        analise.confianca == "baixa" and not categoria
    )

    # -- 3. destino --------------------------------------------------------- #
    if manda_para_quarentena:
        pasta = processo.garantir(AREA_QUARENTENA)
        nome_final = sanitizar_nome_arquivo(origem_arquivo.name)
        status_validacao = "em_quarentena"
    else:
        pasta = processo.garantir(AREA_EXTERNOS, CATEGORIAS_EXTERNAS[analise.categoria])
        nome_final = nome_externo(
            analise.data_documento,
            analise.origem,
            analise.tipo,
            descricao,
            origem_arquivo.suffix,
        )
        status_validacao = "confirmado" if analise.confianca == "alta" else "a_confirmar"

    destino = pasta / nome_final
    if destino.exists():
        destino = pasta / f"{destino.stem}_{digest[:8]}{destino.suffix}"

    avaliacao = avaliar_destino(destino, sensivel=True)
    for alerta in avaliacao.alertas:
        if alerta.gravidade in ("bloqueio", "aviso"):
            resultado.alertas.append(alerta.mensagem)
    if avaliacao.bloqueado:
        raise OperacaoBloqueada(
            "Importação recusada por segurança — documento externo iria para um "
            "repositório tratado como público e versionável:\n" + avaliacao.texto()
        )

    # -- 4. gravação transacional ------------------------------------------ #
    manifesto = processo.ler_documentos()
    with Transacao(processo.temporarios, f"importar {origem_arquivo.name}") as tx:
        tx.copiar(origem_arquivo, destino)  # cópia: o original não se toca
        registro = metadados_externos(
            analise,
            nome_original=origem_arquivo.name,
            nome_padronizado=None if manda_para_quarentena else nome_final,
            numero_processo=numero_processo,
            hash_sha256=digest,
            fonte=fonte,
            email_origem=email_origem,
            classificacao_sigilo=classificacao_sigilo,
            status_validacao=status_validacao,
            caminho_relativo=processo.relativo(destino),
            observacoes=observacoes,
        )
        manifesto.setdefault("documentos_externos", []).append(registro)
        manifesto["atualizado_em"] = agora()
        tx.gravar_json(processo.arquivo_documentos, manifesto)
        tx.acrescentar_linha(processo.arquivo_log, linha_log(evento(
            "arquivo_colocado_em_quarentena" if manda_para_quarentena
            else "documento_externo_classificado",
            documento=registro["documento_id"],
            arquivo=registro["arquivo"],
            hash_sha256=digest,
            responsavel=responsavel,
            motivo="; ".join(analise.alertas) or f"importação de {origem_arquivo.name}",
            categoria=analise.categoria,
            nome_original=origem_arquivo.name,
        )))
        from gerar_painel import montar_painel

        tx.gravar_texto(processo.arquivo_painel, montar_painel(processo, manifesto=manifesto))

    resultado.situacao = "em_quarentena" if manda_para_quarentena else "classificado"
    resultado.destino = processo.relativo(destino)
    if manda_para_quarentena:
        resultado.alertas.append(
            "documento mantido em 98_QUARENTENA/ até confirmação humana; "
            "reimporte com --categoria depois de conferir"
        )
    return resultado


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Importa um documento externo para o processo, preservando o original."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--arquivo", required=True, action="append",
                            help="pode ser repetido para importar vários")
    analisador.add_argument("--categoria",
                            help=f"uma de: {', '.join(CATEGORIAS_EXTERNAS)}")
    analisador.add_argument("--origem", help="fornecedor ou órgão de origem")
    analisador.add_argument("--fonte", help="email | protocolo | portal | entrega_fisica")
    analisador.add_argument("--email-origem")
    analisador.add_argument("--descricao")
    analisador.add_argument("--observacoes", default="")
    analisador.add_argument("--sigilo", default="uso_interno",
                            choices=["publico", "uso_interno", "restrito"])
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--forcar", action="store_true",
                            help="importa mesmo havendo duplicata exata")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    problemas = 0
    for caminho in argumentos.arquivo:
        try:
            resultado = importar(
                argumentos.processo, caminho,
                categoria=argumentos.categoria, origem=argumentos.origem,
                fonte=argumentos.fonte, email_origem=argumentos.email_origem,
                descricao=argumentos.descricao, observacoes=argumentos.observacoes,
                classificacao_sigilo=argumentos.sigilo,
                responsavel=argumentos.responsavel, base=argumentos.base,
                forcar=argumentos.forcar,
            )
        except Exception as erro:  # noqa: BLE001
            print(f"ERRO ({caminho}): {erro}", file=sys.stderr)
            problemas += 1
            continue
        print(resultado.texto())
        print()
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
