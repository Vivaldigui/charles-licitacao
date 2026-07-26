#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classificar_documento.py — o que é este arquivo, de quem é e de que processo é.

Alimenta a importação de documentos externos (itens 17 a 21). Trabalha com o
nome do arquivo e, quando existe extrator, com o texto — e é explícito sobre a
diferença: PDF sem OCR nesta base não tem texto legível, e classificar um PDF
só pelo nome é indício, não conclusão.

Três recusas deliberadas:

* **não inventa metadado** (item 19). Origem, CNPJ e data que não aparecem no
  documento saem como `None`, com pendência anotada;
* **não conclui pertencimento ao processo pelo nome da pasta** (item 21).
  Número de processo diferente citado no texto vira alerta e quarentena;
* **não decide sozinha quando está em dúvida**. Confiança baixa devolve
  categoria `outros` e o motivo da dúvida, para o humano resolver.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from hashes import ConteudoIndisponivel, extrair_texto, sha256_arquivo  # noqa: E402
from manifesto import numeros_de_processo  # noqa: E402
from manifesto import preparar_console  # noqa: E402
from nomes_arquivos import CATEGORIAS_EXTERNAS, remover_acentos  # noqa: E402

#: (categoria, tipo, padrão). A ordem importa: o primeiro que casar vence, e os
#: padrões mais específicos vêm antes.
REGRAS: tuple[tuple[str, str, str], ...] = (
    ("comprovantes", "nota_fiscal", r"NOTA[_ ]?FISCAL|\bNFE?\b|\bDANFE\b"),
    ("comprovantes", "comprovante", r"COMPROVANTE|RECIBO|EMPENHO|ORDEM[_ ]?BANCARIA"),
    ("habilitacao", "certidao", r"CERTIDAO|\bCND\b|\bCNDT\b|\bFGTS\b|\bCRF\b|"
                                r"REGULARIDADE|TRABALHISTA|FALENCIA|CONCORDATA"),
    ("habilitacao", "ato_constitutivo", r"CONTRATO[_ ]?SOCIAL|ESTATUTO|"
                                        r"REQUERIMENTO[_ ]?DE[_ ]?EMPRESARIO|\bCNPJ\b"),
    ("habilitacao", "declaracao", r"DECLARACAO"),
    ("cotacoes_e_propostas", "proposta", r"PROPOSTA"),
    ("cotacoes_e_propostas", "cotacao", r"COTACAO|ORCAMENTO|\bORCTO\b"),
    ("pareceres", "parecer", r"PARECER|NOTA[_ ]?JURIDICA|NOTA[_ ]?TECNICA"),
    ("emails_e_comunicacoes", "email", r"\bE?[_ ]?MAIL\b|MENSAGEM|WHATSAPP|RESPOSTA"),
    ("solicitacoes", "solicitacao", r"SOLICITACAO|REQUISICAO|PEDIDO"),
    ("solicitacoes", "oficio", r"\bOFICIO\b|MEMORANDO|\bCI\b"),
    ("referencias_tecnicas", "referencia_tecnica",
     r"CATALOGO|FICHA[_ ]?TECNICA|MANUAL|ESPECIFICACAO|\bPNCP\b|EDITAL|"
     r"TERMO[_ ]?DE[_ ]?REFERENCIA"),
)

EXTENSOES_EMAIL = {".eml", ".msg"}
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

