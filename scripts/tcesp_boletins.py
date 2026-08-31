#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coleta e indexa julgados sobre contratação direta nos boletins do TCE-SP.

O pipeline usa apenas a página oficial de publicações, os PDFs oficiais e pypdf.
Ele é deliberadamente conservador: seleciona blocos completos de julgados que
contenham expressões inequívocas de contratação direta/dispensa e registra
página, URL e SHA-256. A ficha é fonte de triagem; o boletim não substitui o
inteiro teor da decisão.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - mensagem operacional
    raise SystemExit(
        "Dependência ausente: instale requirements-auditor.txt (pypdf)."
    ) from exc


RAIZ = Path(__file__).resolve().parents[1]
LISTAGEM_URL = "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes"
ORIGINAIS_DIR = RAIZ / "TCE-SP_BOLETINS"
BASE_DIR = RAIZ / "03_jurisprudencia" / "tce_sp" / "contratacao_direta"
FICHAS_DIR = BASE_DIR / "fichas"
TEXTOS_DIR = BASE_DIR / "texto_extraido"
INDICES_DIR = BASE_DIR / "indices"
CONSOLIDACOES_DIR = BASE_DIR / "consolidacoes"
ATUALIZADO_EM = date.today().isoformat()
USER_AGENT = "Charles-TCESP-Boletins/1.0 (pesquisa documental institucional)"

NAO_IDENTIFICADO = "Não identificado no documento"

PADRAO_PUBLICACAO = re.compile(
    r'<div class="publicacao"><a href="([^"]+)"[\s\S]*?'
    r'<div class="titulo"><p>([^<]+)</p>',
    re.IGNORECASE,
)
PADRAO_PDF = re.compile(r'href="([^"]+\.pdf(?:\?[^\"]*)?)"', re.IGNORECASE)
PADRAO_DATA_PUBLICACAO = re.compile(
    r'Data de Publica(?:ç|&ccedil;)ão:</div>[\s\S]{0,500}?field--item[^>]*>(\d{2}/\d{2}/\d{4})<',
    re.IGNORECASE,
)
PADRAO_DATA_PUBLICACAO_FLEX = re.compile(
    r'Data de Publica(?:ç|&ccedil;)ão[\s\S]{0,800}?(\d{2}/\d{2}/\d{4})',
    re.IGNORECASE,
)
PADRAO_PROCESSO = re.compile(
    r"(?:TC-)?\d{5,6}\.989\.\d{2}(?:-\d)?|(?:TC-)?\d{3,6}/\d{3}/\d{2}",
    re.IGNORECASE,
)
PADRAO_SESSAO = re.compile(r"\(\s*Sess[aã]o[^)]*\)", re.IGNORECASE)

EXPRESSOES_FORTES = {
    "contratacao direta": re.compile(r"\bcontratac(?:ao|oes) direta(?:s)?\b"),
    "dispensa de licitacao": re.compile(r"\bdispensas? de licitacao\b"),
    "dispensa licitatoria": re.compile(r"\bdispensa licitatoria\b"),
    "licitacao dispensavel": re.compile(r"\blicitacao dispensavel\b"),
    "aquisicao direta emergencial": re.compile(
        r"\baquisicao direta\b[\s\S]{0,250}\b(?:emergenc|lei federal n?\.? ?13\.979)"
    ),
    "sem previa licitacao": re.compile(r"\b(?:contratac(?:ao|oes)|avencas?)\b[\s\S]{0,80}\bsem previa licitacao\b"),
}

