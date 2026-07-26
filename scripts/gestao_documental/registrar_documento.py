#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
registrar_documento.py — a camada final comum de TODOS os geradores (item 26).

Nenhum gerador grava direto na pasta do processo. Todos entregam um arquivo
temporário aqui, e é este módulo que decide se ele vira a versão vigente:

    registrar_saida_gerada(processo, tipo_documento, arquivo_temporario,
                           minuta_origem, motivo, status)

O fluxo é o do item 14, na ordem:

    sessão temporária → validação → campos pendentes → hash → comparação com o
    atual → decisão de alteração real → arquivamento da anterior → movimento
    atômico → manifesto → log → painel → limpeza.

Três recusas que este módulo pratica sem negociar:

* **documento assinado ou publicado não é sobrescrito** (item 6, regra 34);
* **conteúdo idêntico não vira versão nova** (item 15) — a geração é registrada
  como "sem alteração" e o arquivo atual permanece;
* **erro no meio não deixa estado parcial** (itens 14 e 29) — a transação
  desfaz, o documento anterior continua onde estava, e a falha é registrada.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from arquivar_versao import arquivar_na_transacao  # noqa: E402
from hashes import (  # noqa: E402
    Comparacao,
    campos_pendentes,
    comparar_documentos,
    hash_conteudo,
    sha256_arquivo,
    verificacao_de_pendencias_possivel,
)
from locks import LockDocumento  # noqa: E402
from manifesto import (  # noqa: E402
    OperacaoBloqueada,
    Processo,
    STATUS_IMUTAVEIS,
    STATUS_PROTEGIDOS,
    agora,
    evento,
    linha_log,
    preparar_console,
    validar_status,
)
from nomes_arquivos import existe, nome_canonico, obter_tipo  # noqa: E402
from seguranca_repositorio import exigir_destino_seguro  # noqa: E402
from transacoes import Transacao  # noqa: E402


@dataclass
class ResultadoRegistro:
    """O que aconteceu — em termos verificáveis, sem eufemismo."""

    tipo: str
    situacao: str  # "registrado" | "sem_alteracao" | "bloqueado"
    versao: Optional[int] = None
    arquivo: Optional[str] = None
    hash_sha256: Optional[str] = None
    versao_anterior_arquivada: Optional[str] = None
    campos_pendentes: list[str] = field(default_factory=list)
    pendencias_verificadas: bool = True
    alertas: list[str] = field(default_factory=list)
    comparacao: Optional[Comparacao] = None

    @property
    def houve_gravacao(self) -> bool:
        return self.situacao == "registrado"

    def texto(self) -> str:
        linhas = [f"{self.tipo}: {self.situacao}"]
        if self.versao is not None:
            linhas.append(f"  versão: {self.versao}")
        if self.arquivo:
            linhas.append(f"  arquivo: {self.arquivo}")
        if self.versao_anterior_arquivada:
            linhas.append(f"  versão anterior arquivada em: {self.versao_anterior_arquivada}")
        if self.comparacao:
            linhas.append(f"  comparação: {self.comparacao.resumo}")
        if not self.pendencias_verificadas:
            linhas.append("  campos pendentes: NÃO VERIFICADOS (formato sem extrator de texto)")
        elif self.campos_pendentes:
            amostra = ", ".join(sorted(set(self.campos_pendentes))[:5])
            linhas.append(
                f"  campos pendentes: {len(self.campos_pendentes)} ({amostra})"
            )
        for alerta in self.alertas:
            linhas.append(f"  ! {alerta}")
        return "\n".join(linhas)


def abrir_sessao_temporaria(processo: Processo, rotulo: str = "geracao") -> Path:
    """Sessão isolada em `99_TEMPORARIOS/` (item 14, passo 1)."""
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    sessao = processo.temporarios / f"{rotulo}_{carimbo}_{uuid.uuid4().hex[:6]}"
    sessao.mkdir(parents=True, exist_ok=True)
    return sessao


