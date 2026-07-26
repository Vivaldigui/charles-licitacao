#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
restaurar_versao.py — "Charles, restaure o conteúdo da versão 2 do TR" (item 22).

Restaurar NÃO é voltar no tempo. O contador de versão nunca anda para trás:
está tudo no processo administrativo, e um documento que "volta" à versão 2
apagaria a existência das versões 3, 4 e 5, que podem ter circulado.

O que acontece de fato:

1. a versão atual é arquivada (não some);
2. o conteúdo da versão antiga é COPIADO do histórico;
3. essa cópia entra como versão NOVA — 5 restaurada vira 6;
4. o manifesto e o log registram que a origem foi restauração da versão 2.

O arquivo antigo permanece no histórico onde sempre esteve: a cópia é cópia.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from arquivar_versao import arquivar_na_transacao  # noqa: E402
from hashes import hash_conteudo, sha256_arquivo  # noqa: E402
from locks import LockDocumento  # noqa: E402
from manifesto import (  # noqa: E402
    OperacaoBloqueada,
    Processo,
    STATUS_IMUTAVEIS,
    agora,
    evento,
    linha_log,
    preparar_console,
)
from nomes_arquivos import existe, nome_canonico, obter_tipo  # noqa: E402
from transacoes import Transacao  # noqa: E402


def historico_do_documento(processo: Processo, tipo: str) -> list[dict[str, Any]]:
    registro = processo.documento(tipo)
    return list((registro or {}).get("historico") or [])


def restaurar(
    identificador: str,
    tipo: str,
    versao: int,
    *,
    motivo: str = "",
    responsavel: str = "Charles",
    status: str = "em_revisao",
    base: Optional[Path | str] = None,
) -> dict[str, Any]:
    processo = Processo.abrir(identificador, base)
    chave = obter_tipo(tipo).tipo
    versao = int(versao)

    with LockDocumento(processo.raiz, processo.identificador, chave):
        manifesto = processo.ler_documentos()
        registro = manifesto["documentos"].get(chave)
        if not registro:
            raise OperacaoBloqueada(f"Não há {chave} registrado neste processo.")
        if registro.get("status") in STATUS_IMUTAVEIS:
            raise OperacaoBloqueada(
                f"O {chave} está '{registro.get('status')}' — imutável. Restaurar por "
                f"cima seria sobrescrever documento assinado ou publicado. Use "
                f"promover_documento.py --retificar."
            )

        entradas = [e for e in (registro.get("historico") or []) if int(e.get("versao", -1)) == versao]
        if not entradas:
            disponiveis = sorted({int(e.get("versao", 0)) for e in (registro.get("historico") or [])})
            raise OperacaoBloqueada(
                f"Versão {versao} do {chave} não está no histórico. "
                f"Versões disponíveis: {disponiveis or 'nenhuma'}."
            )
        entrada = entradas[-1]
        origem = processo.absoluto(entrada["arquivo"])
        if not existe(origem):
            raise OperacaoBloqueada(
                f"O manifesto aponta a versão {versao} em {entrada['arquivo']}, mas o "
                f"arquivo não está lá. Não restauro o que não posso ler — apure a "
                f"divergência com validar_processo.py."
            )

        hash_origem = sha256_arquivo(origem)
        if hash_origem != entrada.get("hash_sha256"):
            raise OperacaoBloqueada(
                f"O arquivo da versão {versao} não confere com o hash registrado no "
                f"manifesto. O conteúdo foi alterado fora do Charles; restauração "
                f"recusada até conferência humana."
            )

        nova_versao = int(registro.get("versao_atual") or 0) + 1
        razao = motivo or f"restauração do conteúdo da versão {versao}"

        with Transacao(processo.temporarios, f"restaurar {chave} v{versao}") as tx:
            arquivada = arquivar_na_transacao(
                processo, tx, chave, registro, razao, responsavel=responsavel
            )
            if arquivada is not None:
                arquivada["substituido_por_versao"] = nova_versao

            destino = processo.area_corrente(chave, status) / nome_canonico(
                chave, origem.suffix
            )
            destino.parent.mkdir(parents=True, exist_ok=True)
            tx.copiar(origem, destino)

            registro.update({
                "versao_atual": nova_versao,
                "status": status,
                "arquivo_atual": processo.relativo(destino),
                "hash_sha256": sha256_arquivo(destino),
                "hash_conteudo": hash_conteudo(destino),
                "atualizado_em": agora(),
                "substitui_versao": nova_versao - 1,
                "origem_da_versao": {
                    "tipo": "restauracao",
                    "versao_restaurada": versao,
                    "arquivo_de_origem": entrada["arquivo"],
                },
                "motivo_ultima_alteracao": razao,
            })
            registro["representacoes"] = {
                "docx": registro["arquivo_atual"] if destino.suffix.lower() in (".docx", ".docm") else None,
                "pdf": None,
                "assinado": None,
            }
            manifesto["atualizado_em"] = agora()
            tx.gravar_json(processo.arquivo_documentos, manifesto)
            tx.acrescentar_linha(processo.arquivo_log, linha_log(evento(
                "restauracao_de_versao",
                documento=chave,
                versao=nova_versao,
                arquivo=registro["arquivo_atual"],
                hash_sha256=registro["hash_sha256"],
                responsavel=responsavel,
                motivo=razao,
                versao_restaurada=versao,
            )))
            from gerar_painel import montar_painel

            tx.gravar_texto(processo.arquivo_painel, montar_painel(processo, manifesto=manifesto))

    return {
        "documento": chave,
        "versao_restaurada": versao,
        "nova_versao": nova_versao,
        "arquivo": registro["arquivo_atual"],
        "versao_anterior_arquivada": (arquivada or {}).get("arquivo"),
    }


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Restaura o conteúdo de uma versão antiga como versão nova."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--tipo", required=True)
    analisador.add_argument("--versao", type=int, required=True)
    analisador.add_argument("--motivo", default="")
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--status", default="em_revisao")
    analisador.add_argument("--base")
    analisador.add_argument("--listar", action="store_true",
                            help="apenas lista o histórico do documento")
    argumentos = analisador.parse_args(argv)

    try:
        if argumentos.listar:
            processo = Processo.abrir(argumentos.processo, argumentos.base)
            for entrada in historico_do_documento(processo, argumentos.tipo):
                print(
                    f"v{entrada.get('versao'):>3} | {entrada.get('arquivado_em')} | "
                    f"{entrada.get('status_ao_arquivar')} | {entrada.get('arquivo')} | "
                    f"{entrada.get('motivo')}"
                )
            return 0
        relatorio = restaurar(
            argumentos.processo, argumentos.tipo, argumentos.versao,
            motivo=argumentos.motivo, responsavel=argumentos.responsavel,
            status=argumentos.status, base=argumentos.base,
        )
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    for chave, valor in relatorio.items():
        print(f"{chave}: {valor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
