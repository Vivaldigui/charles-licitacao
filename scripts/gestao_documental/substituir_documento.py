#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
substituir_documento.py — troca a versão vigente de um documento já existente.

    python scripts/gestao_documental/substituir_documento.py \
      --processo PA_031_2026 --tipo TR --arquivo saida/TR_revisado.docx \
      --motivo "Ajuste do prazo de entrega"

É `registrar_documento` com duas exigências a mais, próprias de quem já tem
documento no lugar:

* **motivo obrigatório** — substituir sem dizer por quê é como salvar
  "TR_final_2": ninguém depois sabe o que mudou nem por decisão de quem;
* **tem de haver o que substituir** — se o tipo ainda não existe no processo, o
  script recusa e manda usar o registro de primeira geração, para que ninguém
  ache que substituiu algo que nunca existiu.

O resto do comportamento é o do fluxo comum: assinado e publicado continuam
imutáveis, conteúdo idêntico não vira versão nova, e a versão anterior vai
inteira para `90_HISTORICO/`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from manifesto import OperacaoBloqueada, Processo  # noqa: E402
from manifesto import preparar_console  # noqa: E402
from nomes_arquivos import obter_tipo  # noqa: E402
from registrar_documento import ResultadoRegistro, registrar_saida_gerada  # noqa: E402


def substituir(
    identificador: str,
    tipo: str,
    arquivo: Path | str,
    motivo: str,
    *,
    status: Optional[str] = None,
    responsavel: str = "Charles",
    minuta_origem: Optional[str] = None,
    base: Optional[Path | str] = None,
    exigir_sem_pendencias: bool = False,
    forcar_nova_versao: bool = False,
) -> ResultadoRegistro:
    if not str(motivo).strip():
        raise OperacaoBloqueada(
            "Substituição exige --motivo: é o que dá sentido ao histórico de versões."
        )
    processo = Processo.abrir(identificador, base)
    chave = obter_tipo(tipo).tipo
    registro = processo.documento(chave)
    if not registro or not registro.get("arquivo_atual"):
        raise OperacaoBloqueada(
            f"Não há {chave} vigente neste processo para substituir. Para a primeira "
            f"geração, use registrar_documento.py."
        )
    return registrar_saida_gerada(
        processo,
        chave,
        arquivo,
        minuta_origem=minuta_origem,
        motivo=motivo,
        status=status or registro.get("status") or "em_elaboracao",
        responsavel=responsavel,
        exigir_sem_pendencias=exigir_sem_pendencias,
        forcar_nova_versao=forcar_nova_versao,
    )


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Substitui a versão vigente de um documento do processo."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--tipo", required=True)
    analisador.add_argument("--arquivo", required=True)
    analisador.add_argument("--motivo", required=True)
    analisador.add_argument("--status")
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--minuta-origem")
    analisador.add_argument("--estrito", action="store_true")
    analisador.add_argument("--forcar-nova-versao", action="store_true")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    try:
        resultado = substituir(
            argumentos.processo, argumentos.tipo, argumentos.arquivo, argumentos.motivo,
            status=argumentos.status, responsavel=argumentos.responsavel,
            minuta_origem=argumentos.minuta_origem, base=argumentos.base,
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