def registrar_saida_gerada(
    processo: str | Processo,
    tipo_documento: str,
    arquivo_temporario: Path | str,
    minuta_origem: Optional[str] = None,
    motivo: str = "",
    status: str = "em_elaboracao",
    *,
    responsavel: str = "Charles",
    validacao: Optional[dict[str, Any]] = None,
    base: Optional[Path | str] = None,
    exigir_sem_pendencias: bool = False,
    forcar_nova_versao: bool = False,
) -> ResultadoRegistro:
    """
    Interface única de gravação (item 26). Todo gerador termina aqui.

    `arquivo_temporario` é COPIADO para a sessão temporária do processo antes de
    qualquer coisa: o arquivo do gerador nunca é consumido nem alterado, e uma
    falha no meio não o perde.

    `forcar_nova_versao` existe para o caso em que o conteúdo textual é idêntico
    mas a mudança importa (uma correção de formatação que se quer versionar).
    Precisa ser pedido: o padrão é não criar versão sem alteração real (item 15).
    """
    processo = processo if isinstance(processo, Processo) else Processo.abrir(processo, base)
    descricao = obter_tipo(tipo_documento)
    tipo = descricao.tipo
    status = validar_status(status)
    origem = Path(arquivo_temporario)
    if not origem.is_file():
        raise FileNotFoundError(f"Arquivo a registrar não encontrado: {origem}")

    alertas: list[str] = []

    with LockDocumento(processo.raiz, processo.identificador, tipo) as lock:
        if lock.recuperado:
            alertas.append(f"lock abandonado recuperado ({lock.recuperado})")
        sessao = abrir_sessao_temporaria(processo, f"registrar_{tipo}")
        candidato = sessao / f"{tipo}{origem.suffix.lower()}"
        shutil.copy2(origem, candidato)

        try:
            resultado = _registrar_candidato(
                processo=processo,
                tipo=tipo,
                candidato=candidato,
                minuta_origem=minuta_origem,
                motivo=motivo,
                status=status,
                responsavel=responsavel,
                validacao=validacao,
                exigir_sem_pendencias=exigir_sem_pendencias,
                forcar_nova_versao=forcar_nova_versao,
                alertas=alertas,
            )
        except Exception as erro:
            _registrar_falha(processo, tipo, erro, responsavel)
            raise
        finally:
            shutil.rmtree(sessao, ignore_errors=True)

        if lock.recuperado:
            processo_log = evento(
                "lock_recuperado",
                documento=tipo,
                responsavel=responsavel,
                motivo=lock.recuperado,
            )
            with open(processo.arquivo_log, "a", encoding="utf-8", newline="\n") as log:
                log.write(linha_log(processo_log) + "\n")
    return resultado


def _registrar_falha(processo: Processo, tipo: str, erro: Exception, responsavel: str) -> None:
    """Falha vira evento. Erro silencioso é proibido (regra 34)."""
    try:
        with open(processo.arquivo_log, "a", encoding="utf-8", newline="\n") as log:
            log.write(linha_log(evento(
                "erro_de_validacao",
                documento=tipo,
                responsavel=responsavel,
                motivo=f"{type(erro).__name__}: {erro}",
            )) + "\n")
    except OSError:
        pass


