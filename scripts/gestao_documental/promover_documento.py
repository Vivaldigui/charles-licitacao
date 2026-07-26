#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
promover_documento.py — muda o estado de um documento (itens 6 e 16 do escopo).

    python scripts/gestao_documental/promover_documento.py \
      --processo PA_031_2026 --tipo TR --status aprovado \
      --responsavel "Agente de contratação"

Promover não é editar um campo de JSON: é o momento em que o documento muda de
natureza jurídica, e cada degrau tem consequência material.

* **aprovado** — a peça sai de `01_EM_ELABORACAO/` e passa a documento oficial
  da fase, em `02_DOCUMENTOS_OFICIAIS/`. Exige que não haja campo pendente.
* **assinado** — exige o arquivo assinado (`--arquivo`), que entra em
  `05_ASSINADOS/` como REPRESENTAÇÃO da mesma versão (item 9), não como versão
  nova. A partir daqui o documento é imutável.
* **publicado** — registra o comprovante em `04_PUBLICACOES/`. Também imutável.

**Retificação** (`--retificar`) é a única porta de saída de assinado e
publicado. Ela não sobrescreve nada: preserva a peça imutável no histórico,
abre uma versão nova em revisão e grava a relação entre as duas.

O que este script NÃO faz: julgar se o documento merece ser aprovado. Ele
verifica o verificável — campos `[PREENCHER]` e `{{...}}`, controle de
alterações, comentários, pertencimento ao processo — e diz o que não conseguiu
verificar. O mérito é do responsável, que fica nominalmente registrado.
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from arquivar_versao import arquivar_na_transacao  # noqa: E402
from hashes import (  # noqa: E402
    campos_pendentes,
    sha256_arquivo,
    verificacao_de_pendencias_possivel,
)
from locks import LockDocumento  # noqa: E402
from manifesto import (  # noqa: E402
    AREA_PUBLICACOES,
    OperacaoBloqueada,
    Processo,
    STATUS_IMUTAVEIS,
    agora,
    evento,
    linha_log,
    numeros_de_processo,
    preparar_console,
    promocao_permitida,
    validar_status,
)
from nomes_arquivos import (  # noqa: E402
    nome_canonico,
    nome_canonico_assinado,
    obter_tipo,
)
from transacoes import Transacao  # noqa: E402

VEICULO_PADRAO = {
    "AVISO": "AVISOS",
    # Item 27: o pacote do Aviso Completo é artefato derivado e mora em PACOTES.
    "AVISO_COMPLETO": "PACOTES",
    "EXTRATO": "EXTRATOS",
}
VEICULOS = ("AVISOS", "EXTRATOS", "PNCP", "DIARIO_OFICIAL", "PACOTES")


@dataclass
class Verificacao:
    """O que foi conferido antes de promover — e o que não foi."""

    impeditivos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    nao_verificado: list[str] = field(default_factory=list)

    @property
    def aprovado(self) -> bool:
        return not self.impeditivos

    def texto(self) -> str:
        linhas = []
        for item in self.impeditivos:
            linhas.append(f"  [IMPEDITIVO] {item}")
        for item in self.avisos:
            linhas.append(f"  [AVISO] {item}")
        for item in self.nao_verificado:
            linhas.append(f"  [NÃO VERIFICADO] {item}")
        return "\n".join(linhas)


def verificar_documento(
    processo: Processo, tipo: str, caminho: Path, dados_processo: dict[str, Any]
) -> Verificacao:
    """Checagens objetivas do item 16. Nada de opinião sobre o mérito."""
    resultado = Verificacao()
    if not caminho.exists():
        resultado.impeditivos.append(f"arquivo não encontrado: {caminho}")
        return resultado

    if verificacao_de_pendencias_possivel(caminho):
        pendentes = campos_pendentes(caminho)
        if pendentes:
            amostra = ", ".join(sorted(set(pendentes))[:6])
            resultado.impeditivos.append(
                f"{len(pendentes)} campo(s) por preencher: {amostra}"
            )
    else:
        resultado.nao_verificado.append(
            f"campos pendentes: {caminho.suffix or 'formato'} sem extrator de texto "
            f"nesta base"
        )

    if caminho.suffix.lower() in (".docx", ".docm"):
        resultado.avisos.extend(_conferir_pacote_docx(caminho))
        resultado.impeditivos.extend(_conferir_processo_correto(caminho, dados_processo))
    else:
        resultado.nao_verificado.append(
            "comentários, controle de alterações e pertencimento ao processo: "
            "verificáveis apenas em DOCX"
        )
    return resultado


