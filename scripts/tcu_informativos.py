#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coleta informativos do TCU sobre contratação direta e dispensa de licitação.

O recorte padrão compreende os Informativos de Licitações e Contratos 452 a 531.
A seleção é feita nos enunciados do sumário, evitando que simples menções incidentais
no histórico do processo gerem falsos positivos. Cada ficha conserva PDF, página,
URL, acórdão e SHA-256 e permanece marcada para conferência do inteiro teor.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Sequence

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - mensagem operacional
    raise SystemExit(
        "Dependência ausente: instale requirements-auditor.txt (pypdf)."
    ) from exc


RAIZ = Path(__file__).resolve().parents[1]
LISTAGEM_URL = (
    "https://portal.tcu.gov.br/jurisprudencia"
    "?tipo=Informativo+de+Licita%C3%A7%C3%B5es+e+Contratos"
)
INICIO_PADRAO = 452
FIM_PADRAO = 531
ORIGINAIS_DIR = RAIZ / "TCU_INFORMATIVOS_LICITACOES_CONTRATOS"
BASE_DIR = RAIZ / "03_jurisprudencia" / "tcu" / "informativos_licitacoes_contratos"
FICHAS_DIR = BASE_DIR / "fichas"
TEXTOS_DIR = BASE_DIR / "texto_extraido"
INDICES_DIR = BASE_DIR / "indices"
CONSOLIDACOES_DIR = BASE_DIR / "consolidacoes"
ATUALIZADO_EM = date.today().isoformat()
USER_AGENT = "Charles-TCU-Informativos/1.0 (pesquisa documental institucional)"
NAO_IDENTIFICADO = "Não identificado no documento"

ROW_RE = re.compile(r"<tr\b[^>]*>([\s\S]*?)</tr>", re.IGNORECASE)
TITLE_RE = re.compile(r"Informativo de Licitações e Contratos\s+(\d+)", re.IGNORECASE)
DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
TOTAL_PAGES_RE = re.compile(r'"totalPages"\s*:\s*(\d+)')
ACORDAO_RE = re.compile(
    r"Acórdão\s+([\d.]+/\d{4})(?:-TCU)?\s+"
    r"(Plenário|Primeira Câmara|Segunda Câmara)\s*,?\s*"
    r"([^,\n]+?)\s*,\s*(Relator(?:a)?|Revisor(?:a)?)\s+([^\.\n]+)\.",
    re.IGNORECASE,
)
ORGAO_SUMARIO_RE = re.compile(r"^(Plenário|Primeira Câmara|Segunda Câmara)\s*$", re.IGNORECASE)
ORGAO_DETALHE_RE = re.compile(r"^(PLENÁRIO|PRIMEIRA CÂMARA|SEGUNDA CÂMARA)\s*$")
INICIO_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")

PADROES_SELECAO: dict[str, re.Pattern[str]] = {
    "contratação direta": re.compile(r"\bcontrata(?:ção|ções)\s+direta(?:s)?\b", re.IGNORECASE),
    "dispensa de licitação": re.compile(r"\bdispensa(?:s)?\s+de\s+licita(?:ção|ções)\b", re.IGNORECASE),
    "inexigibilidade de licitação": re.compile(
        r"\binexigibilidade(?:s)?(?:\s+de\s+licita(?:ção|ções))?\b", re.IGNORECASE
    ),
    "licitação dispensável ou dispensada": re.compile(
        r"\blicita(?:ção|ções)\s+dispens(?:ável|áveis|ada|adas)\b", re.IGNORECASE
    ),
    "contratação emergencial": re.compile(
        r"\bcontrata(?:ção|ções)\s+(?:direta(?:s)?\s+)?emergencial(?:is)?\b", re.IGNORECASE
    ),
    "contratação sem licitação": re.compile(
        r"\bcontrata(?:ção|ções|do|da|dos|das|r)\b[\s\S]{0,90}\bsem\s+(?:prévia\s+)?licita(?:ção|ções)\b",
        re.IGNORECASE,
    ),
    "fornecedor exclusivo": re.compile(r"\bfornecedor(?:es)?\s+exclusivo(?:s)?\b", re.IGNORECASE),
    "credenciamento": re.compile(r"\bcredenciamento\b", re.IGNORECASE),
    "fundamento legal de contratação direta": re.compile(
        r"\bart(?:igo)?\.?\s*(?:24|25)\b[\s\S]{0,90}\bLei\s+(?:n[ºo]\.?\s*)?8\.666"
        r"|\bart(?:igo)?\.?\s+(?:74|75)\b[\s\S]{0,90}\bLei\s+(?:n[ºo]\.?\s*)?14\.133",
        re.IGNORECASE,
    ),
}