TEMAS = {
    "emergência": ("emergenc", "calamidade", "urgencia"),
    "planejamento": ("planejamento", "desidia", "tempo suficiente"),
    "pesquisa de preços": ("pesquisa de precos", "cotacao de precos", "economicidade"),
    "justificativa do preço": ("justificativa do preco", "justificativa de precos"),
    "escolha do fornecedor": ("escolha do fornecedor", "escolha da empresa", "razao da escolha"),
    "execução contratual": ("execucao contratual", "acompanhamento da execucao", "recebimento definitivo"),
    "fiscalização": ("fiscalizacao", "gestor do contrato", "fiscal do contrato"),
    "publicidade": ("publicacao do contrato", "transparencia", "publicidade"),
    "subcontratação": ("subcontrat", "terceirizado integralmente"),
    "qualificação técnica": ("capacidade tecnica", "qualificacao tecnica"),
    "pandemia": ("covid", "coronavirus", "13.979"),
    "saúde": ("servicos medicos", "saude", "ventiladores pulmonares"),
    "alimentação escolar": ("alimentacao escolar", "generos alimenticios", "agricultura familiar"),
    "transporte escolar": ("transporte escolar", "transporte de alunos"),
    "resíduos e limpeza urbana": ("residuos solidos", "limpeza urbana"),
    "terceiro setor": ("organizacoes sociais", "contrato de gestao", "terceiro setor"),
    "responsabilização": ("multa", "responsabil", "ministerio publico"),
    "fracionamento": ("fracionamento", "parcelamento indevido"),
    "dispensa por valor": ("pequeno valor", "baixo valor", "dispensa por valor"),
}


@dataclass(frozen=True)
class Publicacao:
    edicao: int
    titulo: str
    pagina_url: str
    pdf_url: str
    data_publicacao: str


@dataclass
class Julgado:
    id: str
    edicao: int
    titulo_boletim: str
    pagina_publicacao_url: str
    pdf_url: str
    data_publicacao: str
    arquivo_original: str
    sha256: str
    tamanho_bytes: int
    paginas: list[int]
    processos: list[str]
    data_sessao: str
    relator: str
    orgao_julgador: str
    ementa: str
    registro_boletim: str
    termos_selecao: list[str]
    temas: list[str]
    regime_legal: str
    ficha_path: str


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acentos = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    normalizado = re.sub(r"\s+", " ", sem_acentos).strip().lower()
    # Alguns PDFs recentes separam o sufixo gráfico de palavras como
    # "LICITA ÇÃO". Repara somente vocábulos jurídicos conhecidos, sem fazer
    # junção genérica que poderia alterar o conteúdo.
    normalizado = re.sub(
        r"\b(licita|contrata|justifica|aquis|execu|fiscaliza) (cao|coes)\b",
        r"\1\2",
        normalizado,
    )
    normalizado = re.sub(r"\blicita (toria|torias)\b", r"licita\1", normalizado)
    return normalizado


def limpar_espacos(texto: str) -> str:
    linhas = [re.sub(r"[ \t]+", " ", linha).strip() for linha in texto.splitlines()]
    saida: list[str] = []
    for linha in linhas:
        if not linha:
            if saida and saida[-1] != "":
                saida.append("")
            continue
        saida.append(linha)
    return "\n".join(saida).strip()