def _conferir_pacote_docx(caminho: Path) -> list[str]:
    """Comentário e controle de alterações são informados, nunca resolvidos."""
    avisos: list[str] = []
    try:
        with zipfile.ZipFile(caminho, "r") as pacote:
            nomes = pacote.namelist()
            if "word/comments.xml" in nomes:
                avisos.append("o documento contém comentários internos")
            if "word/document.xml" in nomes:
                xml = pacote.read("word/document.xml").decode("utf-8", "ignore")
                marcas = len(re.findall(r"<w:(ins|del|moveFrom|moveTo)\b", xml))
                if marcas:
                    avisos.append(
                        f"o documento tem {marcas} marca(s) de controle de alterações"
                    )
                if re.search(r"\bOU\b\s*[\[\(]", xml):
                    avisos.append("há blocos alternativos ('OU') aparentemente abertos")
    except zipfile.BadZipFile:
        avisos.append("o arquivo não é um DOCX válido (pacote ilegível)")
    return avisos


def _conferir_processo_correto(caminho: Path, dados_processo: dict[str, Any]) -> list[str]:
    """
    O documento cita número de processo diferente do seu? (itens 16 e 21)

    Só acusa quando encontra número DIFERENTE e nenhum igual: documento que não
    cita processo nenhum não é indício de nada.
    """
    from hashes import extrair_texto, ConteudoIndisponivel

    numero = str(dados_processo.get("numero") or "")
    esperados = numeros_de_processo(numero)
    if not esperados:
        return []
    try:
        texto = " ".join(extrair_texto(caminho))
    except (ConteudoIndisponivel, OSError):
        return []
    encontrados = numeros_de_processo(texto)
    if encontrados and not (encontrados & esperados):
        return [
            f"o documento cita processo(s) {', '.join(sorted(encontrados))}, e este "
            f"processo é {', '.join(sorted(esperados))}. Confirme se a peça é deste "
            f"processo antes de promover (item 21)."
        ]
    return []


def _destino_publicacao(processo: Processo, tipo: str, veiculo: Optional[str]) -> Path:
    escolhido = (veiculo or VEICULO_PADRAO.get(tipo, "DIARIO_OFICIAL")).upper()
    if escolhido not in VEICULOS:
        raise ValueError(f"Veículo de publicação desconhecido: {veiculo}. Use {VEICULOS}.")
    if escolhido == "PACOTES":
        # Cada pacote tem pasta própria: o ZIP e as cópias de publicação não se
        # espalham pela raiz do processo (item 27).
        return processo.garantir(AREA_PUBLICACOES, escolhido, tipo)
    return processo.garantir(AREA_PUBLICACOES, escolhido)


