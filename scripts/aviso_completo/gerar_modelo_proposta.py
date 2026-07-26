#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_modelo_proposta.py — Anexo do modelo de proposta e da declaração conjunta.

O modelo de proposta é preenchido a partir do Termo de Referência: item,
descrição, unidade e quantidade saem do quadro do TR e só de lá.

Regra que organiza todo o módulo: existem dois domínios de campo.

    domínio da Administração — processo, dispensa, objeto, itens, quantidades.
        São preenchidos aqui, porque a Câmara já os definiu no TR.

    domínio do proponente — razão social, CNPJ, marca, preços, local, data,
        assinatura. Ficam EM BRANCO. Preencher preço em nome do fornecedor
        descaracterizaria a proposta.

Campo do proponente sai como célula vazia, não como `{{MARCADOR}}` ou
`[PREENCHER]`: marcador remanescente é defeito de montagem e bloqueia a
publicação; célula vazia é o espaço legítimo que o fornecedor preenche.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

from extrair_dados_tr import DadosTR, ItemTR
from ocorrencias import Registro
from util_ooxml import (
    CAMPO_RE,
    SUBLINHADO_RE,
    exigir_python_docx,
    iter_paragrafos_corpo,
    iter_paragrafos_tabela,
    substituir_marcadores_paragrafo,
    texto_paragrafo,
)

ETAPA = "modelo de proposta"

# Campos que o fornecedor preenche — sempre esvaziados na montagem.
CAMPOS_DO_PROPONENTE = frozenset({
    "RAZAO_SOCIAL", "CNPJ", "ENDERECO", "CEP", "EMAIL", "TELEFONE",
    "DADOS_BANCARIOS", "DADOS_RESPONSAVEL", "NOME_REPRESENTANTE", "CPF", "RG",
    "MARCA", "MODELO", "VALOR_UNITARIO", "VALOR_TOTAL_ITEM",
    "VALOR_TOTAL_PROPOSTA", "VALOR_TOTAL_EXTENSO", "LOCAL", "DATA",
})

# Marcadores da linha-modelo do quadro de itens.
CAMPOS_DO_ITEM = ("ITEM", "DESCRICAO_ITEM", "UNIDADE", "QUANTIDADE")

PREENCHER_LITERAL = "[PREENCHER]"


def _largura_util_twips(documento) -> int:
    """Largura entre as margens da primeira seção, em twips."""
    secao = documento.sections[0]
    return int((secao.page_width - secao.left_margin - secao.right_margin) / 635)


def _quadro_de_itens(documento):
    """A tabela cuja linha-modelo carrega os marcadores de item."""
    for tabela in documento.tables:
        for linha in tabela.rows:
            texto = " ".join(celula.text for celula in linha.cells)
            if all(f"{{{{{campo}}}}}" in texto for campo in ("ITEM", "DESCRICAO_ITEM")):
                return tabela, linha
    return None, None


def _replicar_linhas(tabela, modelo, quantidade: int) -> list:
    """
    Deixa o quadro com uma linha por item do TR.

    A linha extra é cópia profunda do XML da linha-modelo: bordas, sombreamento,
    largura de coluna e propriedades de quebra vêm junto. Recriar a linha com a
    API de alto nível produziria linhas sem a formatação do quadro.
    """
    linhas = [modelo]
    referencia = modelo._tr
    for _ in range(max(0, quantidade - 1)):
        nova = copy.deepcopy(modelo._tr)
        referencia.addnext(nova)
        referencia = nova
    if quantidade > 1:
        indice = list(tabela._tbl).index(modelo._tr)
        from docx.table import _Row
        linhas = [
            _Row(tr, tabela)
            for tr in list(tabela._tbl)[indice:indice + quantidade]
        ]
    return linhas


# Proporção das colunas do quadro de itens. A minuta foi desenhada para uma
# descrição curta; o TR traz a especificação técnica inteira na mesma célula.
# Com as colunas repartidas por igual, a descrição vira uma coluna de duas
# palavras por linha e o item ocupa três páginas. As proporções abaixo são
# formatação do anexo gerado — a minuta não é alterada.
PROPORCAO_COLUNAS = {
    "ITEM": 0.06,
    "DESCRIÇÃO": 0.44,
    "UND": 0.10,
    "QNTD": 0.08,
    "MARCA": 0.10,
    "VALOR UNITÁRIO": 0.11,
    "VALOR TOTAL": 0.11,
}


