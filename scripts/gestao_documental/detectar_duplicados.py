#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detectar_duplicados.py — "Charles, informe quais arquivos estão duplicados".

Implementa o item 20 com uma distinção que o escopo faz questão de manter:

* **duplicado exato** — mesmo SHA-256. Aqui não há dúvida: é o mesmo arquivo em
  dois lugares. A importação nem copia de novo; aponta o que já existe.
* **duplicado provável** — nome parecido, tamanho parecido, texto parecido. NÃO
  é o mesmo arquivo, e pode ser a segunda proposta do mesmo fornecedor, com um
  preço diferente. Os dois ficam, marcados, e a decisão é humana (regra 34:
  "excluir duplicado provável sem validação" é proibido).

Este módulo não apaga nada, em hipótese nenhuma. Ele relata.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from hashes import semelhanca, sha256_arquivo  # noqa: E402
from manifesto import AREA_HISTORICO, AREA_TEMPORARIOS, Processo  # noqa: E402
from manifesto import preparar_console  # noqa: E402
from nomes_arquivos import remover_acentos  # noqa: E402

LIMITE_SEMELHANCA = 0.90
TOLERANCIA_TAMANHO = 0.10  # 10%: uma proposta com preço trocado muda pouco
LIMITE_INDICIO = 0.60  # abaixo disso, semelhança textual não diz nada
LIMITE_PARES = 400  # acima disso a comparação par a par fica cara demais

PASTAS_IGNORADAS = {AREA_TEMPORARIOS, ".locks", "__pycache__"}


@dataclass
class GrupoExato:
    hash_sha256: str
    arquivos: list[str] = field(default_factory=list)


@dataclass
class ParProvavel:
    arquivo_a: str
    arquivo_b: str
    motivos: list[str] = field(default_factory=list)
    semelhanca_texto: Optional[float] = None


@dataclass
class RelatorioDuplicados:
    total_arquivos: int = 0
    exatos: list[GrupoExato] = field(default_factory=list)
    provaveis: list[ParProvavel] = field(default_factory=list)
    nao_comparados: list[str] = field(default_factory=list)

    def texto(self) -> str:
        linhas = [f"Arquivos analisados: {self.total_arquivos}", ""]
        linhas.append(f"## Duplicados exatos (mesmo SHA-256): {len(self.exatos)}")
        for grupo in self.exatos:
            linhas.append(f"- `{grupo.hash_sha256[:16]}…`")
            linhas.extend(f"    - {arquivo}" for arquivo in grupo.arquivos)
        linhas.append("")
        linhas.append(f"## Duplicados prováveis (exigem validação humana): {len(self.provaveis)}")
        for par in self.provaveis:
            semelhanca_texto = (
                f"{par.semelhanca_texto:.0%}" if par.semelhanca_texto is not None
                else "texto não comparável"
            )
            linhas.append(f"- {par.arquivo_a}")
            linhas.append(f"  {par.arquivo_b}")
            linhas.append(f"    motivos: {'; '.join(par.motivos)} | semelhança: {semelhanca_texto}")
        if self.nao_comparados:
            linhas.append("")
            linhas.append("## Arquivos cujo conteúdo não pôde ser comparado")
            linhas.extend(f"- {arquivo}" for arquivo in self.nao_comparados)
        linhas.append("")
        linhas.append(
            "> Nada foi apagado nem movido. Duplicado provável não se elimina "
            "automaticamente (item 20 do escopo)."
        )
        return "\n".join(linhas)


def _radical_comparavel(nome: str) -> str:
    """Nome sem acento, sem extensão e sem os sufixos que marcam cópia."""
    radical = remover_acentos(Path(nome).stem).upper()
    radical = re.sub(
        r"(?:^|[_\s\-])(?:COPIA|COPY|FINAL|NOVO|NOVA|CORRIGIDO|CORRIGIDA|"
        r"ATUALIZADO|ATUALIZADA|REV|REVISAO|V)\s*\d*(?=$|[_\s\-])",
        " ", radical,
    )
    radical = re.sub(r"\(\s*\d+\s*\)", " ", radical)
    radical = re.sub(r"[_\-\s]+\d{1,2}$", "", radical)
    return re.sub(r"[^A-Z0-9]+", "", radical)


def _arquivos_do_processo(raiz: Path, incluir_historico: bool = False) -> Iterable[Path]:
    """
    Arquivos que fazem sentido comparar entre si.

    `90_HISTORICO/` fica de fora por padrão: ali a repetição é a finalidade da
    pasta. Apontar que `TR.docx` se parece com `TR_v002_...docx` é redescrever o
    versionamento como se fosse desordem, e afoga os achados reais em ruído. Com
    `--incluir-historico` a varredura alcança tudo, para auditoria.
    """
    ignoradas = set(PASTAS_IGNORADAS)
    if not incluir_historico:
        ignoradas.add(AREA_HISTORICO)
    for caminho in sorted(raiz.rglob("*")):
        if not caminho.is_file():
            continue
        if any(parte in ignoradas for parte in caminho.parts):
            continue
        yield caminho