def promover(
    identificador: str,
    tipo: str,
    novo_status: str,
    *,
    responsavel: str = "Charles",
    motivo: str = "",
    arquivo: Optional[Path | str] = None,
    veiculo: Optional[str] = None,
    base: Optional[Path | str] = None,
    ignorar_avisos: bool = False,
) -> dict[str, Any]:
    """Executa a promoção. Devolve um relatório do que foi feito e conferido."""
    processo = Processo.abrir(identificador, base)
    chave = obter_tipo(tipo).tipo
    novo_status = validar_status(novo_status)

    with LockDocumento(processo.raiz, processo.identificador, chave):
        manifesto = processo.ler_documentos()
        registro = manifesto["documentos"].get(chave)
        if not registro:
            raise OperacaoBloqueada(
                f"Não há {chave} registrado neste processo. Registre-o antes de promover."
            )
        status_atual = registro.get("status", "em_elaboracao")

        if status_atual == novo_status:
            raise OperacaoBloqueada(f"O {chave} já está '{novo_status}'.")
        if not promocao_permitida(status_atual, novo_status):
            raise OperacaoBloqueada(
                f"Promoção de '{status_atual}' para '{novo_status}' não está prevista "
                f"no ciclo de vida. Se o caso é mudar documento já assinado ou "
                f"publicado, use --retificar."
            )
        if novo_status == "assinado" and not arquivo:
            raise OperacaoBloqueada(
                "Promover para 'assinado' exige o arquivo assinado (--arquivo): a "
                "assinatura é uma representação real, não um campo de status."
            )

        editavel = processo.absoluto(registro["arquivo_atual"]) if registro.get("arquivo_atual") else None
        alvo = Path(arquivo) if arquivo else editavel
        if alvo is None:
            raise OperacaoBloqueada(f"O {chave} não tem arquivo corrente para promover.")

        verificacao = verificar_documento(processo, chave, alvo, processo.ler_processo())
        if not verificacao.aprovado:
            raise OperacaoBloqueada(
                f"Promoção do {chave} para '{novo_status}' recusada:\n"
                + verificacao.texto()
            )
        if verificacao.avisos and not ignorar_avisos and novo_status in ("aprovado", "assinado", "publicado"):
            raise OperacaoBloqueada(
                f"Promoção do {chave} para '{novo_status}' interrompida por ressalvas:\n"
                + verificacao.texto()
                + "\n  Resolva as ressalvas ou repita com --ignorar-avisos, "
                  "assumindo-as expressamente."
            )

        movimentos: list[str] = []
        with Transacao(processo.temporarios, f"promover {chave} -> {novo_status}") as tx:
            if novo_status == "aprovado" and editavel is not None:
                destino = processo.garantir(
                    *processo.area_corrente(chave, "aprovado").relative_to(processo.raiz).parts
                ) / nome_canonico(chave, editavel.suffix)
                if destino != editavel:
                    anterior = registro["arquivo_atual"]
                    tx.mover(editavel, destino)
                    registro["arquivo_atual"] = processo.relativo(destino)
                    # A peça é a mesma: só mudou de área. Toda representação que
                    # apontava para o caminho antigo passa a apontar para o novo.
                    for rotulo, valor in list((registro.get("representacoes") or {}).items()):
                        if valor == anterior:
                            registro["representacoes"][rotulo] = registro["arquivo_atual"]
                    movimentos.append(f"documento oficial: {registro['arquivo_atual']}")

            elif novo_status == "assinado":
                destino = processo.garantir(
                    "05_ASSINADOS", obter_tipo(chave).pasta_assinados
                ) / nome_canonico_assinado(chave, Path(alvo).suffix)
                tx.copiar(alvo, destino)
                registro["representacoes"]["assinado"] = processo.relativo(destino)
                registro["hash_assinado"] = sha256_arquivo(destino)
                movimentos.append(f"representação assinada: {registro['representacoes']['assinado']}")

            elif novo_status == "publicado":
                pasta = _destino_publicacao(processo, chave, veiculo)
                origem_publicacao = Path(alvo)
                destino = pasta / f"{chave}{origem_publicacao.suffix.lower()}"
                tx.copiar(origem_publicacao, destino)
                registro.setdefault("publicacoes", []).append({
                    "arquivo": processo.relativo(destino),
                    "veiculo": (veiculo or VEICULO_PADRAO.get(chave, "DIARIO_OFICIAL")).upper(),
                    "versao": registro.get("versao_atual"),
                    "hash_sha256": sha256_arquivo(destino),
                    "publicado_em": agora(),
                    "responsavel": responsavel,
                })
                movimentos.append(f"publicação registrada: {processo.relativo(destino)}")

            registro["status"] = novo_status
            registro["atualizado_em"] = agora()
            registro.setdefault("promocoes", []).append({
                "de": status_atual,
                "para": novo_status,
                "responsavel": responsavel,
                "motivo": motivo,
                "data": agora(),
                "ressalvas": verificacao.avisos,
                "nao_verificado": verificacao.nao_verificado,
            })
            manifesto["atualizado_em"] = agora()
            tx.gravar_json(processo.arquivo_documentos, manifesto)

            acao = {
                "assinado": "documento_assinado",
                "publicado": "documento_publicado",
            }.get(novo_status, "documento_promovido")
            tx.acrescentar_linha(processo.arquivo_log, linha_log(evento(
                acao,
                documento=chave,
                versao=registro.get("versao_atual"),
                arquivo=registro.get("arquivo_atual"),
                hash_sha256=registro.get("hash_sha256"),
                responsavel=responsavel,
                motivo=motivo or f"promoção de {status_atual} para {novo_status}",
                de=status_atual,
                para=novo_status,
            )))
            _regerar_painel(processo, tx, manifesto)

    return {
        "documento": chave,
        "de": status_atual,
        "para": novo_status,
        "movimentos": movimentos,
        "ressalvas": verificacao.avisos,
        "nao_verificado": verificacao.nao_verificado,
    }