def _ajustar_larguras(tabela, largura_total_twips: int) -> bool:
    """Redistribui as colunas do quadro de itens conforme o conteúdo real."""
    from docx.shared import Twips

    cabecalhos = [c.text.strip().upper() for c in tabela.rows[0].cells]
    proporcoes = [PROPORCAO_COLUNAS.get(nome) for nome in cabecalhos]
    if any(p is None for p in proporcoes):
        return False

    larguras = [int(largura_total_twips * p) for p in proporcoes]
    tabela.autofit = False
    for indice, largura in enumerate(larguras):
        if indice < len(tabela.columns):
            tabela.columns[indice].width = Twips(largura)
    for linha in tabela.rows:
        for indice, celula in enumerate(linha.cells):
            if indice < len(larguras):
                celula.width = Twips(larguras[indice])
    return True


def _manter_cabecalho_com_primeira_linha(tabela) -> None:
    """
    Impede que a linha de cabeçalho fique sozinha no fim de uma página.

    Sem isso, um item com especificação longa empurra a primeira linha de dados
    para a página seguinte e deixa o cabeçalho do quadro isolado, numa folha em
    que não há mais nada.
    """
    for celula in tabela.rows[0].cells:
        for paragrafo in celula.paragraphs:
            paragrafo.paragraph_format.keep_with_next = True


def _preencher_linha(linha, item: ItemTR) -> None:
    """Preenche uma linha do quadro; campos de preço e marca saem vazios."""
    valores = {
        "ITEM": item.numero,
        "DESCRICAO_ITEM": item.descricao,
        "UNIDADE": item.unidade,
        "QUANTIDADE": item.quantidade,
    }

    def resolver(nome: str) -> Optional[str]:
        if nome in valores:
            return valores[nome]
        if nome in CAMPOS_DO_PROPONENTE:
            return ""
        return None

    for celula in linha.cells:
        for paragrafo in celula.paragraphs:
            substituir_marcadores_paragrafo(paragrafo, resolver, CAMPO_RE)


# Lacuna que o fornecedor preenche à mão ou digitando. Em texto corrido a régua
# é necessária — "A empresa , inscrita no CNPJ sob o nº ," seria um documento
# malfeito. Dentro de tabela a célula fica vazia, porque a própria célula já
# delimita o espaço e a régua estouraria a largura da coluna.
LACUNA = "_" * 20


def _esvaziar_campos_do_proponente(documento) -> tuple[list[str], list[str]]:
    """
    Converte os campos do proponente em espaço de preenchimento.

    Devolve (nomes dos campos, linhas resultantes). As linhas voltam porque a
    validação final precisa saber quais lacunas são legítimas: sublinhado é, em
    regra, campo por preencher e bloqueia a publicação — exceto nestas, que
    existem justamente para o fornecedor preencher.
    """
    esvaziados: list[str] = []
    linhas: list[str] = []

    def resolver_texto(nome: str) -> Optional[str]:
        if nome in CAMPOS_DO_PROPONENTE:
            esvaziados.append(nome)
            return LACUNA
        return None

    def resolver_celula(nome: str) -> Optional[str]:
        if nome in CAMPOS_DO_PROPONENTE:
            esvaziados.append(nome)
            return ""
        return None

    for paragrafo in documento.paragraphs:
        resultado = substituir_marcadores_paragrafo(paragrafo, resolver_texto, CAMPO_RE)
        if resultado.preenchidos:
            linhas.append(texto_paragrafo(paragrafo).strip())
    for tabela in documento.tables:
        for paragrafo in iter_paragrafos_tabela(tabela):
            substituir_marcadores_paragrafo(paragrafo, resolver_celula, CAMPO_RE)
    return sorted(set(esvaziados)), linhas