def texto_corrido(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def sha256_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as stream:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest().upper()


def requisitar(url: str) -> bytes:
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            return resposta.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha ao acessar {url}: {exc}") from exc


def url_absoluta(url: str, base: str) -> str:
    return urllib.parse.urljoin(base, html.unescape(url))


def descobrir_publicacoes() -> list[Publicacao]:
    registros: dict[int, tuple[str, str]] = {}
    for pagina in range(0, 20):
        url = f"{LISTAGEM_URL}?page={pagina}"
        conteudo = requisitar(url).decode("utf-8", errors="replace")
        encontrados = PADRAO_PUBLICACAO.findall(conteudo)
        if not encontrados:
            break
        antes = len(registros)
        for href, titulo_html in encontrados:
            titulo = html.unescape(re.sub(r"<[^>]+>", "", titulo_html)).strip()
            m_edicao = re.search(r"Edi(?:ç|c)ão N\.º\s*(\d+)", titulo, re.IGNORECASE)
            if not m_edicao:
                continue
            edicao = int(m_edicao.group(1))
            registros[edicao] = (titulo, url_absoluta(href, LISTAGEM_URL))
        if len(registros) == antes:
            break

    publicacoes: list[Publicacao] = []
    for edicao, (titulo, pagina_url) in sorted(registros.items()):
        detalhe = requisitar(pagina_url).decode("utf-8", errors="replace")
        pdfs = PADRAO_PDF.findall(detalhe)
        if not pdfs:
            raise RuntimeError(f"PDF não localizado para a edição {edicao}: {pagina_url}")
        pdf_url = url_absoluta(pdfs[0], pagina_url)
        m_data = PADRAO_DATA_PUBLICACAO.search(detalhe) or PADRAO_DATA_PUBLICACAO_FLEX.search(detalhe)
        data_publicacao = converter_data(m_data.group(1)) if m_data else NAO_IDENTIFICADO
        publicacoes.append(Publicacao(edicao, titulo, pagina_url, pdf_url, data_publicacao))
    return publicacoes


def converter_data(valor: str) -> str:
    dia, mes, ano = valor.split("/")
    return f"{ano}-{mes}-{dia}"


def nome_pdf(publicacao: Publicacao) -> str:
    parsed = urllib.parse.urlparse(publicacao.pdf_url)
    base = urllib.parse.unquote(Path(parsed.path).name)
    seguro = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    return f"edicao-{publicacao.edicao:02d}_{seguro}"


def baixar_pdf(publicacao: Publicacao, destino_dir: Path) -> Path:
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / nome_pdf(publicacao)
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    temporario = destino.with_suffix(destino.suffix + ".part")
    temporario.write_bytes(requisitar(publicacao.pdf_url))
    if not temporario.read_bytes().startswith(b"%PDF"):
        temporario.unlink(missing_ok=True)
        raise RuntimeError(f"Conteúdo baixado não é PDF: {publicacao.pdf_url}")
    temporario.replace(destino)
    return destino


def limpar_pagina(texto: str) -> str:
    linhas: list[str] = []
    for linha in texto.splitlines():
        n = normalizar(linha)
        if "boletim de jurisprudencia tcesp" in n and "tce.sp.gov.br/boletim-jurisprudencia" in n:
            continue
        if re.fullmatch(r"\d+", n):
            continue
        linhas.append(linha)
    return limpar_espacos("\n".join(linhas))


def extrair_paginas(pdf: Path) -> list[str]:
    reader = PdfReader(pdf)
    return [limpar_pagina(pagina.extract_text() or "") for pagina in reader.pages]


def cabecalhos_processos(paginas: Sequence[str]) -> list[tuple[int, int]]:
    """Retorna (página zero-based, offset) de cabeçalhos seguidos por sessão."""
    cabecalhos: list[tuple[int, int]] = []
    for indice, texto in enumerate(paginas):
        linhas = texto.splitlines(keepends=True)
        offsets: list[int] = []
        total = 0
        for linha in linhas:
            offsets.append(total)
            total += len(linha)
        candidatos: list[tuple[int, int]] = []
        for numero_linha, linha in enumerate(linhas):
            if not PADRAO_PROCESSO.search(linha):
                continue
            janela = "".join(linhas[numero_linha : numero_linha + 12])
            sessao = PADRAO_SESSAO.search(janela)
            if not sessao:
                continue
            # Evita tomar como novo cabeçalho referências jurisprudenciais no corpo.
            prefixo = linha.strip().lower()
            if numero_linha > 0 and not (
                prefixo.startswith(("➢", "processo", "tc-"))
                or re.match(r"^\d{5,6}\.989\.\d{2}(?:-\d)?", prefixo)
                or re.match(r"^\d{3,6}/\d{3}/\d{2}", prefixo)
            ):
                continue
            sessao_absoluta = offsets[numero_linha] + sessao.start()
            candidatos.append((offsets[numero_linha], sessao_absoluta))
        # Uma lista de processos pode quebrar em várias linhas. Todas enxergam a
        # mesma sessão adiante; conserva-se somente o começo mais antigo.
        por_sessao: dict[int, int] = {}
        for offset, sessao_offset in candidatos:
            por_sessao[sessao_offset] = min(offset, por_sessao.get(sessao_offset, offset))
        cabecalhos.extend((indice, offset) for _, offset in sorted(por_sessao.items()))
    return cabecalhos


def recortar_bloco(
    paginas: Sequence[str], inicio: tuple[int, int], fim: tuple[int, int] | None
) -> tuple[str, list[int]]:
    p_inicio, o_inicio = inicio
    if fim is None:
        p_fim, o_fim = len(paginas) - 1, len(paginas[-1])
    else:
        p_fim, o_fim = fim
    partes: list[str] = []
    usadas: list[int] = []
    for p in range(p_inicio, p_fim + 1):
        a = o_inicio if p == p_inicio else 0
        b = o_fim if p == p_fim else len(paginas[p])
        trecho = paginas[p][a:b].strip()
        if trecho:
            partes.append(trecho)
            usadas.append(p + 1)
    return limpar_espacos("\n\n".join(partes)), usadas


def termos_relevantes(bloco: str) -> list[str]:
    n = normalizar(bloco)
    return [nome for nome, padrao in EXPRESSOES_FORTES.items() if padrao.search(n)]


def detectar_temas(bloco: str) -> list[str]:
    n = normalizar(bloco)
    encontrados = {nome for nome, termos in TEMAS.items() if any(termo in n for termo in termos)}
    # Evita classificar art. 24, IV (emergência) como inciso I por prefixo textual.
    if re.search(r"\bart(?:igo)?\.?\s*(?:24|75)\s*,\s*(?:inciso\s*)?(?:i(?!v)|ii)\b", n):
        encontrados.add("dispensa por valor")
    return sorted(encontrados)


def detectar_regime(bloco: str) -> str:
    n = normalizar(bloco)
    regimes: list[str] = []
    if "14.133" in n:
        regimes.append("lei-14133")
    if "8.666" in n or "8666/93" in n:
        regimes.append("lei-8666")
    if "13.979" in n or "13979/2020" in n:
        regimes.append("lei-13979")
    return "+".join(regimes) if regimes else "nao-identificado"


def extrair_metadados(bloco: str, contexto_anterior: str) -> dict[str, object]:
    sessao = PADRAO_SESSAO.search(bloco)
    cabecalho = bloco[: sessao.start()] if sessao else bloco[:500]
    processos = []
    for valor in PADRAO_PROCESSO.findall(cabecalho):
        canonico = valor.upper()
        if not canonico.startswith("TC-"):
            canonico = "TC-" + canonico
        if canonico not in processos:
            processos.append(canonico)

    sessao_texto = texto_corrido(sessao.group(0)) if sessao else ""
    data_m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", sessao_texto)
    data_sessao = converter_data(data_m.group(1)) if data_m else NAO_IDENTIFICADO
    relator_m = re.search(r"relatoria\s*:\s*([^)]*)", sessao_texto, re.IGNORECASE)
    relator = texto_corrido(relator_m.group(1)) if relator_m else NAO_IDENTIFICADO

    if "plenária" in sessao_texto.lower() or "plenaria" in normalizar(sessao_texto):
        orgao = "TRIBUNAL PLENO"
    else:
        anteriores = re.findall(
            r"(?im)^\s*(Primeira Câmara|Segunda Câmara|Tribunal Pleno)(?:\s*\([^\n]*\))?\s*$",
            contexto_anterior,
        )
        orgao = anteriores[-1].upper() if anteriores else NAO_IDENTIFICADO

    ementa_m = re.search(r"EMENTA\s*:\s*([\s\S]*?)(?:\n\s*\n|$)", bloco, re.IGNORECASE)
    ementa = texto_corrido(ementa_m.group(1)) if ementa_m else NAO_IDENTIFICADO
    if ementa_m:
        registro = texto_corrido(bloco[ementa_m.end() :])
    else:
        pos_sessao = sessao.end() if sessao else 0
        registro = texto_corrido(bloco[pos_sessao:])
    if not registro:
        registro = NAO_IDENTIFICADO
    return {
        "processos": processos,
        "data_sessao": data_sessao,
        "relator": relator,
        "orgao_julgador": orgao,
        "ementa": ementa,
        "registro_boletim": registro,
    }


def slug_processo(processo: str) -> str:
    return re.sub(r"[^0-9]+", "-", processo).strip("-")


def caminho_relativo(caminho: Path) -> str:
    return caminho.relative_to(RAIZ).as_posix()


def montar_julgados(publicacao: Publicacao, pdf: Path, paginas: Sequence[str]) -> list[Julgado]:
    sha = sha256_arquivo(pdf)
    cabecalhos = cabecalhos_processos(paginas)
    julgados: list[Julgado] = []
    for indice, inicio in enumerate(cabecalhos):
        fim = cabecalhos[indice + 1] if indice + 1 < len(cabecalhos) else None
        bloco, paginas_usadas = recortar_bloco(paginas, inicio, fim)
        termos = termos_relevantes(bloco)
        if not termos:
            continue
        contexto = "\n".join(paginas[: inicio[0]]) + "\n" + paginas[inicio[0]][: inicio[1]]
        dados = extrair_metadados(bloco, contexto)
        processos = list(dados["processos"])
        principal = processos[0] if processos else f"edicao-{publicacao.edicao:02d}-pagina-{paginas_usadas[0]}"
        identificador = f"tcesp-{slug_processo(principal)}-b{publicacao.edicao:02d}-{sha[:12].lower()}"
        ficha = FICHAS_DIR / f"{identificador}.md"
        julgados.append(
            Julgado(
                id=identificador,
                edicao=publicacao.edicao,
                titulo_boletim=publicacao.titulo,
                pagina_publicacao_url=publicacao.pagina_url,
                pdf_url=publicacao.pdf_url,
                data_publicacao=publicacao.data_publicacao,
                arquivo_original=caminho_relativo(pdf),
                sha256=sha,
                tamanho_bytes=pdf.stat().st_size,
                paginas=paginas_usadas,
                processos=processos,
                data_sessao=str(dados["data_sessao"]),
                relator=str(dados["relator"]),
                orgao_julgador=str(dados["orgao_julgador"]),
                ementa=str(dados["ementa"]),
                registro_boletim=str(dados["registro_boletim"]),
                termos_selecao=termos,
                temas=detectar_temas(bloco),
                regime_legal=detectar_regime(bloco),
                ficha_path=caminho_relativo(ficha),
            )
        )
    return julgados


def yaml_string(valor: str) -> str:
    return json.dumps(valor, ensure_ascii=False)


def fonte_pagina(julgado: Julgado, pagina: int) -> str:
    return f"[Fonte: {julgado.arquivo_original}, p. {pagina}]"


def paginas_texto(paginas: Sequence[int]) -> str:
    if len(paginas) == 1:
        return str(paginas[0])
    return ", ".join(str(p) for p in paginas)


def renderizar_ficha(j: Julgado) -> str:
    processos = ", ".join(j.processos) if j.processos else NAO_IDENTIFICADO
    titulo = f"TCE-SP — {processos} — Boletim nº {j.edicao:02d}"
    tags = ["tce-sp", "contratacao-direta", "dispensa-de-licitacao", *j.temas]
    tags = list(dict.fromkeys(tags))
    pagina_inicial = j.paginas[0]
    citacao = fonte_pagina(j, pagina_inicial)
    return f'''---
tipo: jurisprudencia
hierarquia: persuasiva
tema: contratacao direta
subtemas: {json.dumps(j.temas, ensure_ascii=False)}
fonte: Tribunal de Contas do Estado de São Paulo / Boletim de Jurisprudência
processo: {yaml_string(processos)}
relator: {yaml_string(j.relator)}
orgao_julgador: {yaml_string(j.orgao_julgador)}
data_julgamento: {yaml_string(j.data_sessao)}
regime_legal: {yaml_string(j.regime_legal)}
status_precedente: verificar-inteiro-teor
vigencia: vigente
atualizado_em: {ATUALIZADO_EM}
arquivo_original: {yaml_string(j.arquivo_original)}
url_publicacao: {yaml_string(j.pagina_publicacao_url)}
url_pdf: {yaml_string(j.pdf_url)}
sha256: {yaml_string(j.sha256)}
tags: {json.dumps(tags, ensure_ascii=False)}
---

# {titulo}

> **Status:** registro extraído de boletim oficial do TCE-SP. O boletim contém síntese
> jurisprudencial e **não substitui o inteiro teor**. Antes de sustentar conclusão jurídica,
> localizar e ler a decisão completa, conferir voto vencedor, contexto fático e eventual recurso.

## 1. Identificação

- Processo(s): {processos} {citacao}
- Órgão julgador: {j.orgao_julgador} {citacao}
- Sessão/julgamento: {j.data_sessao} {citacao}
- Relatoria: {j.relator} {citacao}
- Boletim: edição nº {j.edicao:02d}; publicação em {j.data_publicacao}.
- Páginas do registro: {paginas_texto(j.paginas)}.
- Regime detectado mecanicamente: {j.regime_legal}; exige conferência no inteiro teor.

## 2. Resumo objetivo

{j.ementa if j.ementa != NAO_IDENTIFICADO else j.registro_boletim} {citacao}

## 3. Tese principal

Não identificada como tese autônoma além do registro oficial do boletim. A síntese acima não foi
ampliada por inferência.

## 4. Fundamentos citados

{j.registro_boletim} {citacao}

## 5. Aplicação prática na Câmara de Itanhandu

**Interpretação do Charles — pendente de validação humana:** o registro foi recuperado pelos termos
{", ".join(j.termos_selecao)} e pelos temas {", ".join(j.temas) if j.temas else "não classificados"}.
Seu uso exige comparação do caso concreto com a legislação e as normas internas vigentes, que têm
precedência sobre esta jurisprudência persuasiva de outro Estado.

## 6. Trechos relevantes

> {j.ementa if j.ementa != NAO_IDENTIFICADO else j.registro_boletim}
>
> {citacao}

## 7. Riscos e cautelas

- O boletim é fonte oficial de síntese, mas não contém necessariamente todo o fundamento do voto.
- Não presumir que a manifestação resumida é vinculante ou aplicável à Lei nº 14.133/2021.
- Não transplantar automaticamente precedente regido pela Lei nº 8.666/1993 ou por legislação emergencial.
- Conferir o inteiro teor antes de atribuir conduta, sanção, tese ou resultado a responsável específico.

## 8. Fontes

- PDF oficial: [{j.titulo_boletim}]({j.pdf_url}) — páginas {paginas_texto(j.paginas)}; SHA-256 `{j.sha256}`.
- Página oficial da publicação: [{j.pagina_publicacao_url}]({j.pagina_publicacao_url}).
- Original preservado: `{j.arquivo_original}`.
'''


def escrever_texto_extraido(publicacao: Publicacao, paginas: Sequence[str]) -> Path:
    TEXTOS_DIR.mkdir(parents=True, exist_ok=True)
    destino = TEXTOS_DIR / f"boletim-{publicacao.edicao:02d}.txt"
    conteudo = "\n\n".join(
        f"===== PÁGINA {indice} =====\n{texto}" for indice, texto in enumerate(paginas, 1)
    )
    destino.write_text(conteudo.rstrip() + "\n", encoding="utf-8")
    return destino


def escrever_fichas(julgados: Sequence[Julgado], destino_dir: Path = FICHAS_DIR) -> None:
    destino_dir.mkdir(parents=True, exist_ok=True)
    ids_atuais = {j.id for j in julgados}
    for existente in destino_dir.glob("tcesp-*.md"):
        if existente.stem not in ids_atuais:
            existente.unlink()
    for julgado in julgados:
        (destino_dir / f"{julgado.id}.md").write_text(renderizar_ficha(julgado), encoding="utf-8")


def escrever_indices(publicacoes: Sequence[Publicacao], julgados: Sequence[Julgado]) -> None:
    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    manifesto_path = INDICES_DIR / "manifesto_boletins.jsonl"
    linhas_manifesto = []
    for pub in publicacoes:
        pdf = ORIGINAIS_DIR / nome_pdf(pub)
        linhas_manifesto.append(
            {
                "edition": pub.edicao,
                "title": pub.titulo,
                "publication_date": pub.data_publicacao,
                "publication_url": pub.pagina_url,
                "pdf_url": pub.pdf_url,
                "source_path": caminho_relativo(pdf),
                "sha256": sha256_arquivo(pdf),
                "size_bytes": pdf.stat().st_size,
            }
        )
    manifesto_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in linhas_manifesto),
        encoding="utf-8",
    )

    catalogo_jsonl = INDICES_DIR / "catalogo_julgados.jsonl"
    catalogo_jsonl.write_text(
        "".join(json.dumps(asdict(j), ensure_ascii=False, sort_keys=True) + "\n" for j in julgados),
        encoding="utf-8",
    )
    catalogo_csv = INDICES_DIR / "catalogo_julgados.csv"
    campos = [
        "id", "edicao", "data_publicacao", "processos", "data_sessao", "relator",
        "orgao_julgador", "paginas", "regime_legal", "temas", "termos_selecao",
        "arquivo_original", "sha256", "pagina_publicacao_url", "pdf_url", "ficha_path",
    ]
    with catalogo_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=campos)
        writer.writeheader()
        for j in julgados:
            registro = asdict(j)
            for campo in ("processos", "paginas", "temas", "termos_selecao"):
                registro[campo] = " | ".join(map(str, registro[campo]))
            writer.writerow({campo: registro[campo] for campo in campos})