def retificar(
    identificador: str,
    tipo: str,
    arquivo: Path | str,
    motivo: str,
    *,
    responsavel: str = "Charles",
    base: Optional[Path | str] = None,
) -> dict[str, Any]:
    """
    Retificação de documento assinado ou publicado (item 6).

    O imutável não é tocado: ele desce ao histórico com o status que tinha, e o
    substitutivo nasce como versão nova, em revisão, apontando para a versão
    retificada. Publicar de novo é etapa seguinte e separada — este passo não
    presume republicação.
    """
    processo = Processo.abrir(identificador, base)
    chave = obter_tipo(tipo).tipo
    if not motivo:
        raise OperacaoBloqueada("Retificação exige motivo expresso.")
    origem = Path(arquivo)
    if not origem.is_file():
        raise FileNotFoundError(f"Arquivo da retificação não encontrado: {origem}")

    with LockDocumento(processo.raiz, processo.identificador, chave):
        manifesto = processo.ler_documentos()
        registro = manifesto["documentos"].get(chave)
        if not registro:
            raise OperacaoBloqueada(f"Não há {chave} registrado neste processo.")
        status_atual = registro.get("status")
        if status_atual not in STATUS_IMUTAVEIS:
            raise OperacaoBloqueada(
                f"Retificação se aplica a documento assinado ou publicado. O {chave} "
                f"está '{status_atual}': use registrar_documento.py para substituí-lo."
            )

        versao_retificada = int(registro.get("versao_atual") or 1)
        nova_versao = versao_retificada + 1

        with Transacao(processo.temporarios, f"retificar {chave}") as tx:
            arquivada = arquivar_na_transacao(
                processo, tx, chave, registro,
                f"retificação: {motivo}",
                responsavel=responsavel,
                permitir_imutavel=True,
            )
            if arquivada is not None:
                arquivada["substituido_por_versao"] = nova_versao
                arquivada["retificado"] = True

            destino = processo.area_corrente(chave, "em_revisao") / nome_canonico(
                chave, origem.suffix
            )
            destino.parent.mkdir(parents=True, exist_ok=True)
            tx.copiar(origem, destino)

            registro.update({
                "versao_atual": nova_versao,
                "status": "em_revisao",
                "arquivo_atual": processo.relativo(destino),
                "hash_sha256": sha256_arquivo(destino),
                "atualizado_em": agora(),
                "substitui_versao": versao_retificada,
                "retifica_versao": versao_retificada,
                "motivo_ultima_alteracao": f"retificação: {motivo}",
            })
            registro["representacoes"] = {
                "docx": registro["arquivo_atual"] if destino.suffix.lower() in (".docx", ".docm") else None,
                "pdf": None,
                "assinado": None,
            }
            manifesto["atualizado_em"] = agora()
            tx.gravar_json(processo.arquivo_documentos, manifesto)
            tx.acrescentar_linha(processo.arquivo_log, linha_log(evento(
                "documento_retificado",
                documento=chave,
                versao=nova_versao,
                arquivo=registro["arquivo_atual"],
                hash_sha256=registro["hash_sha256"],
                responsavel=responsavel,
                motivo=motivo,
                retifica_versao=versao_retificada,
                status_retificado=status_atual,
            )))
            _regerar_painel(processo, tx, manifesto)

    return {
        "documento": chave,
        "versao_retificada": versao_retificada,
        "nova_versao": nova_versao,
        "arquivo": registro["arquivo_atual"],
        "observacao": (
            "O documento retificado permanece íntegro em 90_HISTORICO/. A nova "
            "publicação, quando cabível, é ato separado."
        ),
    }


def _regerar_painel(processo: Processo, tx: Transacao, manifesto: dict) -> None:
    from gerar_painel import montar_painel

    tx.gravar_texto(processo.arquivo_painel, montar_painel(processo, manifesto=manifesto))


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Promove um documento no ciclo de vida, ou o retifica."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--tipo", required=True)
    analisador.add_argument("--status", help="novo status (ex.: aprovado, assinado)")
    analisador.add_argument("--retificar", action="store_true",
                            help="retifica documento assinado ou publicado")
    analisador.add_argument("--arquivo", help="representação assinada, publicada ou retificadora")
    analisador.add_argument("--motivo", default="")
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--veiculo", choices=VEICULOS, help="destino da publicação")
    analisador.add_argument("--ignorar-avisos", action="store_true")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    try:
        if argumentos.retificar:
            if not argumentos.arquivo:
                raise SystemExit("ERRO: --retificar exige --arquivo com o substitutivo.")
            relatorio = retificar(
                argumentos.processo, argumentos.tipo, argumentos.arquivo,
                argumentos.motivo, responsavel=argumentos.responsavel,
                base=argumentos.base,
            )
        else:
            if not argumentos.status:
                raise SystemExit("ERRO: informe --status ou --retificar.")
            relatorio = promover(
                argumentos.processo, argumentos.tipo, argumentos.status,
                responsavel=argumentos.responsavel, motivo=argumentos.motivo,
                arquivo=argumentos.arquivo, veiculo=argumentos.veiculo,
                base=argumentos.base, ignorar_avisos=argumentos.ignorar_avisos,
            )
    except SystemExit:
        raise
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    for chave, valor in relatorio.items():
        if isinstance(valor, list):
            for item in valor:
                print(f"  {chave}: {item}")
        else:
            print(f"{chave}: {valor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