def _esvaziar_preencher_literal(documento) -> int:
    """
    Troca `[PREENCHER]` por célula vazia nas tabelas de dados do fornecedor.

    Na minuta da proposta, `[PREENCHER]` marca o que o fornecedor informa. Se o
    literal permanecesse, a validação final o leria — corretamente — como campo
    pendente e bloquearia a publicação de um documento que está certo.
    """
    trocados = 0
    for tabela in documento.tables:
        for paragrafo in iter_paragrafos_tabela(tabela):
            texto = texto_paragrafo(paragrafo)
            if PREENCHER_LITERAL not in texto.upper():
                continue
            for elemento in paragrafo._p.iter(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                if PREENCHER_LITERAL in (elemento.text or "").upper():
                    elemento.text = ""
                    trocados += 1
    return trocados


def gerar(minuta: Path, destino: Path, dados_administracao: dict[str, str],
          dados_tr: Optional[DadosTR], registro: Registro) -> tuple[Path, list[str]]:
    """
    Gera o Anexo do modelo de proposta a partir da minuta oficial.

    Devolve o caminho e as linhas com lacunas do proponente, que a validação
    final precisa reconhecer como legítimas.
    """
    exigir_python_docx()
    from docx import Document

    minuta, destino = Path(minuta), Path(destino)
    documento = Document(str(minuta))

    tabela, modelo = _quadro_de_itens(documento)
    itens = list(dados_tr.itens) if dados_tr else []
    if tabela is None or modelo is None:
        registro.alerta(
            ETAPA,
            "A minuta do modelo de proposta não tem quadro de itens com "
            "marcadores. O anexo foi gerado sem replicar os itens do TR.",
            origem=minuta.name,
        )
    elif not itens:
        registro.bloqueante(
            ETAPA,
            "Não há itens extraídos do TR para compor o modelo de proposta. O "
            "modelo não pode ser publicado com o quadro em branco.",
            origem=minuta.name,
        )
    else:
        linhas = _replicar_linhas(tabela, modelo, len(itens))
        for linha, item in zip(linhas, itens):
            _preencher_linha(linha, item)
        if _ajustar_larguras(tabela, _largura_util_twips(documento)):
            registro.informacao(
                ETAPA,
                "Colunas do quadro de itens redistribuídas para acomodar a "
                "especificação vinda do TR (formatação do anexo gerado; a "
                "minuta não foi alterada).",
                origem=minuta.name,
            )
        _manter_cabecalho_com_primeira_linha(tabela)
        registro.informacao(
            ETAPA,
            f"Quadro do modelo de proposta gerado com {len(itens)} item(ns) do TR, "
            "com marca e preços reservados ao proponente.",
            origem=minuta.name,
        )

    preenchidos: list[str] = []

    def resolver(nome: str) -> Optional[str]:
        if nome in dados_administracao:
            preenchidos.append(nome)
            return dados_administracao[nome]
        return None

    for paragrafo in iter_paragrafos_corpo(documento):
        substituir_marcadores_paragrafo(paragrafo, resolver, CAMPO_RE)

    esvaziados, lacunas = _esvaziar_campos_do_proponente(documento)
    literais = _esvaziar_preencher_literal(documento)

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(destino))

    registro.informacao(
        ETAPA,
        f"Campos da Administração preenchidos: {', '.join(sorted(set(preenchidos))) or 'nenhum'}. "
        f"Campos reservados ao proponente: {', '.join(esvaziados) or 'nenhum'}"
        + (f"; {literais} campo(s) '[PREENCHER]' convertido(s) em espaço do "
           "fornecedor." if literais else "."),
        origem=destino.name,
    )
    return destino, lacunas


def gerar_declaracao(minuta: Path, destino: Path,
                     dados_administracao: dict[str, str],
                     registro: Registro) -> tuple[Path, list[str]]:
    """
    Gera a declaração conjunta a partir da minuta oficial da Câmara.

    A declaração não é redigida aqui: o texto é o da minuta aprovada, e a
    montagem só identifica o processo e o aviso. Acrescentar declaração que a
    minuta não tem — ainda que usual em outro órgão — é proibido.
    """
    exigir_python_docx()
    from docx import Document

    minuta, destino = Path(minuta), Path(destino)
    documento = Document(str(minuta))

    preenchidos: list[str] = []

    def resolver(nome: str) -> Optional[str]:
        if nome in dados_administracao:
            preenchidos.append(nome)
            return dados_administracao[nome]
        return None

    for paragrafo in iter_paragrafos_corpo(documento):
        substituir_marcadores_paragrafo(paragrafo, resolver, CAMPO_RE)

    esvaziados, lacunas = _esvaziar_campos_do_proponente(documento)
    _esvaziar_preencher_literal(documento)

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(destino))
    registro.informacao(
        ETAPA,
        f"Declaração conjunta gerada da minuta oficial {minuta.name}; campos "
        f"reservados ao declarante: {', '.join(esvaziados) or 'nenhum'}.",
        origem=destino.name,
    )
    return destino, lacunas


def reservar_campos_restantes(documento) -> tuple[list[str], list[str]]:
    """
    Esvazia TODO marcador remanescente, devolvendo os nomes reservados.

    Usado na minuta de contrato anexa ao aviso: nela sobram, por natureza, os
    dados que só existem depois do julgamento — razão social da contratada,
    CNPJ, número e data do contrato. Anexar a minuta com esses campos em branco
    é o correto; anexá-la com `{{RAZAO_SOCIAL}}` à mostra é defeito de montagem.
    """
    reservados: list[str] = []
    linhas: list[str] = []

    def resolver_texto(nome: str) -> Optional[str]:
        reservados.append(nome)
        return LACUNA

    def resolver_celula(nome: str) -> Optional[str]:
        reservados.append(nome)
        return ""

    for paragrafo in documento.paragraphs:
        resultado = substituir_marcadores_paragrafo(paragrafo, resolver_texto, CAMPO_RE)
        if resultado.preenchidos:
            linhas.append(texto_paragrafo(paragrafo).strip())
    for tabela in documento.tables:
        for paragrafo in iter_paragrafos_tabela(tabela):
            substituir_marcadores_paragrafo(paragrafo, resolver_celula, CAMPO_RE)
    return sorted(set(reservados)), linhas