def escrever_readme(julgados: Sequence[Julgado], publicacoes: Sequence[Publicacao]) -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    primeiro = min((p.edicao for p in publicacoes), default=0)
    ultimo = max((p.edicao for p in publicacoes), default=0)
    conteudo = f'''---
tipo: jurisprudencia
hierarquia: persuasiva
tema: contratacao direta
fonte: Tribunal de Contas do Estado de São Paulo / Boletins de Jurisprudência
vigencia: vigente
atualizado_em: {ATUALIZADO_EM}
tags: [tce-sp, boletim-de-jurisprudencia, contratacao-direta, dispensa-de-licitacao]
---

# Corpus TCE-SP — contratação direta e dispensa de licitação

Corpus derivado das {len(publicacoes)} edições oficiais do Boletim de Jurisprudência do TCE-SP
(edições {primeiro:02d} a {ultimo:02d}), com {len(julgados)} registros de julgados selecionados.

## Escopo e método

- Fonte de descoberta: `{LISTAGEM_URL}`.
- Seleção conservadora por bloco completo de processo/sessão, mediante expressões inequívocas de
  contratação direta ou dispensa de licitação.
- Cada ocorrência conserva edição, processo, página, URL oficial, original e SHA-256.
- Falsos positivos do mecanismo de busca do portal (como “dispensa a elaboração”) não entram.
- OCR não é usado quando o PDF já contém texto pesquisável.

## Limite jurídico essencial

O boletim é fonte oficial de síntese, mas não substitui o inteiro teor. As fichas estão marcadas
`verificar-inteiro-teor`; nenhuma delas, isoladamente, autoriza afirmar tese, sanção ou contexto não
expresso no registro. O TCE-SP é jurisprudência persuasiva de outro Estado e não supera lei, norma
aplicável, regulamento interno ou jurisprudência competente do TCE-MG.

## Estrutura

- `fichas/`: um registro por bloco de julgado.
- `texto_extraido/`: texto integral paginado de cada boletim.
- `indices/manifesto_boletins.jsonl`: URLs, caminhos e hashes dos PDFs.
- `indices/catalogo_julgados.jsonl` e `.csv`: catálogo estruturado.
- `consolidacoes/MAPA_TEMATICO_CONTRATACAO_DIRETA.md`: navegação por cautela/tema.
'''
    (BASE_DIR / "README.md").write_text(conteudo, encoding="utf-8")