def _registrar_candidato(
    *,
    processo: Processo,
    tipo: str,
    candidato: Path,
    minuta_origem: Optional[str],
    motivo: str,
    status: str,
    responsavel: str,
    validacao: Optional[dict[str, Any]],
    exigir_sem_pendencias: bool,
    forcar_nova_versao: bool,
    alertas: list[str],
) -> ResultadoRegistro:
    manifesto = processo.ler_documentos()
    registro = manifesto["documentos"].get(tipo)
    dados_processo = processo.ler_processo()

    # -- 1. estados imutáveis e protegidos (item 6) ------------------------ #
    if registro:
        status_atual = registro.get("status", "em_elaboracao")
        if status_atual in STATUS_IMUTAVEIS:
            raise OperacaoBloqueada(
                f"O {tipo} está '{status_atual}' — imutável. Nada foi alterado. "
                f"Para mudar o conteúdo, use promover_documento.py --retificar, "
                f"que cria documento substitutivo e registra a relação entre as "
                f"versões (item 6 do escopo)."
            )
        if status_atual in STATUS_PROTEGIDOS and not motivo:
            raise OperacaoBloqueada(
                f"O {tipo} está aprovado. Substituição de documento aprovado exige "
                f"motivo e responsável explícitos (--motivo)."
            )

    # -- 2. campos pendentes (itens 14 e 16) ------------------------------- #
    pendencias_verificaveis = verificacao_de_pendencias_possivel(candidato)
    pendentes = campos_pendentes(candidato) if pendencias_verificaveis else []
    if not pendencias_verificaveis:
        alertas.append(
            f"campos pendentes não verificados: {candidato.suffix or 'sem extensão'} "
            f"não tem extrator de texto nesta base"
        )
    if pendentes and exigir_sem_pendencias:
        raise OperacaoBloqueada(
            f"O {tipo} tem {len(pendentes)} campo(s) por preencher "
            f"({', '.join(sorted(set(pendentes))[:5])}). Registro recusado no modo "
            f"estrito."
        )

    # -- 3. destino e segurança -------------------------------------------- #
    destino = processo.area_corrente(tipo, status) / nome_canonico(tipo, candidato.suffix)
    exigir_destino_seguro(destino, sensivel=False)

    # -- 4. alteração real? (item 15) -------------------------------------- #
    comparacao: Optional[Comparacao] = None
    atual = processo.absoluto(registro["arquivo_atual"]) if registro and registro.get("arquivo_atual") else None
    if atual is not None and existe(atual):
        comparacao = comparar_documentos(candidato, atual)
        if not comparacao.houve_alteracao and not forcar_nova_versao:
            with open(processo.arquivo_log, "a", encoding="utf-8", newline="\n") as log:
                log.write(linha_log(evento(
                    "geracao_sem_alteracao",
                    documento=tipo,
                    versao=registro.get("versao_atual"),
                    arquivo=registro.get("arquivo_atual"),
                    hash_sha256=registro.get("hash_sha256"),
                    responsavel=responsavel,
                    motivo=motivo or "geração idêntica à versão vigente",
                    detalhe=comparacao.resumo,
                )) + "\n")
            return ResultadoRegistro(
                tipo=tipo,
                situacao="sem_alteracao",
                versao=registro.get("versao_atual"),
                arquivo=registro.get("arquivo_atual"),
                hash_sha256=registro.get("hash_sha256"),
                campos_pendentes=pendentes,
                pendencias_verificadas=pendencias_verificaveis,
                alertas=alertas + [
                    "nenhuma versão criada: " + comparacao.resumo
                ],
                comparacao=comparacao,
            )

    # -- 5. gravação transacional (itens 14 e 29) -------------------------- #
    nova_versao = int(registro.get("versao_atual", 0)) + 1 if registro else 1
    arquivada: Optional[dict[str, Any]] = None

    with Transacao(processo.temporarios, f"registrar {tipo} v{nova_versao}") as tx:
        if registro is None:
            registro = _registro_novo(processo, tipo, dados_processo)
            manifesto["documentos"][tipo] = registro
        else:
            arquivada = arquivar_na_transacao(
                processo, tx, tipo, registro,
                motivo or "substituição por nova versão",
                responsavel=responsavel,
            )
            if arquivada is not None:
                # Item 6: o substituído aponta para quem o substituiu.
                arquivada["substituido_por_versao"] = nova_versao

        tx.mover(candidato, destino)
        hash_novo = sha256_arquivo(destino)

        registro.update({
            "versao_atual": nova_versao,
            "status": status,
            "arquivo_atual": processo.relativo(destino),
            "hash_sha256": hash_novo,
            "hash_conteudo": hash_conteudo(destino),
            "atualizado_em": agora(),
            "gerado_por": responsavel,
            "minuta_origem": minuta_origem or registro.get("minuta_origem"),
            "substitui_versao": nova_versao - 1 if nova_versao > 1 else None,
            "motivo_ultima_alteracao": motivo or "",
            "validacao": _montar_validacao(validacao, pendentes, pendencias_verificaveis),
        })
        # Item 9: representação, não versão. `docx` é a chave da peça editável,
        # qualquer que seja o formato editável; PDF entra na chave própria.
        chave_representacao = "pdf" if destino.suffix.lower() == ".pdf" else "docx"
        registro["representacoes"][chave_representacao] = registro["arquivo_atual"]
        manifesto["atualizado_em"] = agora()
        tx.gravar_json(processo.arquivo_documentos, manifesto)

        tx.acrescentar_linha(
            processo.arquivo_log,
            linha_log(evento(
                "documento_gerado" if nova_versao == 1 else "documento_substituido",
                documento=tipo,
                versao=nova_versao,
                arquivo=registro["arquivo_atual"],
                hash_sha256=hash_novo,
                responsavel=responsavel,
                motivo=motivo or ("primeira geração" if nova_versao == 1 else "nova versão"),
                status=status,
            )),
        )
        _atualizar_processo_json(processo, tx, manifesto)
        _regerar_painel(processo, tx, manifesto)

    return ResultadoRegistro(
        tipo=tipo,
        situacao="registrado",
        versao=nova_versao,
        arquivo=registro["arquivo_atual"],
        hash_sha256=registro["hash_sha256"],
        versao_anterior_arquivada=(arquivada or {}).get("arquivo"),
        campos_pendentes=pendentes,
        pendencias_verificadas=pendencias_verificaveis,
        alertas=alertas,
        comparacao=comparacao,
    )