def analisar(
    raiz: Path | str,
    *,
    limite_semelhanca: float = LIMITE_SEMELHANCA,
    comparar_texto: bool = True,
    incluir_historico: bool = False,
) -> RelatorioDuplicados:
    raiz = Path(raiz)
    relatorio = RelatorioDuplicados()
    por_hash: dict[str, list[Path]] = defaultdict(list)
    arquivos: list[Path] = []

    for caminho in _arquivos_do_processo(raiz, incluir_historico):
        arquivos.append(caminho)
        por_hash[sha256_arquivo(caminho)].append(caminho)
    relatorio.total_arquivos = len(arquivos)

    exatos: set[Path] = set()
    for digest, lista in sorted(por_hash.items()):
        if len(lista) > 1:
            relatorio.exatos.append(GrupoExato(
                hash_sha256=digest,
                arquivos=[str(c.relative_to(raiz)) for c in lista],
            ))
            exatos.update(lista)

    # Prováveis: só entre arquivos que NÃO são duplicata exata um do outro.
    # Nome parecido é UM dos critérios do item 20, não o único — duas propostas
    # do mesmo fornecedor podem ter nomes distintos e conteúdo quase igual. Por
    # isso todo par de mesma extensão e tamanho próximo é comparado.
    candidatos = [c for c in arquivos if c not in exatos]
    if len(candidatos) > LIMITE_PARES:
        relatorio.nao_comparados.append(
            f"{len(candidatos)} arquivos: comparação par a par não executada "
            f"(limite de {LIMITE_PARES}); rode por subpasta"
        )
        return relatorio

    for indice, primeiro in enumerate(candidatos):
        for segundo in candidatos[indice + 1:]:
            if primeiro.suffix.lower() != segundo.suffix.lower():
                continue
            motivos: list[str] = []
            radical_a = _radical_comparavel(primeiro.name)
            radical_b = _radical_comparavel(segundo.name)
            if radical_a and radical_a == radical_b:
                motivos.append(f"radical de nome idêntico ('{radical_a}')")

            tamanho_a, tamanho_b = primeiro.stat().st_size, segundo.stat().st_size
            maior = max(tamanho_a, tamanho_b) or 1
            proximo_em_tamanho = abs(tamanho_a - tamanho_b) / maior <= TOLERANCIA_TAMANHO
            if proximo_em_tamanho:
                motivos.append("tamanho equivalente")
            if not motivos:
                continue

            nome_bate = any("radical" in m for m in motivos)
            proximidade = semelhanca(primeiro, segundo) if comparar_texto else None
            if proximidade is None:
                relatorio.nao_comparados.append(
                    f"{primeiro.relative_to(raiz)} × {segundo.relative_to(raiz)}"
                )
                if not nome_bate:
                    # Sem leitura do texto, "mesmo tamanho" sozinho não é indício
                    # de nada: dois PDFs de 200 KB não têm relação por isso.
                    continue
            elif proximidade >= limite_semelhanca:
                motivos.append(f"texto {proximidade:.0%} semelhante")
            elif proximidade >= LIMITE_INDICIO:
                # Duas propostas do mesmo fornecedor com preço diferente caem
                # aqui: parecidas demais para ignorar, diferentes demais para
                # tratar como a mesma coisa.
                motivos.append(f"texto {proximidade:.0%} semelhante — possível versão")
            elif not nome_bate:
                continue  # só o tamanho bate, e o texto discorda: não é indício

            relatorio.provaveis.append(ParProvavel(
                arquivo_a=str(primeiro.relative_to(raiz)),
                arquivo_b=str(segundo.relative_to(raiz)),
                motivos=motivos,
                semelhanca_texto=proximidade,
            ))
    return relatorio


def duplicado_exato_no_processo(
    processo: Processo, caminho: Path | str
) -> Optional[str]:
    """
    Já existe arquivo com este hash no processo? Devolve o caminho relativo.

    Usado pela importação antes de copiar qualquer coisa (item 20, passo 1).
    """
    digest = sha256_arquivo(caminho)
    for existente in _arquivos_do_processo(processo.raiz):
        if Path(existente).resolve() == Path(caminho).resolve():
            continue
        if sha256_arquivo(existente) == digest:
            return processo.relativo(existente)
    return None


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Relata arquivos duplicados num processo. Não apaga nada."
    )
    analisador.add_argument("--processo", help="identificador ou caminho do processo")
    analisador.add_argument("--pasta", help="pasta avulsa a analisar")
    analisador.add_argument("--limite", type=float, default=LIMITE_SEMELHANCA)
    analisador.add_argument("--sem-texto", action="store_true",
                            help="não compara texto (mais rápido)")
    analisador.add_argument("--incluir-historico", action="store_true",
                            help="compara também 90_HISTORICO/ (versões antigas)")
    analisador.add_argument("--json", action="store_true")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    if not argumentos.processo and not argumentos.pasta:
        print("ERRO: informe --processo ou --pasta.", file=sys.stderr)
        return 2
    try:
        raiz = (
            Path(argumentos.pasta) if argumentos.pasta
            else Processo.abrir(argumentos.processo, argumentos.base).raiz
        )
        relatorio = analisar(
            raiz, limite_semelhanca=argumentos.limite,
            comparar_texto=not argumentos.sem_texto,
            incluir_historico=argumentos.incluir_historico,
        )
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    if argumentos.json:
        from dataclasses import asdict

        print(json.dumps(asdict(relatorio), ensure_ascii=False, indent=2))
    else:
        print(relatorio.texto())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
