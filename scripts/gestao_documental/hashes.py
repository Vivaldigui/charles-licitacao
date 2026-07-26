#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hashes.py — identidade binária e identidade de conteúdo dos documentos.

Duas perguntas diferentes, respondidas por duas assinaturas diferentes:

* **hash binário** (SHA-256 dos bytes) — identifica o ARQUIVO. É o que prova
  que um documento assinado não foi trocado e o que detecta duplicata exata de
  documento externo (itens 17 e 20 do escopo).
* **hash de conteúdo** — identifica o TEXTO do documento, já normalizado e
  incluindo tabelas, cabeçalho e rodapé. É o que responde ao item 15: "não
  criar nova versão sem alteração real". Salvar de novo um DOCX muda os bytes
  (data de modificação interna, ordem do ZIP) sem mudar uma vírgula do texto —
  por isso o hash binário sozinho criaria versão fantasma.

Só biblioteca padrão: um DOCX é um ZIP com XML, e ler o texto dele não exige
`python-docx`. Formatos sem extrator (PDF, imagem, planilha) caem no hash
binário e são declarados como tal — este módulo nunca finge ter lido o que não
leu.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))

from nomes_arquivos import caminho_os  # noqa: E402

BLOCO = 1024 * 1024

# Partes de um DOCX que carregam conteúdo visível ao leitor.
RE_PARTE_CONTEUDO = re.compile(
    r"^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$"
)
RE_TEXTO_XML = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.DOTALL)
RE_QUEBRA_XML = re.compile(r"<w:(?:p|br|tab|tr)\b[^>]*/?>")
RE_TAG = re.compile(r"<[^>]+>")

# Marcadores de campo pendente (itens 16 e 34 do escopo).
RE_PREENCHER = re.compile(r"\[\s*PREENCHER\b[^\]]*\]", re.IGNORECASE)
RE_CHAVES = re.compile(r"\{\{\s*[^}]{1,120}\}\}")


class ConteudoIndisponivel(RuntimeError):
    """O formato não tem extrator de texto nesta base."""


# --------------------------------------------------------------------------- #
# Hash binário
# --------------------------------------------------------------------------- #