RE_CNPJ = re.compile(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b")
RE_DATA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RE_DATA_BR = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
RE_DATA_EXTENSO = re.compile(
    r"\b(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})\b", re.IGNORECASE
)
MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5,
    "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}
RE_RAZAO_SOCIAL = re.compile(
    r"\b([A-ZÀ-Ú][A-ZÀ-Ú0-9&\.\- ]{3,60}?\s"
    r"(?:LTDA|EIRELI|ME|EPP|S\.?A\.?|SOCIEDADE|COM[EÉ]RCIO|IND[UÚ]STRIA|SERVI[ÇC]OS))\b"
)


@dataclass
class Classificacao:
    """O que se conseguiu afirmar sobre o arquivo — e com que confiança."""

    arquivo: str
    categoria: str = "outros"
    tipo: Optional[str] = None
    origem: Optional[str] = None
    cnpj: Optional[str] = None
    data_documento: Optional[str] = None
    processos_citados: list[str] = field(default_factory=list)
    confianca: str = "baixa"  # alta | media | baixa
    fonte_da_analise: str = "nome do arquivo"
    texto_legivel: bool = False
    pendencias: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)

    def como_dicionario(self) -> dict[str, Any]:
        return asdict(self)


def _texto_do_arquivo(caminho: Path) -> tuple[str, bool]:
    try:
        return " ".join(extrair_texto(caminho)), True
    except (ConteudoIndisponivel, OSError, ValueError):
        return "", False


def _data_encontrada(texto: str) -> Optional[str]:
    achado = RE_DATA_ISO.search(texto)
    if achado:
        return achado.group(0)
    achado = RE_DATA_BR.search(texto)
    if achado:
        dia, mes, ano = achado.groups()
        return f"{ano}-{mes}-{dia}"
    achado = RE_DATA_EXTENSO.search(texto)
    if achado:
        dia, mes_nome, ano = achado.groups()
        mes = MESES.get(remover_acentos(mes_nome.lower()))
        if mes:
            return f"{ano}-{mes:02d}-{int(dia):02d}"
    return None


