#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
estilos_docx.py — Padrão visual, estilos nomeados CMI e classificação de papéis.

Carrega `09_padronizacao_documental/PERFIS_DOCUMENTAIS.json`, cria/normaliza os
estilos nomeados `CMI ...` e aplica a formatação correspondente ao papel de cada
parágrafo.

Princípio: FORMATAÇÃO pode ser corrigida; CONTEÚDO não. Nenhuma função daqui
altera texto — apenas propriedades de estilo, fonte, espaçamento e paginação.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from util_ooxml import (
    controle_viuvas_desligado,
    definir_controle_viuvas,
    definir_manter_com_proximo,
    definir_manter_junto,
    marcadores_pendentes,
    qn,
    texto_paragrafo,
)

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_PERFIS = RAIZ / "09_padronizacao_documental" / "PERFIS_DOCUMENTAIS.json"

# --------------------------------------------------------------------------- #
# Papéis documentais
# --------------------------------------------------------------------------- #

PAPEL_TITULO_DOCUMENTO = "titulo_documento"
PAPEL_IDENTIFICACAO = "identificacao"
PAPEL_TITULO_1 = "titulo_1"
PAPEL_TITULO_2 = "titulo_2"
PAPEL_TITULO_3 = "titulo_3"
PAPEL_CORPO = "corpo"
PAPEL_MARCADOR = "marcador"
PAPEL_ITEM = "item_numerado"
PAPEL_NOTA = "nota"
PAPEL_ASSINATURA = "assinatura"
PAPEL_CITACAO = "citacao_legal"
PAPEL_TABELA = "tabela"
PAPEL_CABECALHO_TABELA = "cabecalho_tabela"

# Estilo nomeado correspondente a cada papel.
ESTILO_POR_PAPEL = {
    PAPEL_TITULO_DOCUMENTO: "CMI Titulo do Documento",
    PAPEL_IDENTIFICACAO: "CMI Identificacao",
    PAPEL_TITULO_1: "CMI Titulo 1",
    PAPEL_TITULO_2: "CMI Titulo 2",
    PAPEL_TITULO_3: "CMI Titulo 3",
    PAPEL_CORPO: "CMI Corpo",
    PAPEL_MARCADOR: "CMI Marcador",
    PAPEL_NOTA: "CMI Nota",
    PAPEL_ASSINATURA: "CMI Assinatura",
    PAPEL_CITACAO: "CMI Citacao Legal",
    PAPEL_TABELA: "CMI Tabela",
    PAPEL_CABECALHO_TABELA: "CMI Cabecalho de Tabela",
}

# Chave da seção do padrão base usada por papel.
SECAO_PADRAO_POR_PAPEL = {
    PAPEL_TITULO_DOCUMENTO: "titulo_documento",
    PAPEL_TITULO_1: "titulo_1",
    PAPEL_TITULO_2: "titulo_2",
    PAPEL_TITULO_3: "titulo_3",
    PAPEL_ASSINATURA: "assinatura",
    PAPEL_NOTA: "nota",
    PAPEL_CITACAO: "citacao_legal",
}

# Estilos "genéricos" cujo parágrafo pode receber estilo nomeado CMI sem risco.
ESTILOS_GENERICOS = {
    "Normal", "Body Text", "Standard", "Text body", "Default Paragraph Font",
    "Corpo de texto", "Padrão", "Texto",
}

# Estilos de origem mapeáveis para papéis de título.
MAPA_ESTILO_TITULO = {
    "Heading 1": PAPEL_TITULO_1, "Título 1": PAPEL_TITULO_1, "Nivel 01": PAPEL_TITULO_1,
    "Heading 2": PAPEL_TITULO_2, "Título 2": PAPEL_TITULO_2, "Nivel 2": PAPEL_TITULO_2,
    "Heading 3": PAPEL_TITULO_3, "Título 3": PAPEL_TITULO_3, "Nivel 3": PAPEL_TITULO_3,
}
MAPA_ESTILO_NOTA = {"Nota explicativa", "Nota", "Footnote Text", "Caption"}

# --------------------------------------------------------------------------- #
# Padrões textuais
# --------------------------------------------------------------------------- #