def sha256_arquivo(caminho: Path | str) -> str:
    digest = hashlib.sha256()
    with open(caminho_os(caminho), "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(BLOCO), b""):
            digest.update(bloco)
    return digest.hexdigest()


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_texto(linhas: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for linha in linhas:
        digest.update(linha.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# Texto e conteúdo
# --------------------------------------------------------------------------- #

def normalizar_texto(texto: str) -> str:
    """NFC, espaços colapsados, sem espaço nas pontas."""
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace("\xa0", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", texto).strip()


def _desescapar(texto: str) -> str:
    for entidade, caractere in (
        ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
        ("&apos;", "'"), ("&amp;", "&"),
    ):
        texto = texto.replace(entidade, caractere)
    return texto


def texto_docx(caminho: Path | str) -> list[str]:
    """
    Linhas de texto de um DOCX: corpo, tabelas, cabeçalhos e rodapés.

    Cada parte entra prefixada pelo nome (`word/document.xml|...`) para que
    mover um parágrafo do corpo para o rodapé apareça como diferença.
    """
    linhas: list[str] = []
    caminho = caminho_os(caminho)
    if not zipfile.is_zipfile(caminho):
        # Extensão .docx não faz um DOCX: arquivo renomeado, corrompido ou .doc
        # antigo cai aqui, e é melhor dizer isso do que devolver texto vazio.
        raise ConteudoIndisponivel(
            f"{Path(caminho).name} tem extensão de DOCX, mas não é um pacote OOXML "
            f"válido; a comparação usa o hash binário."
        )
    with zipfile.ZipFile(caminho, "r") as pacote:
        for nome in sorted(pacote.namelist()):
            if not RE_PARTE_CONTEUDO.match(nome):
                continue
            xml = pacote.read(nome).decode("utf-8", "ignore")
            # Marca os limites de parágrafo/célula antes de remover as tags.
            xml = RE_QUEBRA_XML.sub("\n", xml)
            bruto = "\n".join(_desescapar(t) for t in RE_TEXTO_XML.findall(xml))
            if not bruto:
                bruto = RE_TAG.sub("", xml)
            for linha in bruto.splitlines():
                limpo = normalizar_texto(RE_TAG.sub("", linha))
                if limpo:
                    linhas.append(f"{nome}|{limpo}")
    return linhas


def texto_simples(caminho: Path | str) -> list[str]:
    with open(caminho_os(caminho), encoding="utf-8", errors="ignore") as arquivo:
        conteudo = arquivo.read()
    return [normalizar_texto(l) for l in conteudo.splitlines() if l.strip()]


EXTENSOES_COM_TEXTO = {".docx", ".docm", ".txt", ".md", ".json", ".csv", ".jsonl"}


def extrair_texto(caminho: Path | str) -> list[str]:
    """
    Texto normalizado do arquivo. Levanta `ConteudoIndisponivel` sem extrator.

    PDF e imagem caem aqui de propósito: sem OCR nem parser na base, afirmar o
    conteúdo deles seria invenção.
    """
    caminho = Path(caminho)
    extensao = caminho.suffix.lower()
    if extensao in (".docx", ".docm"):
        return texto_docx(caminho)
    if extensao in EXTENSOES_COM_TEXTO:
        return texto_simples(caminho)
    raise ConteudoIndisponivel(
        f"Sem extrator de texto para {extensao or 'arquivo sem extensão'} "
        f"({caminho.name}); a comparação usa o hash binário."
    )


def hash_conteudo(caminho: Path | str) -> Optional[str]:
    """Assinatura do texto normalizado, ou None quando o formato não permite."""
    try:
        return sha256_texto(extrair_texto(caminho))
    except ConteudoIndisponivel:
        return None


def campos_pendentes(caminho: Path | str) -> list[str]:
    """
    Marcadores `[PREENCHER: ...]` e `{{CAMPO}}` ainda presentes no documento.

    Campo pendente impede promoção e impede "pronto para assinatura"
    (itens 16 e 32 do escopo). Formato sem extrator devolve lista vazia — e
    quem chama precisa dizer que a verificação não foi executada.
    """
    try:
        linhas = extrair_texto(caminho)
    except ConteudoIndisponivel:
        return []
    achados: list[str] = []
    for linha in linhas:
        achados.extend(m.group(0) for m in RE_PREENCHER.finditer(linha))
        achados.extend(m.group(0) for m in RE_CHAVES.finditer(linha))
    return achados


def verificacao_de_pendencias_possivel(caminho: Path | str) -> bool:
    return Path(caminho).suffix.lower() in EXTENSOES_COM_TEXTO


# --------------------------------------------------------------------------- #
# Comparação
# --------------------------------------------------------------------------- #

@dataclass
class Comparacao:
    """Resultado da comparação entre o candidato e o documento atual."""

    identico_binario: bool
    identico_conteudo: Optional[bool]  # None = conteúdo não comparável
    hash_novo: str = ""
    hash_atual: str = ""
    conteudo_novo: Optional[str] = None
    conteudo_atual: Optional[str] = None
    observacoes: list[str] = field(default_factory=list)

    @property
    def houve_alteracao(self) -> bool:
        """
        Há alteração real a versionar?

        Regra do item 15: conteúdo idêntico não gera versão nova, ainda que os
        bytes mudem (metadados internos do DOCX). Sem extrator de texto, a
        decisão recai sobre os bytes — e a observação registra isso.
        """
        if self.identico_conteudo is not None:
            return not self.identico_conteudo
        return not self.identico_binario

    @property
    def resumo(self) -> str:
        if not self.houve_alteracao:
            if self.identico_binario:
                return "arquivo idêntico (bytes e conteúdo)"
            return "conteúdo idêntico; mudança apenas nos metadados internos"
        if self.identico_conteudo is None:
            return "alteração detectada pelo hash binário (conteúdo não comparável)"
        return "alteração real de conteúdo"


def comparar_documentos(novo: Path | str, atual: Path | str) -> Comparacao:
    """Compara bytes e conteúdo textual normalizado (item 15 do escopo)."""
    novo, atual = Path(novo), Path(atual)
    hash_novo = sha256_arquivo(novo)
    hash_atual = sha256_arquivo(atual)
    if hash_novo == hash_atual:
        return Comparacao(
            identico_binario=True,
            identico_conteudo=True,
            hash_novo=hash_novo,
            hash_atual=hash_atual,
            observacoes=["hashes binários iguais"],
        )

    observacoes: list[str] = []
    conteudo_novo = hash_conteudo(novo)
    conteudo_atual = hash_conteudo(atual)
    if conteudo_novo is None or conteudo_atual is None:
        observacoes.append(
            "conteúdo textual não comparável neste formato; comparação binária"
        )
        identico_conteudo = None
    else:
        identico_conteudo = conteudo_novo == conteudo_atual
        if identico_conteudo:
            observacoes.append(
                "texto, tabelas, cabeçalho e rodapé idênticos; diferem apenas "
                "os metadados internos do pacote"
            )
    return Comparacao(
        identico_binario=False,
        identico_conteudo=identico_conteudo,
        hash_novo=hash_novo,
        hash_atual=hash_atual,
        conteudo_novo=conteudo_novo,
        conteudo_atual=conteudo_atual,
        observacoes=observacoes,
    )


def semelhanca(a: Path | str, b: Path | str) -> Optional[float]:
    """
    Proximidade textual entre dois arquivos (0.0 a 1.0), ou None sem extrator.

    Serve ao item 20: arquivos PARECIDOS, mas não idênticos, ficam os dois e
    vão para validação humana. Nunca decide exclusão.
    """
    import difflib

    try:
        texto_a = extrair_texto(a)
        texto_b = extrair_texto(b)
    except ConteudoIndisponivel:
        return None
    if not texto_a and not texto_b:
        return 1.0
    return difflib.SequenceMatcher(None, texto_a, texto_b).ratio()