def classificar(
    caminho: Path | str,
    *,
    numero_processo: Optional[str] = None,
    categoria_informada: Optional[str] = None,
    origem_informada: Optional[str] = None,
) -> Classificacao:
    """
    Classifica um documento externo. O que o usuário informa prevalece sobre a
    heurística — quem viu o documento chegar sabe mais que um regex.
    """
    caminho = Path(caminho)
    resultado = Classificacao(arquivo=str(caminho))

    nome_normalizado = remover_acentos(caminho.stem).upper()
    texto, legivel = _texto_do_arquivo(caminho)
    resultado.texto_legivel = legivel
    corpus_nome = re.sub(r"[^A-Z0-9]+", " ", nome_normalizado)
    corpus_texto = remover_acentos(texto).upper()

    # -- categoria e tipo -------------------------------------------------- #
    if categoria_informada:
        chave = categoria_informada.strip().lower()
        chave = {"proposta": "cotacoes_e_propostas",
                 "cotacao": "cotacoes_e_propostas",
                 "certidao": "habilitacao",
                 "parecer": "pareceres",
                 "email": "emails_e_comunicacoes",
                 "nota_fiscal": "comprovantes"}.get(chave, chave)
        if chave not in CATEGORIAS_EXTERNAS:
            raise ValueError(
                f"Categoria desconhecida: {categoria_informada}. "
                f"Previstas: {', '.join(CATEGORIAS_EXTERNAS)}."
            )
        resultado.categoria = chave
        resultado.tipo = categoria_informada.strip().lower()
        resultado.confianca = "alta"
        resultado.fonte_da_analise = "informada pelo usuário"
    else:
        for categoria, tipo, padrao in REGRAS:
            if re.search(padrao, corpus_nome):
                resultado.categoria, resultado.tipo = categoria, tipo
                resultado.confianca = "media"
                resultado.fonte_da_analise = "nome do arquivo"
                break
        else:
            if caminho.suffix.lower() in EXTENSOES_EMAIL:
                resultado.categoria, resultado.tipo = "emails_e_comunicacoes", "email"
                resultado.confianca = "media"
                resultado.fonte_da_analise = "extensão do arquivo"
            elif legivel:
                for categoria, tipo, padrao in REGRAS:
                    if re.search(padrao, corpus_texto[:4000]):
                        resultado.categoria, resultado.tipo = categoria, tipo
                        resultado.confianca = "media"
                        resultado.fonte_da_analise = "texto do documento"
                        break

        # Nome e texto concordando: é o mais perto de "alta" que a heurística chega.
        padrao_do_tipo = {tipo: padrao for _, tipo, padrao in REGRAS}.get(resultado.tipo or "")
        if legivel and padrao_do_tipo and re.search(padrao_do_tipo, corpus_texto[:4000]):
            resultado.confianca = "alta"
            resultado.fonte_da_analise = "nome e texto do documento"

    if resultado.tipo is None:
        resultado.pendencias.append("tipo do documento não identificado")

    # -- origem, CNPJ e data ----------------------------------------------- #
    if origem_informada:
        resultado.origem = origem_informada.strip()
    elif legivel:
        achado = RE_RAZAO_SOCIAL.search(texto)
        if achado:
            resultado.origem = re.sub(r"\s+", " ", achado.group(1)).strip()
    if not resultado.origem:
        resultado.pendencias.append("origem (fornecedor ou órgão) não identificada")

    if legivel:
        cnpj = RE_CNPJ.search(texto)
        if cnpj:
            resultado.cnpj = cnpj.group(1)
        resultado.data_documento = _data_encontrada(texto)
    if not resultado.data_documento:
        resultado.data_documento = _data_encontrada(caminho.name)
    if not resultado.data_documento:
        resultado.pendencias.append("data do documento não identificada")

    # -- pertencimento ao processo (item 21) -------------------------------- #
    citados = numeros_de_processo(f"{caminho.name} {texto}")
    resultado.processos_citados = sorted(citados)
    if numero_processo:
        esperados = numeros_de_processo(numero_processo)
        if citados and esperados and not (citados & esperados):
            resultado.alertas.append(
                f"o documento cita processo(s) {', '.join(sorted(citados))}, e este "
                f"processo é {', '.join(sorted(esperados))}: pode pertencer a outro "
                f"processo — permanece em quarentena até confirmação humana"
            )

    if not legivel:
        resultado.pendencias.append(
            f"texto não extraível ({caminho.suffix or 'sem extensão'}): classificação "
            f"apoiada apenas no nome; conferência humana necessária"
        )
        if resultado.confianca == "alta":
            resultado.confianca = "media"

    if caminho.suffix.lower() in EXTENSOES_IMAGEM:
        resultado.pendencias.append(
            "documento digitalizado: depende de OCR ou conferência manual"
        )
    return resultado


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Classifica um documento externo sem movê-lo."
    )
    analisador.add_argument("--arquivo", required=True)
    analisador.add_argument("--numero-processo")
    analisador.add_argument("--categoria")
    analisador.add_argument("--origem")
    analisador.add_argument("--json", action="store_true")
    argumentos = analisador.parse_args(argv)

    caminho = Path(argumentos.arquivo)
    if not caminho.is_file():
        print(f"ERRO: arquivo não encontrado: {caminho}", file=sys.stderr)
        return 1

    resultado = classificar(
        caminho,
        numero_processo=argumentos.numero_processo,
        categoria_informada=argumentos.categoria,
        origem_informada=argumentos.origem,
    )
    if argumentos.json:
        dados = resultado.como_dicionario()
        dados["hash_sha256"] = sha256_arquivo(caminho)
        dados["analisado_em"] = datetime.now().isoformat(timespec="seconds")
        print(json.dumps(dados, ensure_ascii=False, indent=2))
        return 0

    print(f"arquivo:    {caminho.name}")
    print(f"categoria:  {resultado.categoria} ({resultado.confianca}, {resultado.fonte_da_analise})")
    print(f"tipo:       {resultado.tipo or '—'}")
    print(f"origem:     {resultado.origem or '—'}")
    print(f"CNPJ:       {resultado.cnpj or '—'}")
    print(f"data:       {resultado.data_documento or '—'}")
    for item in resultado.pendencias:
        print(f"  [PENDÊNCIA] {item}")
    for item in resultado.alertas:
        print(f"  [ALERTA] {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