TEMAS: dict[str, tuple[str, ...]] = {
    "emergência": ("emergenc", "calamidade", "urgência"),
    "dispensa por valor": ("dispensa por valor", "pequeno valor", "baixo valor", "fracionamento"),
    "inexigibilidade e exclusividade": ("inexigib", "fornecedor exclusivo", "exclusividade"),
    "credenciamento": ("credenciamento", "credenciado"),
    "pesquisa e justificativa de preços": ("pesquisa de preços", "justificativa de preço", "preço de mercado"),
    "escolha do contratado": ("razão da escolha", "escolha do fornecedor", "escolha do contratado"),
    "planejamento": ("planejamento", "falta de planejamento", "desídia", "previsível"),
    "fracionamento": ("fracionamento", "parcelamento indevido"),
    "publicidade e transparência": ("publicidade", "publicação", "transparência"),
    "licitação deserta ou fracassada": ("licitação deserta", "licitação fracassada", "certame deserto"),
    "contratação de remanescente": ("remanescente", "remanescente de obra", "remanescente de serviço"),
    "serviços técnicos especializados": ("serviço técnico especializado", "notória especialização"),
    "instrução e parecer jurídico": ("parecer jurídico", "instrução processual", "processo administrativo"),
    "responsabilização": ("responsabil", "multa", "débito"),
}


@dataclass(frozen=True)
class Publicacao:
    numero: int
    titulo: str
    data_publicacao: str
    data_atualizacao: str
    pagina_listagem: int
    pagina_url: str
    pdf_url: str
    word_url: str


@dataclass(frozen=True)
class ItemSumario:
    numero: int
    orgao: str
    enunciado: str


@dataclass
class Julgado:
    id: str
    informativo: int
    titulo_informativo: str
    data_publicacao: str
    acordao: str
    orgao_julgador: str
    classe_processual: str
    relator: str
    responsavel_citacao: str
    numero_item: int
    enunciado: str
    registro_informativo: str
    paginas: list[int]
    termos_selecao: list[str]
    temas: list[str]
    regime_legal: str
    pagina_publicacao_url: str
    pdf_url: str
    url_inteiro_teor: str
    arquivo_original: str
    sha256: str
    tamanho_bytes: int
    ficha_path: str


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip().lower()


def limpar_espacos(texto: str) -> str:
    linhas = [re.sub(r"[ \t]+", " ", linha).strip() for linha in texto.splitlines()]
    saida: list[str] = []
    for linha in linhas:
        if not linha:
            if saida and saida[-1] != "":
                saida.append("")
        else:
            saida.append(linha)
    return "\n".join(saida).strip()