def _registro_novo(processo: Processo, tipo: str, dados_processo: dict) -> dict[str, Any]:
    descricao = obter_tipo(tipo)
    return {
        "titulo": descricao.titulo,
        "versao_atual": 0,
        "status": "em_elaboracao",
        "arquivo_atual": None,
        "hash_sha256": None,
        "hash_conteudo": None,
        "criado_em": agora(),
        "atualizado_em": agora(),
        "gerado_por": "Charles",
        "minuta_origem": None,
        "processo": dados_processo.get("numero") or processo.identificador,
        "fase": descricao.fase,
        "substitui_versao": None,
        "motivo_ultima_alteracao": "",
        "validacao": {},
        "representacoes": {"docx": None, "pdf": None, "assinado": None},
        "historico": [],
    }


def _montar_validacao(
    validacao: Optional[dict[str, Any]], pendentes: list[str], verificaveis: bool
) -> dict[str, Any]:
    """
    Consolida a validação. O que não foi executado aparece como
    `nao_executada` — nunca como "aprovado" por omissão.
    """
    base = {
        "conteudo": "nao_executada",
        "formatacao": "nao_executada",
        "campos_pendentes": len(pendentes),
        "campos_pendentes_verificados": verificaveis,
    }
    base.update(validacao or {})
    base["campos_pendentes"] = len(pendentes)
    base["campos_pendentes_verificados"] = verificaveis
    return base


def _atualizar_processo_json(processo: Processo, tx: Transacao, manifesto: dict) -> None:
    """Mantém a lista de documentos existentes/pendentes coerente (item 11)."""
    dados = processo.ler_processo()
    if not dados:
        return
    existentes = sorted(
        chave for chave, registro in manifesto["documentos"].items()
        if registro.get("arquivo_atual")
    )
    obrigatorios = list(dados.get("documentos_obrigatorios") or [])
    dados["documentos_existentes"] = existentes
    dados["documentos_pendentes"] = [d for d in obrigatorios if d not in existentes]
    dados["atualizado_em"] = agora()
    tx.gravar_json(processo.arquivo_processo, dados)


def _regerar_painel(processo: Processo, tx: Transacao, manifesto: dict) -> None:
    """Painel é derivado (item 12): regenerado, nunca editado como fonte."""
    from gerar_painel import montar_painel  # import tardio: evita ciclo

    tx.gravar_texto(
        processo.arquivo_painel,
        montar_painel(processo, manifesto=manifesto),
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Registra um documento gerado como versão vigente do processo."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--tipo", required=True)
    analisador.add_argument("--arquivo", required=True, help="arquivo gerado (temporário)")
    analisador.add_argument("--motivo", default="")
    analisador.add_argument("--minuta-origem")
    analisador.add_argument("--status", default="em_elaboracao")
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--estrito", action="store_true",
                            help="recusa o registro se houver campo pendente")
    analisador.add_argument("--forcar-nova-versao", action="store_true",
                            help="versiona mesmo sem alteração de conteúdo")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    try:
        resultado = registrar_saida_gerada(
            argumentos.processo,
            argumentos.tipo,
            argumentos.arquivo,
            minuta_origem=argumentos.minuta_origem,
            motivo=argumentos.motivo,
            status=argumentos.status,
            responsavel=argumentos.responsavel,
            base=argumentos.base,
            exigir_sem_pendencias=argumentos.estrito,
            forcar_nova_versao=argumentos.forcar_nova_versao,
        )
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    print(resultado.texto())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