def escrever_mapa(julgados: Sequence[Julgado]) -> None:
    CONSOLIDACOES_DIR.mkdir(parents=True, exist_ok=True)
    por_tema: dict[str, list[Julgado]] = {}
    for j in julgados:
        temas = j.temas or ["outros aspectos de contratação direta"]
        for tema in temas:
            por_tema.setdefault(tema, []).append(j)
    linhas = [
        "---",
        "tipo: jurisprudencia",
        "hierarquia: persuasiva",
        "tema: contratacao direta",
        "fonte: Tribunal de Contas do Estado de São Paulo / Boletins de Jurisprudência",
        "vigencia: vigente",
        f"atualizado_em: {ATUALIZADO_EM}",
        "tags: [tce-sp, mapa-tematico, contratacao-direta, dispensa-de-licitacao]",
        "---",
        "",
        "# Mapa temático — contratação direta nos boletins do TCE-SP",
        "",
        "> Índice mecânico para localização. A ficha e o inteiro teor devem ser conferidos antes do uso jurídico.",
        "",
    ]
    for tema in sorted(por_tema):
        linhas.extend([f"## {tema}", ""])
        for j in sorted(por_tema[tema], key=lambda x: (x.data_sessao, x.id)):
            processos = ", ".join(j.processos) if j.processos else NAO_IDENTIFICADO
            rel = Path("..") / Path(j.ficha_path).relative_to(BASE_DIR.relative_to(RAIZ))
            resumo = j.ementa if j.ementa != NAO_IDENTIFICADO else j.registro_boletim
            if len(resumo) > 240:
                resumo = resumo[:237].rstrip() + "..."
            linhas.append(
                f"- [{processos}](../fichas/{j.id}.md) — boletim {j.edicao:02d}, "
                f"p. {paginas_texto(j.paginas)}; {resumo}"
            )
        linhas.append("")
    (CONSOLIDACOES_DIR / "MAPA_TEMATICO_CONTRATACAO_DIRETA.md").write_text(
        "\n".join(linhas).rstrip() + "\n", encoding="utf-8"
    )


