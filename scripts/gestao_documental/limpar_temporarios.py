#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
limpar_temporarios.py — "Charles, limpe os arquivos temporários".

Encerra o passo 14 do fluxo de geração e recolhe o que ficou de gerações
interrompidas: sessões em `99_TEMPORARIOS/`, arquivos `.part-*` de movimentos
que não completaram e locks vencidos.

O que este script apaga é estreito e definido: **só** o que está dentro de
`99_TEMPORARIOS/` e os `.locks/` expirados. Nada em `01_EM_ELABORACAO/`,
`02_DOCUMENTOS_OFICIAIS/`, `03_DOCUMENTOS_EXTERNOS/`, `90_HISTORICO/` ou
`98_QUARENTENA/` é tocado — nem quando parece lixo. Arquivo suspeito fora da
área temporária é assunto do relatório de organização, não da vassoura.

Duas cautelas:

* **sessão recente não é lixo** — pode ser de uma geração em curso agora. Por
  isso a idade mínima (`--idade-horas`, padrão 12) e o respeito ao lock ativo.
* **diário de transação com rollback incompleto não é removido** — ele é a
  prova do que ficou pela metade, e sai daqui listado, não deletado.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from locks import PASTA_LOCKS, LockDocumento, locks_ativos  # noqa: E402
from manifesto import Processo, evento, linha_log  # noqa: E402
from manifesto import preparar_console  # noqa: E402

IDADE_PADRAO_HORAS = 12


@dataclass
class RelatorioLimpeza:
    sessoes_removidas: list[str] = field(default_factory=list)
    sessoes_preservadas: list[str] = field(default_factory=list)
    parciais_removidos: list[str] = field(default_factory=list)
    locks_removidos: list[str] = field(default_factory=list)
    locks_preservados: list[str] = field(default_factory=list)
    diarios_com_pendencia: list[str] = field(default_factory=list)
    bytes_liberados: int = 0
    simulacao: bool = False

    def texto(self) -> str:
        cabecalho = "SIMULAÇÃO — nada foi removido" if self.simulacao else "Limpeza executada"
        linhas = [
            f"# {cabecalho}",
            "",
            f"- Sessões temporárias removidas: {len(self.sessoes_removidas)}",
            f"- Sessões preservadas (recentes ou em uso): {len(self.sessoes_preservadas)}",
            f"- Arquivos parciais removidos: {len(self.parciais_removidos)}",
            f"- Locks vencidos removidos: {len(self.locks_removidos)}",
            f"- Locks ativos preservados: {len(self.locks_preservados)}",
            f"- Espaço liberado: {self.bytes_liberados / 1024:.1f} KB",
        ]
        if self.diarios_com_pendencia:
            linhas += [
                "",
                "## Transações que não concluíram — PRESERVADAS para conferência",
                "",
            ]
            linhas += [f"- {item}" for item in self.diarios_com_pendencia]
        if self.sessoes_preservadas:
            linhas += ["", "## Sessões preservadas", ""]
            linhas += [f"- {item}" for item in self.sessoes_preservadas]
        linhas += [
            "",
            "> Apenas `99_TEMPORARIOS/` e locks vencidos são afetados. Documentos, "
            "histórico e quarentena permanecem intactos.",
        ]
        return "\n".join(linhas)


def _tamanho(caminho: Path) -> int:
    if caminho.is_file():
        return caminho.stat().st_size
    return sum(c.stat().st_size for c in caminho.rglob("*") if c.is_file())


