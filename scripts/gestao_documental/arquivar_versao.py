#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arquivar_versao.py — tira a versão anterior da área corrente sem perdê-la.

É aqui que se concilia o item 1 ("um só arquivo atual visível") com o item 2
("não apagar o histórico"). Arquivar não é excluir: o arquivo sai da pasta de
trabalho, ganha nome com versão e carimbo de tempo (item 8) e passa a constar
do histórico do manifesto, com hash e motivo.

A função principal roda DENTRO da transação de quem chama — arquivar e
substituir precisam ter o mesmo destino, ou nenhum: manifesto e arquivos jamais
divergem (regra 34).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from hashes import sha256_arquivo  # noqa: E402
from manifesto import (  # noqa: E402
    OperacaoBloqueada,
    Processo,
    STATUS_IMUTAVEIS,
    agora,
    evento,
    linha_log,
    preparar_console,
)
from nomes_arquivos import existe, nome_historico, obter_tipo  # noqa: E402
from transacoes import Transacao  # noqa: E402


def arquivar_na_transacao(
    processo: Processo,
    tx: Transacao,
    tipo: str,
    registro: dict[str, Any],
    motivo: str,
    *,
    responsavel: str = "Charles",
    permitir_imutavel: bool = False,
) -> Optional[dict[str, Any]]:
    """
    Move a representação editável atual para `90_HISTORICO/` e registra.

    Devolve a entrada acrescentada ao histórico, ou None quando não havia
    arquivo atual em disco (processo recém-criado, ou representação já movida).

    `permitir_imutavel` existe para um caso legítimo e apenas um: a RETIFICAÇÃO
    de documento publicado, que preserva o publicado no histórico em vez de
    sobrescrevê-lo. Fora disso, assinado e publicado não se arquivam para dar
    lugar a outro arquivo (item 6).
    """
    status_atual = registro.get("status", "em_elaboracao")
    if status_atual in STATUS_IMUTAVEIS and not permitir_imutavel:
        raise OperacaoBloqueada(
            f"O {tipo} está com status '{status_atual}', que é imutável. "
            f"Documento assinado ou publicado não é substituído: gere uma "
            f"retificação (promover_documento.py --retificar) e mantenha a "
            f"relação entre as versões."
        )

    relativo_atual = registro.get("arquivo_atual")
    if not relativo_atual:
        return None
    origem = processo.absoluto(relativo_atual)
    if not existe(origem):
        return None

    versao = int(registro.get("versao_atual") or 1)
    destino = processo.garantir(
        "90_HISTORICO", obter_tipo(tipo).pasta_historico
    ) / nome_historico(tipo, versao, datetime.now(), motivo, origem.suffix)

    hash_arquivado = sha256_arquivo(origem)
    tx.mover(origem, destino)

    entrada = {
        "versao": versao,
        "arquivo": processo.relativo(destino),
        "hash_sha256": hash_arquivado,
        "status_ao_arquivar": status_atual,
        "arquivado_em": agora(),
        "motivo": motivo or "substituição por nova versão",
        "responsavel": responsavel,
    }
    registro.setdefault("historico", []).append(entrada)
    tx.acrescentar_linha(
        processo.arquivo_log,
        linha_log(evento(
            "documento_arquivado",
            documento=tipo,
            versao=versao,
            arquivo=entrada["arquivo"],
            hash_sha256=hash_arquivado,
            responsavel=responsavel,
            motivo=entrada["motivo"],
        )),
    )
    return entrada


def arquivar(
    identificador: str,
    tipo: str,
    motivo: str,
    *,
    responsavel: str = "Charles",
    base: Optional[Path | str] = None,
) -> Optional[dict[str, Any]]:
    """
    Arquiva a versão atual sem colocar outra no lugar (encerramento, cancelamento).

    Depois disso o tipo fica sem arquivo corrente e com status `arquivado` — o
    conteúdo permanece inteiro em `90_HISTORICO/`.
    """
    processo = Processo.abrir(identificador, base)
    manifesto = processo.ler_documentos()
    chave = obter_tipo(tipo).tipo
    registro = manifesto["documentos"].get(chave)
    if not registro:
        raise OperacaoBloqueada(f"Não há {chave} registrado neste processo.")

    with Transacao(processo.temporarios, f"arquivar {chave}") as tx:
        entrada = arquivar_na_transacao(
            processo, tx, chave, registro, motivo, responsavel=responsavel
        )
        registro["status"] = "arquivado"
        registro["arquivo_atual"] = None
        registro["representacoes"]["docx"] = None
        registro["atualizado_em"] = agora()
        registro["motivo_ultima_alteracao"] = motivo
        manifesto["atualizado_em"] = agora()
        tx.gravar_json(processo.arquivo_documentos, manifesto)
    return entrada


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Arquiva a versão atual de um documento, preservando-a no histórico."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--tipo", required=True)
    analisador.add_argument("--motivo", required=True)
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    try:
        entrada = arquivar(
            argumentos.processo,
            argumentos.tipo,
            argumentos.motivo,
            responsavel=argumentos.responsavel,
            base=argumentos.base,
        )
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    if entrada is None:
        print("Não havia arquivo corrente para arquivar.")
    else:
        print(f"Versão {entrada['versao']} arquivada em {entrada['arquivo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