def filtrar_edicoes(publicacoes: Sequence[Publicacao], edicoes: set[int] | None) -> list[Publicacao]:
    if not edicoes:
        return list(publicacoes)
    faltantes = sorted(edicoes - {p.edicao for p in publicacoes})
    if faltantes:
        raise RuntimeError(f"Edições não localizadas: {', '.join(map(str, faltantes))}")
    return [p for p in publicacoes if p.edicao in edicoes]


def validar_resultado(publicacoes: Sequence[Publicacao], julgados: Sequence[Julgado]) -> list[str]:
    erros: list[str] = []
    ids: set[str] = set()
    for pub in publicacoes:
        pdf = ORIGINAIS_DIR / nome_pdf(pub)
        if not pdf.exists():
            erros.append(f"Original ausente: {pdf}")
        elif not pdf.read_bytes().startswith(b"%PDF"):
            erros.append(f"Original inválido: {pdf}")
    for j in julgados:
        if j.id in ids:
            erros.append(f"ID duplicado: {j.id}")
        ids.add(j.id)
        if not j.paginas:
            erros.append(f"Sem página: {j.id}")
        if not j.processos:
            erros.append(f"Sem processo: {j.id}")
        if not j.termos_selecao:
            erros.append(f"Sem termo de seleção: {j.id}")
        ficha = RAIZ / j.ficha_path
        if not ficha.exists():
            erros.append(f"Ficha ausente: {j.ficha_path}")
        elif j.sha256 not in ficha.read_text(encoding="utf-8"):
            erros.append(f"Hash ausente da ficha: {j.ficha_path}")
    return erros