def _diario_pendente(sessao: Path) -> Optional[str]:
    """Sessão com transação não confirmada? Devolve a situação encontrada."""
    for diario in sessao.glob(".transacao-*.json"):
        try:
            dados = json.loads(diario.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return "diário de transação ilegível"
        if dados.get("situacao") not in ("confirmada", "rollback"):
            return f"transação '{dados.get('descricao')}' em situação '{dados.get('situacao')}'"
    return None


def limpar(
    identificador: str,
    *,
    idade_horas: float = IDADE_PADRAO_HORAS,
    simulacao: bool = False,
    responsavel: str = "Charles",
    base: Optional[Path | str] = None,
) -> RelatorioLimpeza:
    processo = Processo.abrir(identificador, base)
    relatorio = RelatorioLimpeza(simulacao=simulacao)
    limite = time.time() - idade_horas * 3600
    documentos_travados = {d.documento for d in locks_ativos(processo.raiz)}

    # -- sessões temporárias ------------------------------------------------ #
    if processo.temporarios.is_dir():
        for item in sorted(processo.temporarios.iterdir()):
            relativo = processo.relativo(item)
            if item.name == "backup":
                continue
            if item.stat().st_mtime > limite:
                relatorio.sessoes_preservadas.append(f"{relativo} (recente)")
                continue
            if any(f"_{doc}" in item.name for doc in documentos_travados):
                relatorio.sessoes_preservadas.append(f"{relativo} (documento travado)")
                continue
            pendencia = _diario_pendente(item) if item.is_dir() else None
            if pendencia:
                relatorio.diarios_com_pendencia.append(f"{relativo}: {pendencia}")
                relatorio.sessoes_preservadas.append(f"{relativo} (transação pendente)")
                continue

            relatorio.bytes_liberados += _tamanho(item)
            relatorio.sessoes_removidas.append(relativo)
            if not simulacao:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)

        # Diários soltos na raiz de 99_TEMPORARIOS.
        for diario in sorted(processo.temporarios.glob(".transacao-*.json")):
            try:
                dados = json.loads(diario.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if dados.get("situacao") in ("confirmada", "rollback") and \
                    diario.stat().st_mtime <= limite:
                relatorio.bytes_liberados += _tamanho(diario)
                relatorio.sessoes_removidas.append(processo.relativo(diario))
                if not simulacao:
                    diario.unlink(missing_ok=True)
            elif dados.get("situacao") not in ("confirmada", "rollback"):
                relatorio.diarios_com_pendencia.append(
                    f"{processo.relativo(diario)}: situação '{dados.get('situacao')}'"
                )

    # -- arquivos parciais de movimentos interrompidos --------------------- #
    for parcial in sorted(processo.raiz.rglob("*.part-*")):
        if not parcial.is_file() or parcial.stat().st_mtime > limite:
            continue
        relatorio.bytes_liberados += parcial.stat().st_size
        relatorio.parciais_removidos.append(processo.relativo(parcial))
        if not simulacao:
            parcial.unlink(missing_ok=True)

    # -- locks vencidos ----------------------------------------------------- #
    pasta_locks = processo.raiz / PASTA_LOCKS
    if pasta_locks.is_dir():
        for arquivo in sorted(pasta_locks.glob("*.lock")):
            lock = LockDocumento(processo.raiz, processo.identificador, arquivo.stem)
            dados = lock.ler()
            if dados is None or dados.expirado():
                relatorio.locks_removidos.append(processo.relativo(arquivo))
                if not simulacao:
                    arquivo.unlink(missing_ok=True)
            else:
                relatorio.locks_preservados.append(
                    f"{processo.relativo(arquivo)} (sessão {dados.sessao}, "
                    f"expira {dados.expira_em})"
                )

    if not simulacao and (relatorio.sessoes_removidas or relatorio.parciais_removidos
                          or relatorio.locks_removidos):
        with open(processo.arquivo_log, "a", encoding="utf-8", newline="\n") as log:
            log.write(linha_log(evento(
                "temporarios_limpos",
                responsavel=responsavel,
                motivo=f"{len(relatorio.sessoes_removidas)} sessão(ões), "
                       f"{len(relatorio.parciais_removidos)} parcial(is), "
                       f"{len(relatorio.locks_removidos)} lock(s) vencido(s)",
            )) + "\n")
    return relatorio


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Remove sessões temporárias e locks vencidos de um processo."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--idade-horas", type=float, default=IDADE_PADRAO_HORAS)
    analisador.add_argument("--simular", action="store_true",
                            help="mostra o que seria removido, sem remover")
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    try:
        relatorio = limpar(
            argumentos.processo, idade_horas=argumentos.idade_horas,
            simulacao=argumentos.simular, responsavel=argumentos.responsavel,
            base=argumentos.base,
        )
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    print(relatorio.texto())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