def texto_corrido(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def converter_data(valor: str) -> str:
    dia, mes, ano = valor.split("/")
    return f"{ano}-{mes}-{dia}"


def caminho_relativo(caminho: Path) -> str:
    return caminho.relative_to(RAIZ).as_posix()


def sha256_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as stream:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest().upper()


def requisitar(url: str) -> bytes:
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(pedido, timeout=90) as resposta:
            return resposta.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha ao acessar {url}: {exc}") from exc


def texto_html(fragmento: str) -> str:
    return texto_corrido(html.unescape(re.sub(r"<[^>]+>", " ", fragmento)))


def descobrir_publicacoes(inicio: int, fim: int) -> list[Publicacao]:
    primeira = requisitar(LISTAGEM_URL).decode("utf-8", errors="replace")
    m_paginas = TOTAL_PAGES_RE.search(primeira)
    total_paginas = int(m_paginas.group(1)) if m_paginas else 36
    registros: dict[int, Publicacao] = {}
    for pagina in range(1, total_paginas + 1):
        url = f"{LISTAGEM_URL}&pagina={pagina}"
        conteudo = primeira if pagina == 1 else requisitar(url).decode("utf-8", errors="replace")
        numeros_pagina: list[int] = []
        for row in ROW_RE.findall(conteudo):
            texto = texto_html(row)
            m_titulo = TITLE_RE.search(texto)
            if not m_titulo:
                continue
            numero = int(m_titulo.group(1))
            numeros_pagina.append(numero)
            if not inicio <= numero <= fim:
                continue
            datas = DATE_RE.findall(texto)
            hrefs = [html.unescape(v) for v in HREF_RE.findall(row)]
            arquivos = [v for v in hrefs if "ObterDocumentoSisdoc" in v]
            if not arquivos:
                raise RuntimeError(f"PDF não localizado no portal para o informativo {numero}")
            pdf_url = next((v for v in arquivos if "codVersao=" not in v), arquivos[0])
            word_url = next((v for v in arquivos if "codVersao=" in v), NAO_IDENTIFICADO)
            registros[numero] = Publicacao(
                numero=numero,
                titulo=f"Informativo de Licitações e Contratos {numero}",
                data_publicacao=converter_data(datas[0]) if datas else NAO_IDENTIFICADO,
                data_atualizacao=converter_data(datas[1]) if len(datas) > 1 else NAO_IDENTIFICADO,
                pagina_listagem=pagina,
                pagina_url=url,
                pdf_url=pdf_url,
                word_url=word_url,
            )
        if numeros_pagina and min(numeros_pagina) < inicio:
            break
    faltantes = sorted(set(range(inicio, fim + 1)) - set(registros))
    if faltantes:
        raise RuntimeError("Informativos não localizados: " + ", ".join(map(str, faltantes)))
    return [registros[n] for n in sorted(registros)]


def nome_pdf(publicacao: Publicacao) -> str:
    return f"informativo-{publicacao.numero:03d}.pdf"


def baixar_pdf(publicacao: Publicacao) -> Path:
    ORIGINAIS_DIR.mkdir(parents=True, exist_ok=True)
    destino = ORIGINAIS_DIR / nome_pdf(publicacao)
    if destino.exists():
        if destino.stat().st_size == 0 or not destino.read_bytes()[:4] == b"%PDF":
            raise RuntimeError(f"Original existente é inválido e não será sobrescrito: {destino}")
        return destino
    temporario = destino.with_suffix(".pdf.part")
    conteudo = requisitar(publicacao.pdf_url)
    if not conteudo.startswith(b"%PDF"):
        raise RuntimeError(f"Conteúdo baixado não é PDF: {publicacao.pdf_url}")
    temporario.write_bytes(conteudo)
    temporario.replace(destino)
    return destino


def limpar_pagina(texto: str) -> str:
    linhas: list[str] = []
    for linha in texto.replace("\x00", "").splitlines():
        n = normalizar(linha)
        if re.fullmatch(r"\d+", n):
            continue
        if n.startswith("elaboracao: diretoria de jurisprudencia"):
            continue
        if n.startswith("contato: jurisprudenciafaleconosco"):
            continue
        linhas.append(linha)
    resultado = limpar_espacos("\n".join(linhas))
    # Repara apenas quebras gráficas conhecidas do gerador dos informativos.
    # Não é uma junção genérica e não altera o conteúdo jurídico extraído.
    reparos = {
        r"\bRelato\s+r\b": "Relator",
        r"\bAcórd\s+ão\b": "Acórdão",
        r"\bPlená\s+rio\b": "Plenário",
        r"\bCâ\s+mara\b": "Câmara",
        r"\bcontrata\s+ção\b": "contratação",
        r"\bcontrata\s+ções\b": "contratações",
        r"\blicita\s+ção\b": "licitação",
        r"\blicita\s+ções\b": "licitações",
        r"\binexigibili\s+dade\b": "inexigibilidade",
        r"\bMinistr([oa])\s+-\s*Substitut([oa])\b": r"Ministr\1-Substitut\2",
    }
    for padrao, substituto in reparos.items():
        resultado = re.sub(padrao, substituto, resultado, flags=re.IGNORECASE)
    return resultado


def extrair_paginas(pdf: Path) -> tuple[PdfReader, list[str]]:
    reader = PdfReader(pdf)
    return reader, [limpar_pagina(p.extract_text() or "") for p in reader.pages]


def juntar_paginas(paginas: Sequence[str]) -> tuple[str, list[tuple[int, int]]]:
    partes: list[str] = []
    intervalos: list[tuple[int, int]] = []
    cursor = 0
    for texto in paginas:
        if partes:
            separador = "\n\n"
            partes.append(separador)
            cursor += len(separador)
        inicio = cursor
        partes.append(texto)
        cursor += len(texto)
        intervalos.append((inicio, cursor))
    return "".join(partes), intervalos


def paginas_do_intervalo(inicio: int, fim: int, intervalos: Sequence[tuple[int, int]]) -> list[int]:
    return [i for i, (a, b) in enumerate(intervalos, 1) if inicio < b and fim > a]


def localizar_limite_sumario(texto: str) -> tuple[int, int]:
    m_sumario = re.search(r"(?m)^\s*SUMÁRIO\s*$", texto)
    if not m_sumario:
        raise RuntimeError("Marcador SUMÁRIO não localizado")
    for m in re.finditer(r"(?m)^\s*(PLENÁRIO|PRIMEIRA CÂMARA|SEGUNDA CÂMARA)\s*$", texto):
        if m.start() > m_sumario.end():
            return m_sumario.end(), m.start()
    raise RuntimeError("Início da seção detalhada não localizado")


def extrair_sumario(texto: str) -> tuple[list[ItemSumario], int]:
    inicio, fim = localizar_limite_sumario(texto)
    linhas = texto[inicio:fim].splitlines()
    itens: list[ItemSumario] = []
    orgao = NAO_IDENTIFICADO
    numero_atual: int | None = None
    fragmentos: list[str] = []

    def concluir() -> None:
        nonlocal numero_atual, fragmentos
        if numero_atual is not None:
            itens.append(ItemSumario(numero_atual, orgao, texto_corrido(" ".join(fragmentos))))
        numero_atual = None
        fragmentos = []

    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        m_orgao = ORGAO_SUMARIO_RE.match(linha)
        if m_orgao:
            concluir()
            orgao = m_orgao.group(1).title()
            continue
        m_item = INICIO_ITEM_RE.match(linha)
        if m_item:
            concluir()
            numero_atual = int(m_item.group(1))
            fragmentos = [m_item.group(2)]
        elif numero_atual is not None:
            fragmentos.append(linha)
    concluir()
    return itens, fim


def urls_anotacoes(reader: PdfReader) -> list[str]:
    urls: list[str] = []
    for pagina in reader.pages:
        for referencia in pagina.get("/Annots") or []:
            anotacao = referencia.get_object()
            acao = anotacao.get("/A")
            url = acao.get("/URI") if acao else None
            if isinstance(url, str) and url not in urls:
                urls.append(url)
    return urls


def localizar_url_inteiro_teor(acordao: str, urls: Sequence[str]) -> str:
    numero, ano = acordao.split("/")
    numero = numero.replace(".", "")
    marcador_numero = f"NUMACORDAO%253A{numero}".lower()
    marcador_ano = f"ANOACORDAO%253A{ano}".lower()
    for url in urls:
        url_baixa = url.lower()
        if marcador_numero in url_baixa and marcador_ano in url_baixa:
            return url
    return NAO_IDENTIFICADO


def termos_relevantes(enunciado: str) -> list[str]:
    return [nome for nome, padrao in PADROES_SELECAO.items() if padrao.search(enunciado)]


def detectar_temas(enunciado: str, registro: str) -> list[str]:
    n = normalizar(enunciado + " " + registro[:2500])
    temas = {nome for nome, termos in TEMAS.items() if any(normalizar(t) in n for t in termos)}
    if re.search(r"\bart(?:igo)?\.?\s*(?:24|75)\s*,?\s*(?:inciso\s*)?(?:i(?!v)|ii)\b", n):
        temas.add("dispensa por valor")
    return sorted(temas)


def detectar_regime(enunciado: str, registro: str) -> str:
    n = normalizar(enunciado + " " + registro)
    regimes: list[str] = []
    for nome, termos in (
        ("lei-14133", ("14.133", "14133/2021")),
        ("lei-8666", ("8.666", "8666/1993", "8666/93")),
        ("lei-13303", ("13.303", "13303/2016")),
        ("lei-13979", ("13.979", "13979/2020")),
        ("lei-10520", ("10.520", "10520/2002")),
        ("rdc-lei-12462", ("12.462", "12462/2011")),
    ):
        if any(t in n for t in termos):
            regimes.append(nome)
    return "+".join(regimes) if regimes else "nao-identificado"


def slug(valor: str) -> str:
    valor = normalizar(valor)
    return re.sub(r"[^a-z0-9]+", "-", valor).strip("-")


def montar_julgados(
    publicacao: Publicacao,
    pdf: Path,
    reader: PdfReader,
    paginas: Sequence[str],
) -> list[Julgado]:
    texto, intervalos = juntar_paginas(paginas)
    sumario, inicio_detalhes = extrair_sumario(texto)
    citacoes = list(ACORDAO_RE.finditer(texto))
    if len(sumario) != len(citacoes):
        raise RuntimeError(
            f"Informativo {publicacao.numero}: {len(sumario)} itens no sumário e "
            f"{len(citacoes)} citações finais"
        )
    urls = urls_anotacoes(reader)
    sha = sha256_arquivo(pdf)
    julgados: list[Julgado] = []
    cursor = inicio_detalhes
    for item, citacao in zip(sumario, citacoes):
        trecho_antes = texto[cursor:citacao.start()]
        m_inicio = re.search(r"(?m)^\s*\d+\.\s+", trecho_antes)
        inicio_bloco = cursor + m_inicio.start() if m_inicio else cursor
        fim_bloco = citacao.end()
        registro = limpar_espacos(texto[inicio_bloco:fim_bloco])
        paginas_bloco = paginas_do_intervalo(inicio_bloco, fim_bloco, intervalos)
        acordao, orgao, classe, papel, nome_responsavel = [
            texto_corrido(v) for v in citacao.groups()
        ]
        relator = nome_responsavel if normalizar(papel).startswith("relator") else NAO_IDENTIFICADO
        responsavel_citacao = f"{papel} {nome_responsavel}"
        termos = termos_relevantes(item.enunciado)
        if termos:
            identificador = (
                f"tcu-acordao-{slug(acordao)}-informativo-{publicacao.numero}-item-{item.numero}"
            )
            ficha = FICHAS_DIR / f"{identificador}.md"
            julgados.append(
                Julgado(
                    id=identificador,
                    informativo=publicacao.numero,
                    titulo_informativo=publicacao.titulo,
                    data_publicacao=publicacao.data_publicacao,
                    acordao=acordao,
                    orgao_julgador=orgao,
                    classe_processual=classe,
                    relator=relator,
                    responsavel_citacao=responsavel_citacao,
                    numero_item=item.numero,
                    enunciado=item.enunciado,
                    registro_informativo=registro,
                    paginas=paginas_bloco,
                    termos_selecao=termos,
                    temas=detectar_temas(item.enunciado, registro),
                    regime_legal=detectar_regime(item.enunciado, registro),
                    pagina_publicacao_url=publicacao.pagina_url,
                    pdf_url=publicacao.pdf_url,
                    url_inteiro_teor=localizar_url_inteiro_teor(acordao, urls),
                    arquivo_original=caminho_relativo(pdf),
                    sha256=sha,
                    tamanho_bytes=pdf.stat().st_size,
                    ficha_path=caminho_relativo(ficha),
                )
            )
        cursor = citacao.end()
    return julgados


def paginas_texto(paginas: Sequence[int]) -> str:
    return str(paginas[0]) if len(paginas) == 1 else ", ".join(map(str, paginas))


def yaml_string(valor: str) -> str:
    return json.dumps(valor, ensure_ascii=False)


def renderizar_ficha(j: Julgado) -> str:
    titulo = f"TCU — Acórdão {j.acordao} {j.orgao_julgador} — Informativo {j.informativo}"
    citacao_enunciado = f"[Fonte: {j.arquivo_original}, p. {j.paginas[0]}]"
    citacao_final = f"[Fonte: {j.arquivo_original}, p. {j.paginas[-1]}]"
    tags = list(dict.fromkeys(["tcu", "informativo-licitacoes-contratos", "contratacao-direta", *j.temas]))
    inteiro_teor = (
        f"[{j.url_inteiro_teor}]({j.url_inteiro_teor})"
        if j.url_inteiro_teor != NAO_IDENTIFICADO
        else NAO_IDENTIFICADO
    )
    return f'''---
tipo: jurisprudencia
hierarquia: persuasiva
tema: contratacao direta
subtemas: {json.dumps(j.temas, ensure_ascii=False)}
fonte: Tribunal de Contas da União / Informativo de Licitações e Contratos
acordao: {yaml_string(j.acordao)}
relator: {yaml_string(j.relator)}
responsavel_citacao: {yaml_string(j.responsavel_citacao)}
orgao_julgador: {yaml_string(j.orgao_julgador)}
classe_processual: {yaml_string(j.classe_processual)}
regime_legal: {yaml_string(j.regime_legal)}
status_precedente: verificar-inteiro-teor
status_publicacao: nao-repositorio-oficial
vigencia: vigente
atualizado_em: {ATUALIZADO_EM}
arquivo_original: {yaml_string(j.arquivo_original)}
url_publicacao: {yaml_string(j.pagina_publicacao_url)}
url_pdf: {yaml_string(j.pdf_url)}
url_inteiro_teor: {yaml_string(j.url_inteiro_teor)}
sha256: {yaml_string(j.sha256)}
tags: {json.dumps(tags, ensure_ascii=False)}
---

# {titulo}

> **Status:** enunciado e narrativa extraídos do Informativo de Licitações e Contratos do TCU.
> O próprio informativo declara que suas informações **não constituem resumo oficial da decisão**
> nem representam necessariamente o posicionamento prevalecente do Tribunal. Conferir o inteiro teor.

## 1. Identificação

- Acórdão: {j.acordao} {citacao_final}
- Colegiado: {j.orgao_julgador} {citacao_final}
- Classe processual: {j.classe_processual} {citacao_final}
- Responsável indicado na citação final: {j.responsavel_citacao} {citacao_final}
- Informativo: nº {j.informativo}, item {j.numero_item}; publicação em {j.data_publicacao}.
- Páginas do registro: {paginas_texto(j.paginas)}.
- Regime detectado mecanicamente: {j.regime_legal}; exige conferência no inteiro teor.

## 2. Resumo objetivo

{j.enunciado} {citacao_enunciado}

## 3. Tese principal

O enunciado acima é a síntese editorial publicada pelo TCU. Nenhuma tese adicional foi criada por
inferência nesta ficha.

## 4. Registro narrativo do informativo

{j.registro_informativo}

[Fonte: {j.arquivo_original}, p. {paginas_texto(j.paginas)}]

## 5. Aplicação prática na Câmara de Itanhandu

**Interpretação do Charles — pendente de validação humana:** registro recuperado pelos termos
{", ".join(j.termos_selecao)} e classificado nos temas
{", ".join(j.temas) if j.temas else "não classificados"}. Antes do uso, comparar os fatos e o regime
legal do acórdão com a Lei nº 14.133/2021 e as normas internas vigentes.

## 6. Cautelas

- O informativo facilita a pesquisa, mas não substitui o acórdão e o voto condutor.
- Não presumir caráter vinculante; verificar a natureza da deliberação e seus destinatários.
- Não aplicar automaticamente entendimento de regime legal revogado ou de contexto fático distinto.
- Conferir no inteiro teor eventuais ressalvas, modulação, determinações e recursos posteriores.

## 7. Fontes

- PDF oficial: [{j.titulo_informativo}]({j.pdf_url}) — páginas {paginas_texto(j.paginas)}; SHA-256 `{j.sha256}`.
- Inteiro teor indicado no PDF: {inteiro_teor}.
- Página oficial da coleção: [{LISTAGEM_URL}]({LISTAGEM_URL}).
- Original preservado: `{j.arquivo_original}`.
'''


def escrever_texto_extraido(publicacao: Publicacao, paginas: Sequence[str]) -> None:
    TEXTOS_DIR.mkdir(parents=True, exist_ok=True)
    conteudo = "\n\n".join(
        f"===== PÁGINA {i} =====\n{texto}" for i, texto in enumerate(paginas, 1)
    )
    (TEXTOS_DIR / f"informativo-{publicacao.numero:03d}.txt").write_text(
        conteudo.rstrip() + "\n", encoding="utf-8"
    )


def escrever_fichas(julgados: Sequence[Julgado]) -> None:
    FICHAS_DIR.mkdir(parents=True, exist_ok=True)
    for j in julgados:
        (FICHAS_DIR / f"{j.id}.md").write_text(renderizar_ficha(j), encoding="utf-8")


def escrever_indices(publicacoes: Sequence[Publicacao], julgados: Sequence[Julgado]) -> None:
    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    manifesto = []
    for p in publicacoes:
        pdf = ORIGINAIS_DIR / nome_pdf(p)
        manifesto.append(
            {
                "informativo": p.numero,
                "title": p.titulo,
                "publication_date": p.data_publicacao,
                "update_date": p.data_atualizacao,
                "listing_url": p.pagina_url,
                "pdf_url": p.pdf_url,
                "word_url": p.word_url,
                "source_path": caminho_relativo(pdf),
                "sha256": sha256_arquivo(pdf),
                "size_bytes": pdf.stat().st_size,
            }
        )
    (INDICES_DIR / "manifesto_informativos.jsonl").write_text(
        "".join(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n" for v in manifesto),
        encoding="utf-8",
    )
    (INDICES_DIR / "catalogo_julgados.jsonl").write_text(
        "".join(json.dumps(asdict(j), ensure_ascii=False, sort_keys=True) + "\n" for j in julgados),
        encoding="utf-8",
    )
    campos = [
        "id", "informativo", "data_publicacao", "acordao", "orgao_julgador",
        "classe_processual", "relator", "responsavel_citacao", "numero_item", "paginas", "regime_legal",
        "temas", "termos_selecao", "arquivo_original", "sha256", "pdf_url",
        "url_inteiro_teor", "ficha_path",
    ]
    with (INDICES_DIR / "catalogo_julgados.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=campos)
        writer.writeheader()
        for j in julgados:
            registro = asdict(j)
            for campo in ("paginas", "temas", "termos_selecao"):
                registro[campo] = " | ".join(map(str, registro[campo]))
            writer.writerow({campo: registro[campo] for campo in campos})


def escrever_readme(publicacoes: Sequence[Publicacao], julgados: Sequence[Julgado]) -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    conteudo = f'''---
tipo: jurisprudencia
hierarquia: persuasiva
tema: contratacao direta
fonte: Tribunal de Contas da União / Informativos de Licitações e Contratos
vigencia: vigente
atualizado_em: {ATUALIZADO_EM}
tags: [tcu, informativo-licitacoes-contratos, contratacao-direta, dispensa-de-licitacao]
---

# Corpus TCU — contratação direta e dispensa de licitação

Corpus derivado dos {len(publicacoes)} Informativos de Licitações e Contratos do TCU, números
{min(p.numero for p in publicacoes)} a {max(p.numero for p in publicacoes)}, com {len(julgados)} enunciados
selecionados por relação expressa com contratação direta, dispensa ou inexigibilidade de licitação.

## Escopo e método

- Fonte de descoberta: `{LISTAGEM_URL}`.
- Seleção conservadora aplicada ao **enunciado do sumário**, não à simples ocorrência incidental no histórico.
- Cada ficha conserva informativo, item, acórdão, colegiado, página, URL oficial, original e SHA-256.
- O link do inteiro teor só é registrado quando localizado nas anotações do PDF oficial.
- OCR não é usado porque os PDFs deste recorte contêm texto pesquisável.

## Limite jurídico essencial

O próprio TCU informa que os informativos contêm informações sintéticas, não constituem resumo oficial da
decisão e não representam necessariamente o posicionamento prevalecente do Tribunal. Por isso, todas as fichas
estão marcadas `verificar-inteiro-teor`; não se presume força vinculante nem aplicabilidade automática.

## Estrutura

- `fichas/`: uma ficha por acórdão selecionado.
- `texto_extraido/`: texto integral paginado dos informativos.
- `indices/manifesto_informativos.jsonl`: URLs, caminhos, tamanhos e hashes dos PDFs.
- `indices/catalogo_julgados.jsonl` e `.csv`: catálogo estruturado dos registros selecionados.
- `consolidacoes/MAPA_TEMATICO_CONTRATACAO_DIRETA.md`: navegação temática para cautelas e pesquisa.
'''
    (BASE_DIR / "README.md").write_text(conteudo, encoding="utf-8")


def escrever_mapa(julgados: Sequence[Julgado]) -> None:
    CONSOLIDACOES_DIR.mkdir(parents=True, exist_ok=True)
    por_tema: dict[str, list[Julgado]] = {}
    for j in julgados:
        for tema in j.temas or ["outros aspectos de contratação direta"]:
            por_tema.setdefault(tema, []).append(j)
    linhas = [
        "---",
        "tipo: jurisprudencia",
        "hierarquia: persuasiva",
        "tema: contratacao direta",
        "fonte: Tribunal de Contas da União / Informativos de Licitações e Contratos",
        "vigencia: vigente",
        f"atualizado_em: {ATUALIZADO_EM}",
        "tags: [tcu, mapa-tematico, contratacao-direta, dispensa-de-licitacao]",
        "---",
        "",
        "# Mapa temático — contratação direta nos informativos do TCU",
        "",
        "> Índice de localização. A ficha e o inteiro teor devem ser conferidos antes do uso jurídico.",
        "",
    ]
    for tema in sorted(por_tema):
        linhas.extend([f"## {tema}", ""])
        for j in sorted(por_tema[tema], key=lambda v: (v.informativo, v.acordao)):
            resumo = j.enunciado if len(j.enunciado) <= 300 else j.enunciado[:297].rstrip() + "..."
            linhas.append(
                f"- [Acórdão {j.acordao} {j.orgao_julgador}](../fichas/{j.id}.md) — "
                f"Informativo {j.informativo}, p. {paginas_texto(j.paginas)}; {resumo}"
            )
        linhas.append("")
    (CONSOLIDACOES_DIR / "MAPA_TEMATICO_CONTRATACAO_DIRETA.md").write_text(
        "\n".join(linhas).rstrip() + "\n", encoding="utf-8"
    )


def validar_resultado(publicacoes: Sequence[Publicacao], julgados: Sequence[Julgado]) -> list[str]:
    erros: list[str] = []
    ids: set[str] = set()
    for p in publicacoes:
        pdf = ORIGINAIS_DIR / nome_pdf(p)
        if not pdf.exists() or not pdf.read_bytes()[:4] == b"%PDF":
            erros.append(f"Original ausente ou inválido: {pdf}")
    for j in julgados:
        if j.id in ids:
            erros.append(f"ID duplicado: {j.id}")
        ids.add(j.id)
        if not j.paginas:
            erros.append(f"Página não identificada: {j.id}")
        if not j.termos_selecao:
            erros.append(f"Termo de seleção ausente: {j.id}")
        if not re.fullmatch(r"[\d.]+/\d{4}", j.acordao):
            erros.append(f"Acórdão inválido: {j.id}")
        ficha = RAIZ / j.ficha_path
        if not ficha.exists():
            erros.append(f"Ficha ausente: {j.ficha_path}")
        else:
            conteudo = ficha.read_text(encoding="utf-8")
            if j.sha256 not in conteudo or f"p. {j.paginas[0]}" not in conteudo:
                erros.append(f"Hash ou página ausente da ficha: {j.ficha_path}")
    return erros


def processar(inicio: int, fim: int, edicoes: set[int] | None, somente_descobrir: bool) -> int:
    publicacoes = descobrir_publicacoes(inicio, fim)
    if edicoes:
        faltantes = edicoes - {p.numero for p in publicacoes}
        if faltantes:
            raise RuntimeError("Edições não localizadas: " + ", ".join(map(str, sorted(faltantes))))
        publicacoes = [p for p in publicacoes if p.numero in edicoes]
    print(f"Publicações selecionadas: {len(publicacoes)} ({publicacoes[0].numero}-{publicacoes[-1].numero})")
    if somente_descobrir:
        for p in publicacoes:
            print(f"{p.numero}\t{p.data_publicacao}\t{p.pdf_url}")
        return 0

    julgados: list[Julgado] = []
    for p in publicacoes:
        pdf = baixar_pdf(p)
        reader, paginas = extrair_paginas(pdf)
        escrever_texto_extraido(p, paginas)
        encontrados = montar_julgados(p, pdf, reader, paginas)
        julgados.extend(encontrados)
        print(
            f"Informativo {p.numero}: {len(paginas)} página(s), {len(encontrados)} selecionado(s), "
            f"SHA-256 {sha256_arquivo(pdf)[:12]}..."
        )
    julgados.sort(key=lambda j: (j.informativo, j.numero_item, j.acordao))
    escrever_fichas(julgados)
    escrever_indices(publicacoes, julgados)
    escrever_readme(publicacoes, julgados)
    escrever_mapa(julgados)
    erros = validar_resultado(publicacoes, julgados)
    if erros:
        for erro in erros:
            print(f"ERRO: {erro}")
        return 1
    print(f"Validação concluída: {len(julgados)} julgado(s), sem erro mecânico.")
    return 0


def parse_edicoes(valor: str | None) -> set[int] | None:
    if not valor:
        return None
    return {int(v.strip()) for v in valor.split(",") if v.strip()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inicio", type=int, default=INICIO_PADRAO)
    parser.add_argument("--fim", type=int, default=FIM_PADRAO)
    parser.add_argument("--edicoes", help="Lista separada por vírgulas")
    parser.add_argument("--somente-descobrir", action="store_true")
    args = parser.parse_args(argv)
    if args.inicio > args.fim:
        parser.error("--inicio não pode ser maior que --fim")
    try:
        return processar(args.inicio, args.fim, parse_edicoes(args.edicoes), args.somente_descobrir)
    except (RuntimeError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