def processar(edicoes: set[int] | None = None, somente_descobrir: bool = False) -> int:
    todas = descobrir_publicacoes()
    selecionadas = filtrar_edicoes(todas, edicoes)
    print(f"Publicações descobertas: {len(todas)}; selecionadas: {len(selecionadas)}")
    if somente_descobrir:
        for p in selecionadas:
            print(f"{p.edicao:02d}\t{p.data_publicacao}\t{p.pdf_url}")
        return 0

    julgados: list[Julgado] = []
    for pub in selecionadas:
        pdf = baixar_pdf(pub, ORIGINAIS_DIR)
        paginas = extrair_paginas(pdf)
        escrever_texto_extraido(pub, paginas)
        encontrados = montar_julgados(pub, pdf, paginas)
        julgados.extend(encontrados)
        print(
            f"Edição {pub.edicao:02d}: {len(paginas)} página(s), "
            f"{len(encontrados)} julgado(s), SHA-256 {sha256_arquivo(pdf)[:12]}..."
        )

    julgados.sort(key=lambda j: (j.data_sessao, j.edicao, j.id))
    escrever_fichas(julgados)
    escrever_indices(selecionadas, julgados)
    escrever_readme(julgados, selecionadas)
    escrever_mapa(julgados)
    erros = validar_resultado(selecionadas, julgados)
    if erros:
        print("Falhas de validação:")
        for erro in erros:
            print(f"- {erro}")
        return 1
    print(f"Validação concluída: {len(julgados)} julgado(s), sem erro mecânico.")
    return 0


def parse_edicoes(valor: str | None) -> set[int] | None:
    if not valor:
        return None
    return {int(item.strip()) for item in valor.split(",") if item.strip()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edicoes", help="Lista separada por vírgulas; padrão: todas")
    parser.add_argument("--somente-descobrir", action="store_true")
    args = parser.parse_args(argv)
    return processar(parse_edicoes(args.edicoes), args.somente_descobrir)


if __name__ == "__main__":
    raise SystemExit(main())