RE_NUMERO_HIERARQUICO = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*[\.\)\-–—]?\s+\S")
RE_ALINEA = re.compile(r"^\s*[a-z]\s*\)\s+\S")
RE_INCISO = re.compile(r"^\s*[IVXLC]+\s*[\-–—]\s+\S")
RE_CLAUSULA = re.compile(r"^\s*(CL[ÁA]USULA|PAR[ÁA]GRAFO)\b", re.IGNORECASE)
RE_CITACAO = re.compile(r"^\s*[\"“«]|^\s*Art\.\s*\d+", re.IGNORECASE)
RE_IDENTIFICACAO = re.compile(
    r"^\s*(PROCESSO|PROCESSO ADMINISTRATIVO|SOLICITA[ÇC][ÃA]O|DISPENSA|INEXIGIBILIDADE|"
    r"CONTRATO|OBJETO|INTERESSADO|ASSUNTO|REFER[ÊE]NCIA|MODALIDADE)\s*(n[ºo°]|:)",
    re.IGNORECASE,
)
RE_ASSINATURA = re.compile(
    r"(Presidente|Vereador|Secret[áa]ri[oa]|Diretor|Agente de Contrata[çc][ãa]o|"
    r"Contador|Procurador|Assessor|Respons[áa]vel|Fiscal do Contrato|"
    r"C[âa]mara Municipal de Itanhandu)",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# Carga do padrão
# --------------------------------------------------------------------------- #

@dataclass
class PadraoVisual:
    """Padrão visual institucional + perfil documental selecionado."""

    base: dict[str, Any]
    perfil: dict[str, Any]
    perfil_id: str
    diferencas_permitidas: list[str]
    mapa_minuta_perfil: dict[str, str]

    # -- acessos convenientes ------------------------------------------------
    @property
    def fonte(self) -> str:
        """
        Fonte principal, com prioridade para a do perfil.

        O perfil pode declarar fonte própria quando a minuta-mãe tem padrão
        institucional distinto (é o caso do DFD para o PCA, em Times New Roman).
        Fora isso, prevalece a fonte institucional da base.
        """
        return self.perfil.get("fonte_principal") or self.base["fonte_principal"]

    @property
    def fontes_toleradas(self) -> set[str]:
        """
        Fontes que a auditoria NÃO acusa e que a padronização NÃO reescreve.

        É deliberadamente estreito: misturar Calibri e Arial no mesmo documento
        é justamente o defeito a corrigir, então a tolerância é a fonte do
        perfil (mais a variante metricamente idêntica usada pelo LibreOffice).
        """
        toleradas = {self.fonte}
        toleradas |= set(self.base.get("equivalentes_de_fonte", {}).get(self.fonte, []))
        return toleradas

    def tamanho(self, chave: str) -> float:
        return float(self.base["tamanhos_pt"][chave])

    def cor(self, chave: str) -> str:
        return self.base["cores"][chave]

    def secao(self, nome: str) -> dict[str, Any]:
        return self.base.get(nome, {})

    def estilo_permitido(self, nome_estilo: str) -> bool:
        return nome_estilo in self.perfil.get("estilos_permitidos", [])

    @property
    def niveis_numeracao(self) -> int:
        return int(self.perfil.get("niveis_numeracao", 3))

    @property
    def renumeracao_automatica(self) -> bool:
        return bool(self.perfil.get("renumeracao_automatica", True))


def carregar_padrao(perfil_id: str = "generico",
                    caminho: Optional[Path] = None) -> PadraoVisual:
    """Carrega PERFIS_DOCUMENTAIS.json e devolve o padrão do perfil pedido."""
    caminho = caminho or CAMINHO_PERFIS
    if not caminho.exists():
        raise FileNotFoundError(
            f"Padrão visual não encontrado: {caminho}. "
            "O módulo depende de 09_padronizacao_documental/PERFIS_DOCUMENTAIS.json."
        )
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    perfis = dados["perfis"]
    if perfil_id not in perfis:
        disponiveis = ", ".join(sorted(perfis))
        raise ValueError(f"Perfil '{perfil_id}' inexistente. Disponíveis: {disponiveis}")
    return PadraoVisual(
        base=dados["padrao_base"],
        perfil=perfis[perfil_id],
        perfil_id=perfil_id,
        diferencas_permitidas=list(dados.get("diferencas_permitidas_padrao", [])),
        mapa_minuta_perfil=dict(dados.get("mapa_minuta_para_perfil", {})),
    )


def perfil_por_arquivo(nome_arquivo: str,
                       caminho: Optional[Path] = None) -> Optional[str]:
    """Deduz o perfil a partir do nome do arquivo da minuta-mãe."""
    caminho = caminho or CAMINHO_PERFIS
    if not caminho.exists():
        return None
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    mapa = dados.get("mapa_minuta_para_perfil", {})
    if nome_arquivo in mapa:
        return mapa[nome_arquivo]
    base = nome_arquivo.upper()
    for chave, perfil in mapa.items():
        raiz = chave.replace("_MINUTA_MAE.docx", "")
        if raiz and raiz in base:
            return perfil
    return None


# --------------------------------------------------------------------------- #
# Criação e normalização dos estilos nomeados
# --------------------------------------------------------------------------- #

def _aplicar_spec_em_estilo(estilo, padrao: PadraoVisual, spec: dict[str, Any],
                            tamanho_pt: float) -> list[str]:
    """Escreve fonte/parágrafo de um estilo nomeado. Devolve mudanças."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor

    mudancas: list[str] = []
    fonte = estilo.font
    if fonte.name != padrao.fonte:
        fonte.name = padrao.fonte
        mudancas.append("fonte")
    if fonte.size is None or abs(fonte.size.pt - tamanho_pt) > 0.01:
        fonte.size = Pt(tamanho_pt)
        mudancas.append("tamanho")
    if spec.get("negrito") is not None and fonte.bold != spec["negrito"]:
        fonte.bold = spec["negrito"]
        mudancas.append("negrito")
    if spec.get("italico") is not None and fonte.italic != spec["italico"]:
        fonte.italic = spec["italico"]
        mudancas.append("italico")
    cor_alvo = RGBColor.from_string(spec.get("cor", padrao.cor("texto")))
    if fonte.color.rgb != cor_alvo:
        fonte.color.rgb = cor_alvo
        mudancas.append("cor")

    pf = estilo.paragraph_format
    alinhamento = spec.get("alinhamento")
    if alinhamento:
        alvo = getattr(WD_ALIGN_PARAGRAPH, alinhamento)
        if pf.alignment != alvo:
            pf.alignment = alvo
            mudancas.append("alinhamento")
    if spec.get("entrelinhas") is not None:
        if pf.line_spacing != spec["entrelinhas"]:
            pf.line_spacing = spec["entrelinhas"]
            mudancas.append("entrelinhas")
    for chave, atributo in (("espaco_antes_pt", "space_before"),
                            ("espaco_depois_pt", "space_after")):
        if spec.get(chave) is None:
            continue
        atual = getattr(pf, atributo)
        alvo_pt = float(spec[chave])
        if atual is None or abs(atual.pt - alvo_pt) > 0.01:
            setattr(pf, atributo, Pt(alvo_pt))
            mudancas.append(atributo)
    for chave, atributo in (("recuo_primeira_linha_cm", "first_line_indent"),
                            ("recuo_esquerdo_cm", "left_indent")):
        if spec.get(chave) is None:
            continue
        atual = getattr(pf, atributo)
        alvo_cm = float(spec[chave])
        if atual is None or abs(atual.cm - alvo_cm) > 0.01:
            setattr(pf, atributo, Cm(alvo_cm))
            mudancas.append(atributo)
    if spec.get("manter_com_proximo") is not None:
        if pf.keep_with_next != spec["manter_com_proximo"]:
            pf.keep_with_next = spec["manter_com_proximo"]
            mudancas.append("keep_with_next")
    if spec.get("manter_junto") is not None:
        if pf.keep_together != spec["manter_junto"]:
            pf.keep_together = spec["manter_junto"]
            mudancas.append("keep_together")
    if padrao.base["paginacao"].get("controle_viuvas_orfas") and pf.widow_control is not True:
        pf.widow_control = True
        mudancas.append("widow_control")
    return mudancas


def _spec_do_estilo(padrao: PadraoVisual, nome: str) -> tuple[dict[str, Any], float]:
    """Especificação (spec, tamanho_pt) de cada estilo nomeado CMI."""
    corpo = dict(padrao.secao("corpo"))
    mapa: dict[str, tuple[dict[str, Any], float]] = {
        "CMI Titulo do Documento": (dict(padrao.secao("titulo_documento")),
                                    padrao.tamanho("titulo_documento")),
        "CMI Titulo 1": (dict(padrao.secao("titulo_1")), padrao.tamanho("titulo_1")),
        "CMI Titulo 2": (dict(padrao.secao("titulo_2")), padrao.tamanho("titulo_2")),
        "CMI Titulo 3": (dict(padrao.secao("titulo_3")), padrao.tamanho("titulo_3")),
        "CMI Corpo": (corpo, padrao.tamanho("corpo")),
        "CMI Corpo sem Recuo": ({**corpo, "recuo_primeira_linha_cm": 0.0},
                                padrao.tamanho("corpo")),
        "CMI Identificacao": ({**corpo, "alinhamento": "LEFT", "entrelinhas": 1.0,
                               "recuo_primeira_linha_cm": 0.0, "negrito": None},
                              padrao.tamanho("corpo")),
        "CMI Item Numerado 1": ({**corpo, "recuo_primeira_linha_cm": 0.0,
                                 "recuo_esquerdo_cm": 0.0}, padrao.tamanho("corpo")),
        "CMI Item Numerado 2": ({**corpo, "recuo_primeira_linha_cm": 0.0,
                                 "recuo_esquerdo_cm": 1.0}, padrao.tamanho("corpo")),
        "CMI Item Numerado 3": ({**corpo, "recuo_primeira_linha_cm": 0.0,
                                 "recuo_esquerdo_cm": 2.0}, padrao.tamanho("corpo")),
        "CMI Marcador": ({**corpo, "alinhamento": "JUSTIFY",
                          "recuo_primeira_linha_cm": 0.0, "recuo_esquerdo_cm": 1.0},
                         padrao.tamanho("corpo")),
        "CMI Tabela": ({"alinhamento": "LEFT", "entrelinhas": 1.0,
                        "espaco_antes_pt": 2.0, "espaco_depois_pt": 2.0,
                        "recuo_primeira_linha_cm": 0.0, "recuo_esquerdo_cm": 0.0},
                       padrao.tamanho("tabela")),
        "CMI Cabecalho de Tabela": ({"alinhamento": "CENTER", "entrelinhas": 1.0,
                                     "negrito": True, "espaco_antes_pt": 2.0,
                                     "espaco_depois_pt": 2.0,
                                     "recuo_primeira_linha_cm": 0.0,
                                     "recuo_esquerdo_cm": 0.0,
                                     "manter_com_proximo": True},
                                    padrao.tamanho("cabecalho_tabela")),
        "CMI Nota": (dict(padrao.secao("nota")), padrao.tamanho("nota")),
        "CMI Assinatura": (dict(padrao.secao("assinatura")), padrao.tamanho("assinatura")),
        "CMI Campo Pendente": ({**corpo, "cor": padrao.cor("campo_pendente"),
                                "negrito": True}, padrao.tamanho("corpo")),
        "CMI Citacao Legal": (dict(padrao.secao("citacao_legal")), padrao.tamanho("citacao")),
    }
    if nome not in mapa:
        raise KeyError(f"Estilo CMI sem especificação: {nome}")
    return mapa[nome]


def garantir_estilos(documento, padrao: PadraoVisual,
                     todos: bool = False) -> dict[str, list[str]]:
    """
    Cria (ou normaliza) os estilos nomeados CMI previstos no perfil.

    `todos=True` cria a biblioteca completa (usado no modo revisão de minuta-mãe).
    Idempotente: em nova execução nada muda, pois as propriedades já estarão no
    valor alvo.
    """
    from docx.enum.style import WD_STYLE_TYPE

    nomes = list(ESTILO_POR_PAPEL.values()) + [
        "CMI Corpo sem Recuo", "CMI Item Numerado 1", "CMI Item Numerado 2",
        "CMI Item Numerado 3", "CMI Campo Pendente",
    ]
    if not todos:
        nomes = [n for n in nomes if padrao.estilo_permitido(n)]

    relatorio: dict[str, list[str]] = {}
    existentes = {e.name for e in documento.styles}
    for nome in sorted(set(nomes)):
        spec, tamanho = _spec_do_estilo(padrao, nome)
        if nome in existentes:
            estilo = documento.styles[nome]
            criado = []
        else:
            estilo = documento.styles.add_style(nome, WD_STYLE_TYPE.PARAGRAPH)
            try:
                estilo.base_style = documento.styles["Normal"]
            except KeyError:  # pragma: no cover - documento sem estilo Normal
                pass
            estilo.quick_style = True
            criado = ["criado"]
        mudancas = criado + _aplicar_spec_em_estilo(estilo, padrao, spec, tamanho)
        if mudancas:
            relatorio[nome] = mudancas
    return relatorio


# --------------------------------------------------------------------------- #
# Classificação de papéis
# --------------------------------------------------------------------------- #

def nome_do_estilo(paragrafo) -> str:
    """Nome do estilo do parágrafo, tolerando estilo sem `<w:name>`."""
    estilo = paragrafo.style
    if estilo is None or estilo.name is None:
        return "Normal"
    return estilo.name


def _tem_numeracao_automatica(paragrafo) -> bool:
    pPr = paragrafo._p.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:numPr")) is not None


def _todo_maiusculo(texto: str) -> bool:
    letras = [c for c in texto if c.isalpha()]
    return bool(letras) and all(c.isupper() for c in letras)


def classificar_paragrafo(paragrafo, indice: int, total: int,
                          padrao: PadraoVisual,
                          em_tabela: bool = False,
                          primeira_linha_tabela: bool = False) -> str:
    """
    Determina o papel documental de um parágrafo.

    A classificação é conservadora: na dúvida, `corpo`. Nenhum papel é inferido
    a partir de conteúdo jurídico — apenas de forma (estilo de origem, posição,
    padrão do rótulo, caixa alta, comprimento).
    """
    if em_tabela:
        return PAPEL_CABECALHO_TABELA if primeira_linha_tabela else PAPEL_TABELA

    texto = texto_paragrafo(paragrafo).strip()
    if not texto:
        return PAPEL_CORPO

    # Há minutas com estilo sem <w:name>; nesse caso `.name` vem None.
    nome_estilo = nome_do_estilo(paragrafo)

    if nome_estilo.startswith("CMI "):
        for papel, estilo in ESTILO_POR_PAPEL.items():
            if estilo == nome_estilo:
                return papel
        return PAPEL_CORPO
    if nome_estilo in MAPA_ESTILO_TITULO:
        return MAPA_ESTILO_TITULO[nome_estilo]
    if nome_estilo in MAPA_ESTILO_NOTA:
        return PAPEL_NOTA

    # Título do documento: no topo, curto, caixa alta, centralizado.
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    centralizado = paragrafo.alignment == WD_ALIGN_PARAGRAPH.CENTER
    if indice < 8 and centralizado and _todo_maiusculo(texto) and len(texto) <= 120:
        return PAPEL_TITULO_DOCUMENTO

    if RE_IDENTIFICACAO.match(texto) and len(texto) <= 200:
        return PAPEL_IDENTIFICACAO

    if RE_CLAUSULA.match(texto) and len(texto) <= 160:
        return PAPEL_TITULO_1

    casamento = RE_NUMERO_HIERARQUICO.match(texto)
    if casamento and not _tem_numeracao_automatica(paragrafo):
        nivel = casamento.group(1).count(".") + 1
        curto = len(texto) <= 140
        if curto and nivel <= padrao.niveis_numeracao:
            return {1: PAPEL_TITULO_1, 2: PAPEL_TITULO_2}.get(nivel, PAPEL_TITULO_3)
        return PAPEL_ITEM

    if RE_ALINEA.match(texto) or RE_INCISO.match(texto):
        return PAPEL_ITEM

    if _tem_numeracao_automatica(paragrafo):
        return PAPEL_ITEM

    # Bloco de assinatura: terço final, centralizado, curto.
    if centralizado and len(texto) <= 90 and indice >= max(0, int(total * 0.66)):
        if RE_ASSINATURA.search(texto) or _todo_maiusculo(texto):
            return PAPEL_ASSINATURA

    if RE_CITACAO.match(texto) and len(texto) > 40:
        return PAPEL_CITACAO

    if _todo_maiusculo(texto) and len(texto) <= 100 and not centralizado:
        return PAPEL_TITULO_1

    return PAPEL_CORPO


def tem_campo_pendente(paragrafo) -> list[str]:
    return marcadores_pendentes(texto_paragrafo(paragrafo))


# --------------------------------------------------------------------------- #
# Aplicação da formatação
# --------------------------------------------------------------------------- #

def _cor_do_run(run) -> Optional[str]:
    cor = run.font.color
    if cor is None or cor.type is None or cor.rgb is None:
        return None
    return str(cor.rgb)


def _em_hyperlink(run) -> bool:
    pai = run._r.getparent()
    return pai is not None and pai.tag == qn("w:hyperlink")


def normalizar_runs(paragrafo, padrao: PadraoVisual, tamanho_pt: float,
                    normalizar_cores: bool = False) -> list[str]:
    """
    Normaliza fonte, tamanho e (opcionalmente) cor dos runs.

    Não toca em negrito, itálico e sublinhado: têm função semântica. Não toca em
    runs dentro de hyperlink. Cores diferentes do preto são REPORTADAS por
    padrão e só corrigidas com `normalizar_cores=True`, porque nas minutas de
    contrato o vermelho marca campo a preencher.
    """
    from docx.shared import Pt, RGBColor

    mudancas: list[str] = []
    preto = RGBColor.from_string(padrao.cor("texto"))
    for run in paragrafo.runs:
        if not (run.text or ""):
            continue
        nome_fonte = run.font.name
        if nome_fonte is not None and nome_fonte not in padrao.fontes_toleradas:
            run.font.name = padrao.fonte
            mudancas.append(f"fonte {nome_fonte} -> {padrao.fonte}")
        tamanho = run.font.size
        if tamanho is not None and abs(tamanho.pt - tamanho_pt) > 0.01:
            run.font.size = Pt(tamanho_pt)
            mudancas.append(f"tamanho {tamanho.pt}pt -> {tamanho_pt}pt")
        if normalizar_cores and not _em_hyperlink(run):
            cor = _cor_do_run(run)
            if cor is not None and cor != padrao.cor("texto"):
                run.font.color.rgb = preto
                mudancas.append(f"cor {cor} -> {padrao.cor('texto')}")
    return mudancas


def aplicar_formatacao_paragrafo(paragrafo, papel: str, padrao: PadraoVisual,
                                 aplicar_estilo_nomeado: bool = True,
                                 normalizar_cores: bool = False) -> list[str]:
    """
    Aplica ao parágrafo a formatação do seu papel documental.

    O estilo nomeado só é atribuído quando o parágrafo carrega estilo genérico
    (Normal, Body Text, Standard...). Parágrafos com numeração automática ou
    estilo próprio mantêm o estilo e recebem apenas normalização de fonte,
    espaçamento e paginação — assim a lista automática não é quebrada.
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    mudancas: list[str] = []
    nome_estilo_alvo = ESTILO_POR_PAPEL.get(papel)
    nome_atual = nome_do_estilo(paragrafo)
    pode_trocar_estilo = (
        aplicar_estilo_nomeado
        and nome_estilo_alvo is not None
        and padrao.estilo_permitido(nome_estilo_alvo)
        and nome_atual != nome_estilo_alvo
        and (nome_atual in ESTILOS_GENERICOS
             or nome_atual in MAPA_ESTILO_TITULO
             or nome_atual in MAPA_ESTILO_NOTA)
        and not _tem_numeracao_automatica(paragrafo)
    )
    if pode_trocar_estilo:
        try:
            paragrafo.style = paragrafo.part.document.styles[nome_estilo_alvo]
            mudancas.append(f"estilo {nome_atual} -> {nome_estilo_alvo}")
        except KeyError:
            pass

    # Tamanho de fonte esperado por papel.
    tamanho = {
        PAPEL_TITULO_DOCUMENTO: padrao.tamanho("titulo_documento"),
        PAPEL_TITULO_1: padrao.tamanho("titulo_1"),
        PAPEL_TITULO_2: padrao.tamanho("titulo_2"),
        PAPEL_TITULO_3: padrao.tamanho("titulo_3"),
        PAPEL_NOTA: padrao.tamanho("nota"),
        PAPEL_CITACAO: padrao.tamanho("citacao"),
        PAPEL_TABELA: padrao.tamanho("tabela"),
        PAPEL_CABECALHO_TABELA: padrao.tamanho("cabecalho_tabela"),
        PAPEL_ASSINATURA: padrao.tamanho("assinatura"),
    }.get(papel, padrao.tamanho("corpo"))
    mudancas += normalizar_runs(paragrafo, padrao, tamanho, normalizar_cores)

    pf = paragrafo.paragraph_format
    spec = padrao.secao(SECAO_PADRAO_POR_PAPEL.get(papel, "corpo"))

    # Alinhamento: só normaliza parágrafo de corpo longo já alinhado à esquerda
    # ou sem alinhamento. Centralização existente é intencional e é preservada.
    if papel == PAPEL_CORPO:
        texto = texto_paragrafo(paragrafo).strip()
        if len(texto) >= 80 and pf.alignment in (None, WD_ALIGN_PARAGRAPH.LEFT):
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            mudancas.append("alinhamento -> justificado")
    elif papel in (PAPEL_TITULO_1, PAPEL_TITULO_2, PAPEL_TITULO_3):
        if pf.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            mudancas.append("alinhamento -> esquerda")

    # Espaçamento entre linhas: corrige valores herdados incoerentes
    # (inclusive espaçamento exato em EMU vindo de conversão de formato).
    alvo_entrelinhas = spec.get("entrelinhas")
    if alvo_entrelinhas is not None:
        atual = pf.line_spacing
        if atual is not None and not isinstance(atual, float):
            pf.line_spacing = alvo_entrelinhas
            mudancas.append("entrelinhas exatas -> múltiplo")
        elif isinstance(atual, float) and abs(atual - alvo_entrelinhas) > 0.001:
            pf.line_spacing = alvo_entrelinhas
            mudancas.append(f"entrelinhas {atual} -> {alvo_entrelinhas}")

    for chave, atributo in (("espaco_antes_pt", "space_before"),
                            ("espaco_depois_pt", "space_after")):
        if spec.get(chave) is None:
            continue
        atual = getattr(pf, atributo)
        alvo_pt = float(spec[chave])
        if atual is not None and abs(atual.pt - alvo_pt) > 0.01:
            setattr(pf, atributo, Pt(alvo_pt))
            mudancas.append(f"{atributo} {atual.pt}pt -> {alvo_pt}pt")

    # Paginação por função do parágrafo.
    if papel in (PAPEL_TITULO_DOCUMENTO, PAPEL_TITULO_1, PAPEL_TITULO_2,
                 PAPEL_TITULO_3, PAPEL_CABECALHO_TABELA):
        if definir_manter_com_proximo(paragrafo, True):
            mudancas.append("keep_with_next")
        if definir_manter_junto(paragrafo, True):
            mudancas.append("keep_lines")
    if papel == PAPEL_ASSINATURA:
        if definir_manter_com_proximo(paragrafo, True):
            mudancas.append("keep_with_next")
        if definir_manter_junto(paragrafo, True):
            mudancas.append("keep_lines")
    # Só religa o controle de viúvas quando ele foi explicitamente desligado —
    # o padrão do Word já é ligado, e escrever o flag em todo parágrafo geraria
    # ruído sem efeito visual.
    if padrao.base["paginacao"].get("controle_viuvas_orfas"):
        if controle_viuvas_desligado(paragrafo) and definir_controle_viuvas(paragrafo, True):
            mudancas.append("widow_control religado")

    return mudancas