def gerar_minuta_contrato(minuta: Path, destino: Path,
                          dados_administracao: dict[str, str],
                          registro: Registro) -> tuple[Path, list[str]]:
    """
    Prepara a minuta de contrato oficial para anexação, sem alterar cláusulas.

    Só são preenchidos os dados que o processo já definiu. Nenhuma cláusula é
    criada, removida ou reescrita: a minuta anexa é a minuta oficial da Câmara.
    """
    exigir_python_docx()
    from docx import Document

    minuta, destino = Path(minuta), Path(destino)
    documento = Document(str(minuta))

    preenchidos: list[str] = []

    def resolver(nome: str) -> Optional[str]:
        if nome in dados_administracao:
            preenchidos.append(nome)
            return dados_administracao[nome]
        return None

    for paragrafo in iter_paragrafos_corpo(documento):
        substituir_marcadores_paragrafo(paragrafo, resolver, CAMPO_RE)

    reservados, lacunas = reservar_campos_restantes(documento)

    # Lacunas que já vêm na minuta oficial ("CONTRATO Nº ___"). Elas só se
    # completam depois do julgamento, então não são defeito de montagem — mas
    # também não podem passar em silêncio, porque impedem dar o documento por
    # pronto para assinatura.
    preexistentes = [
        texto_paragrafo(paragrafo).strip()
        for paragrafo in iter_paragrafos_corpo(documento)
        if SUBLINHADO_RE.search(texto_paragrafo(paragrafo))
    ]
    lacunas += preexistentes
    if preexistentes:
        registro.pendencia(
            "minuta de contrato",
            f"A minuta de contrato anexa traz {len(preexistentes)} lacuna(s) que "
            "só se preenchem na assinatura (número do contrato, dados da "
            "contratada). É o esperado para a minuta anexa ao aviso, e impede "
            "tratar o documento como pronto para assinatura.",
            origem=destino.name,
        )

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(destino))

    registro.informacao(
        "minuta de contrato",
        f"Minuta oficial {minuta.name} preparada como anexo. Campos preenchidos: "
        f"{', '.join(sorted(set(preenchidos))) or 'nenhum'}. Campos que só se "
        f"completam na assinatura, deixados em branco: "
        f"{', '.join(reservados) or 'nenhum'}.",
        origem=destino.name,
    )
    return destino, lacunas


def conferir_contra_tr(caminho_proposta: Path, dados_tr: Optional[DadosTR],
                       registro: Registro) -> None:
    """
    Confere item a item o modelo de proposta contra o TR (item 8 do escopo).

    Comparação por número de item, descrição, unidade e quantidade. Divergência
    aqui é bloqueio: proposta que não espelha o TR produz julgamento inválido.
    """
    exigir_python_docx()
    from docx import Document

    if dados_tr is None or not dados_tr.itens:
        return
    documento = Document(str(caminho_proposta))
    tabela = None
    for candidata in documento.tables:
        cabecalho = " ".join(c.text for c in candidata.rows[0].cells).upper()
        if "DESCRI" in cabecalho and ("QNTD" in cabecalho or "QUANT" in cabecalho):
            tabela = candidata
            break
    if tabela is None:
        registro.bloqueante(
            ETAPA,
            "O modelo de proposta gerado não tem quadro de itens conferível "
            "contra o TR.",
            origem=caminho_proposta.name,
        )
        return

    linhas = tabela.rows[1:]
    if len(linhas) != len(dados_tr.itens):
        registro.bloqueante(
            ETAPA,
            f"O modelo de proposta tem {len(linhas)} item(ns) e o TR tem "
            f"{len(dados_tr.itens)}.",
            origem=caminho_proposta.name,
        )
        return

    for linha, item in zip(linhas, dados_tr.itens):
        celulas = [c.text.strip() for c in linha.cells]
        texto = " | ".join(celulas)
        for rotulo, esperado in (
            ("número do item", item.numero),
            ("unidade", item.unidade),
            ("quantidade", item.quantidade),
        ):
            if esperado and esperado not in celulas:
                registro.bloqueante(
                    ETAPA,
                    f"Divergência de {rotulo} no item {item.numero}: o TR indica "
                    f"'{esperado}' e o modelo de proposta traz '{texto[:120]}'.",
                    origem=caminho_proposta.name,
                )
        if item.descricao and item.descricao[:40] not in texto:
            registro.bloqueante(
                ETAPA,
                f"A descrição do item {item.numero} no modelo de proposta não "
                "corresponde à do TR.",
                origem=caminho_proposta.name,
            )
    registro.informacao(
        ETAPA,
        f"Modelo de proposta conferido contra o TR: {len(dados_tr.itens)} "
        "item(ns) correspondentes.",
        origem=caminho_proposta.name,
    )
