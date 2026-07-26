#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nomes_arquivos.py — nomes canônicos, sanitização e leitura de nomes suspeitos.

Um nome de arquivo não é prova de nada (regra 34: "confiar somente no nome do
arquivo" é proibido), mas é a primeira fonte de desordem numa pasta de processo.
Este módulo concentra:

1. o nome estável de cada tipo documental na área corrente (item 7 do escopo);
2. o nome das versões no histórico (item 8);
3. o nome padronizado dos documentos externos (item 18);
4. o reconhecimento dos nomes que denunciam versão solta — "final", "novo",
   "corrigido", "cópia", "TR (1)" — usados só para SINALIZAR, nunca para apagar.

Nada aqui toca disco.
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

LIMITE_MAX_PATH = 250  # margem sob os 260 caracteres da API clássica do Windows


def caminho_os(caminho: Path | str) -> str:
    """
    Caminho aceito pela API do Windows mesmo além de MAX_PATH.

    Uma pasta de processo em `D:\\Setor de Compras\\Contratações 2026\\...` com
    nome padronizado de documento externo passa fácil dos 260 caracteres — e o
    Windows responde a isso com "o sistema não pode encontrar o caminho
    especificado", mensagem que manda o operador procurar um arquivo ausente que
    está lá. O prefixo `\\\\?\\` desliga o limite.

    Fora do Windows, e em caminho curto, devolve o caminho como veio: prefixo
    desnecessário só polui mensagem de erro e log.
    """
    texto = str(caminho)
    if sys.platform != "win32":
        return texto
    absoluto = os.path.abspath(texto)
    if absoluto.startswith("\\\\?\\") or len(absoluto) < LIMITE_MAX_PATH:
        return texto
    if absoluto.startswith("\\\\"):  # compartilhamento de rede (UNC)
        return "\\\\?\\UNC" + absoluto[1:]
    return "\\\\?\\" + absoluto


def existe(caminho: Path | str) -> bool:
    """
    `Path.exists()` que não mente em caminho longo.

    Sem isto, um arquivo perfeitamente presente além dos 260 caracteres é
    reportado como ausente — e a validação acusaria divergência entre manifesto
    e disco onde não há nenhuma.
    """
    return os.path.exists(caminho_os(caminho))

# --------------------------------------------------------------------------- #
# Áreas da estrutura do processo
# --------------------------------------------------------------------------- #

AREA_CONTROLE = "00_CONTROLE"
AREA_ELABORACAO = "01_EM_ELABORACAO"
AREA_OFICIAIS = "02_DOCUMENTOS_OFICIAIS"
AREA_EXTERNOS = "03_DOCUMENTOS_EXTERNOS"
AREA_PUBLICACOES = "04_PUBLICACOES"
AREA_ASSINADOS = "05_ASSINADOS"
AREA_EXECUCAO = "06_EXECUCAO_CONTRATUAL"
AREA_HISTORICO = "90_HISTORICO"
AREA_QUARENTENA = "98_QUARENTENA"
AREA_TEMPORARIOS = "99_TEMPORARIOS"

FASE_PREPARATORIA = "FASE_PREPARATORIA"
FASE_SELECAO = "SELECAO_FORNECEDOR"
FASE_CONTRATACAO = "CONTRATACAO"
FASE_EXECUCAO = "EXECUCAO"

# Subpastas dos documentos externos (item 17 do escopo).
CATEGORIAS_EXTERNAS: dict[str, str] = {
    "solicitacoes": "01_SOLICITACOES",
    "cotacoes_e_propostas": "02_COTACOES_E_PROPOSTAS",
    "habilitacao": "03_HABILITACAO",
    "emails_e_comunicacoes": "04_EMAILS_E_COMUNICACOES",
    "referencias_tecnicas": "05_REFERENCIAS_TECNICAS",
    "pareceres": "06_PARECERES",
    "comprovantes": "07_COMPROVANTES",
    "outros": "08_OUTROS",
}

# Subpastas do histórico (item 4 do escopo). Tipo sem pasta própria vai em OUTROS.
HISTORICO_PROPRIO = ("DFD", "ETP", "TR", "PESQUISA_DE_PRECOS", "AVISO", "CONTRATO")

# Subpastas de 05_ASSINADOS.
ASSINADOS_PROPRIO = ("DFD", "ETP", "TR", "AVISO", "CONTRATO")


# --------------------------------------------------------------------------- #
# Tipos documentais
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class TipoDocumental:
    """Descrição de um tipo documental gerado pelo Charles."""

    tipo: str
    titulo: str
    fase: str
    extensao_padrao: str = ".docx"

    @property
    def pasta_historico(self) -> str:
        return self.tipo if self.tipo in HISTORICO_PROPRIO else "OUTROS"

    @property
    def pasta_assinados(self) -> str:
        return self.tipo if self.tipo in ASSINADOS_PROPRIO else "OUTROS"


TIPOS: dict[str, TipoDocumental] = {
    t.tipo: t
    for t in (
        TipoDocumental("DFD", "Documento de Formalização da Demanda", FASE_PREPARATORIA),
        TipoDocumental("ETP", "Estudo Técnico Preliminar", FASE_PREPARATORIA),
        TipoDocumental("TR", "Termo de Referência", FASE_PREPARATORIA),
        TipoDocumental("MAPA_DE_RISCOS", "Mapa de Riscos", FASE_PREPARATORIA),
        TipoDocumental("PESQUISA_DE_PRECOS", "Pesquisa de Preços", FASE_PREPARATORIA),
        TipoDocumental("JUSTIFICATIVA_CONTRATACAO_DIRETA",
                       "Justificativa da Contratação Direta", FASE_PREPARATORIA),
        TipoDocumental("AUTORIZACAO", "Autorização de Abertura", FASE_PREPARATORIA),
        TipoDocumental("AVISO", "Aviso de Contratação Direta", FASE_SELECAO),
        TipoDocumental("AVISO_COMPLETO", "Aviso de Contratação Direta Completo",
                       FASE_SELECAO),
        TipoDocumental("ATA_JULGAMENTO", "Ata de Julgamento", FASE_SELECAO),
        TipoDocumental("HOMOLOGACAO", "Termo de Adjudicação e Homologação", FASE_SELECAO),
        TipoDocumental("CONTRATO", "Termo de Contrato", FASE_CONTRATACAO),
        TipoDocumental("EXTRATO", "Extrato de Publicação", FASE_CONTRATACAO),
        TipoDocumental("ORDEM_FORNECIMENTO", "Ordem de Fornecimento", FASE_EXECUCAO),
        TipoDocumental("TERMO_RECEBIMENTO", "Termo de Recebimento", FASE_EXECUCAO),
    )
}


class TipoDesconhecido(ValueError):
    """Tipo documental fora da tabela oficial — não se inventa tipo."""


def obter_tipo(tipo: str) -> TipoDocumental:
    chave = (tipo or "").strip().upper().replace("-", "_").replace(" ", "_")
    if chave not in TIPOS:
        conhecidos = ", ".join(sorted(TIPOS))
        raise TipoDesconhecido(
            f"Tipo documental desconhecido: {tipo!r}. Tipos previstos: {conhecidos}."
        )
    return TIPOS[chave]


# --------------------------------------------------------------------------- #
# Sanitização
# --------------------------------------------------------------------------- #

# Reservados do Windows: nenhum arquivo pode se chamar assim, com ou sem extensão.
RESERVADOS_WINDOWS = {
    "CON", "PRN", "AUX", "NUL",
    *{f"COM{n}" for n in range(1, 10)},
    *{f"LPT{n}" for n in range(1, 10)},
}

RE_INVALIDO = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def remover_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def sanitizar_componente(texto: str, limite: int = 60) -> str:
    """
    Reduz um pedaço livre de texto a `A-Z 0-9 _`, sem acento e sem espaço.

    Usado em motivo de versão, origem e descrição de documento externo. Texto
    que sobra vazio devolve string vazia — quem chama decide o que fazer, este
    módulo não inventa rótulo.
    """
    texto = remover_acentos(str(texto or "")).upper()
    texto = RE_INVALIDO.sub(" ", texto)
    texto = re.sub(r"[^A-Z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    if len(texto) > limite:
        texto = texto[:limite].rstrip("_")
    if texto in RESERVADOS_WINDOWS:
        texto = f"{texto}_"
    return texto


def sanitizar_nome_arquivo(nome: str, limite: int = 120) -> str:
    """Sanitiza preservando a extensão. Nome inteiro inválido vira ARQUIVO."""
    nome = remover_acentos(str(nome or "")).strip()
    ponto = nome.rfind(".")
    if 0 < ponto < len(nome) - 1 and len(nome) - ponto <= 12:
        base, extensao = nome[:ponto], nome[ponto:].lower()
    else:
        base, extensao = nome, ""
    extensao = RE_INVALIDO.sub("", extensao)
    base = sanitizar_componente(base, limite=limite) or "ARQUIVO"
    return f"{base}{extensao}"


def sanitizar_nome_processo(numero: str) -> str:
    """
    "PA 031/2026" -> "PA_031_2026". Serve de identificador de pasta.

    Não valida a numeração administrativa: quem numera processo é a Câmara.
    """
    return sanitizar_componente(numero, limite=80)


# --------------------------------------------------------------------------- #
# Nome canônico da área corrente (item 7)
# --------------------------------------------------------------------------- #

def nome_canonico(tipo: str, extensao: str = ".docx") -> str:
    """`TR`, `.docx` -> `TR.docx`. Sem número de versão, sempre (item 7)."""
    descricao = obter_tipo(tipo)
    extensao = normalizar_extensao(extensao or descricao.extensao_padrao)
    return f"{descricao.tipo}{extensao}"


def nome_canonico_assinado(tipo: str, extensao: str = ".pdf") -> str:
    descricao = obter_tipo(tipo)
    return f"{descricao.tipo}_ASSINADO{normalizar_extensao(extensao)}"


def normalizar_extensao(extensao: str) -> str:
    extensao = (extensao or "").strip().lower()
    if not extensao:
        return ""
    if not extensao.startswith("."):
        extensao = f".{extensao}"
    return RE_INVALIDO.sub("", extensao)


# --------------------------------------------------------------------------- #
# Nome no histórico (item 8)
# --------------------------------------------------------------------------- #

MOTIVO_LIMITE = 40


def nome_historico(
    tipo: str,
    versao: int,
    momento: Optional[datetime] = None,
    motivo: str = "",
    extensao: str = ".docx",
) -> str:
    """
    `TIPO_vNNN_AAAAMMDD_HHMMSS[_MOTIVO].ext` (item 8 do escopo).

    O motivo é opcional, sanitizado e curto. Motivos proibidos ("final",
    "novo", "corrigido"...) não são bloqueados aqui de propósito: eles viram
    apenas texto depois do carimbo de versão e data, que é o que identifica.
    Quem bloqueia nome solto é `nome_suspeito`, aplicado à ÁREA CORRENTE.
    """
    descricao = obter_tipo(tipo)
    momento = momento or datetime.now()
    carimbo = momento.strftime("%Y%m%d_%H%M%S")
    partes = [descricao.tipo, f"v{int(versao):03d}", carimbo]
    sufixo = sanitizar_componente(motivo, limite=MOTIVO_LIMITE)
    if sufixo:
        partes.append(sufixo)
    return "_".join(partes) + normalizar_extensao(extensao)


RE_NOME_HISTORICO = re.compile(
    r"^(?P<tipo>[A-Z0-9_]+?)_v(?P<versao>\d{3})_"
    r"(?P<data>\d{8})_(?P<hora>\d{6})(?:_(?P<motivo>[A-Z0-9_]+))?"
    r"(?P<extensao>\.[A-Za-z0-9]+)$"
)


def ler_nome_historico(nome: str) -> Optional[dict[str, str]]:
    """Devolve os campos de um nome de histórico, ou None se não for um."""
    achado = RE_NOME_HISTORICO.match(nome)
    return achado.groupdict() if achado else None


# --------------------------------------------------------------------------- #
# Nome do documento externo (item 18)
# --------------------------------------------------------------------------- #

def nome_externo(
    data_documento: Optional[str],
    origem: Optional[str],
    tipo_documento: Optional[str],
    descricao: Optional[str] = None,
    extensao: str = ".pdf",
) -> str:
    """
    `AAAA-MM-DD_ORIGEM_TIPO_DESCRICAO.ext` (item 18 do escopo).

    Campo desconhecido não é inventado: entra como `SEM_DATA`, `ORIGEM_NAO_
    IDENTIFICADA` ou `TIPO_NAO_IDENTIFICADO`, e quem chama registra a pendência.
    """
    data = (data_documento or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        data = "SEM_DATA"
    partes = [
        data,
        sanitizar_componente(origem, limite=40) or "ORIGEM_NAO_IDENTIFICADA",
        sanitizar_componente(tipo_documento, limite=40) or "TIPO_NAO_IDENTIFICADO",
    ]
    complemento = sanitizar_componente(descricao, limite=40)
    if complemento:
        partes.append(complemento)
    return "_".join(partes) + normalizar_extensao(extensao)


# --------------------------------------------------------------------------- #
# Nomes suspeitos de versão solta (itens 1, 23 e 36)
# --------------------------------------------------------------------------- #

PADROES_SUSPEITOS: tuple[tuple[str, str], ...] = (
    (r"(?:^|[_\s\-])(?:copia|copy|copy\s+of|copia\s+de)(?:[_\s\-]|$)",
     "nome de cópia"),
    (r"(?:^|[_\s\-])final(?:[_\s\-]?\d+)?(?:[_\s\-]|$)", "marcado como 'final'"),
    (r"(?:^|[_\s\-])(?:nov[oa]|atualizad[oa]|ultim[oa]|definitiv[oa])"
     r"(?:[_\s\-]|$)", "marcado como 'novo/atualizado/último'"),
    (r"(?:^|[_\s\-])corrigid[oa](?:[_\s\-]|$)", "marcado como 'corrigido'"),
    (r"(?:^|[_\s\-])(?:versao[_\s\-]?certa|agora[_\s\-]?vai|ok|bom)(?:[_\s\-]|$)",
     "marcação informal de versão"),
    (r"\(\s*\d+\s*\)\s*$", "sufixo de duplicata do sistema, como 'TR (1)'"),
    (r"(?:^|[_\s\-])(?:rev|revisao|revisado|v)[_\s\-]?\d+\s*$",
     "número de revisão no nome"),
    (r"[_\-]\d{1,2}\s*$", "sufixo numérico solto, como 'TR_2'"),
    (r"(?:^|[_\s\-])(?:rascunho|draft|wip|teste|temp|tmp)(?:[_\s\-]|$)",
     "nome de rascunho ou temporário"),
)

_SUSPEITOS_COMPILADOS = tuple(
    (re.compile(padrao, re.IGNORECASE), motivo) for padrao, motivo in PADROES_SUSPEITOS
)


def nome_suspeito(nome: str) -> Optional[str]:
    """
    Motivo pelo qual o nome parece uma versão solta, ou None.

    Aplica-se ao radical, sem extensão, sem acento. É um SINAL para o relatório
    de organização — nunca autoriza apagar arquivo (regra 34).
    """
    radical = remover_acentos(str(nome or ""))
    ponto = radical.rfind(".")
    if ponto > 0:
        radical = radical[:ponto]
    radical = radical.strip()
    if ler_nome_historico(f"{radical}.tmp"):
        return None  # nome legítimo do histórico: TIPO_vNNN_data_hora
    for padrao, motivo in _SUSPEITOS_COMPILADOS:
        if padrao.search(radical):
            return motivo
    return None


def tipo_provavel(nome: str) -> Optional[str]:
    """
    Palpite do tipo documental a partir do nome — INDÍCIO, não conclusão.

    Devolve None quando o nome não é claro. Quem decide o tipo de um arquivo
    encontrado numa pasta antiga é o operador humano, no plano de migração.
    """
    radical = remover_acentos(str(nome or "")).upper()
    ponto = radical.rfind(".")
    if ponto > 0:
        radical = radical[:ponto]
    compacto = re.sub(r"[^A-Z0-9]+", "_", radical).strip("_")

    # Primeiro os rótulos compostos, para "AVISO_COMPLETO" não virar "AVISO".
    for tipo in sorted(TIPOS, key=len, reverse=True):
        if re.search(rf"(?:^|_){tipo}(?:_|$)", compacto):
            return tipo

    sinonimos = (
        ("AVISO_COMPLETO", r"AVISO.*COMPLET|COMPLET.*AVISO"),
        ("TR", r"TERMO_DE_REFERENCIA|TERMO_REFERENCIA"),
        ("DFD", r"FORMALIZACAO_DA_DEMANDA|DOCUMENTO_DE_FORMALIZACAO"),
        ("ETP", r"ESTUDO_TECNICO"),
        ("MAPA_DE_RISCOS", r"MAPA.*RISCO|ANALISE.*RISCO|MATRIZ.*RISCO"),
        ("PESQUISA_DE_PRECOS", r"PESQUISA.*PRECO|MAPA.*PRECO|COTACAO_MAPA"),
        ("JUSTIFICATIVA_CONTRATACAO_DIRETA", r"JUSTIFICATIVA.*(DIRETA|DISPENSA)"),
        ("AUTORIZACAO", r"AUTORIZACAO.*ABERTURA|ABERTURA.*PROCESSO"),
        ("ATA_JULGAMENTO", r"ATA.*JULGAMENTO"),
        ("HOMOLOGACAO", r"HOMOLOGA|ADJUDICA"),
        ("CONTRATO", r"^CONTRATO|TERMO_DE_CONTRATO"),
        ("ORDEM_FORNECIMENTO", r"ORDEM.*(FORNECIMENTO|SERVICO)"),
        ("TERMO_RECEBIMENTO", r"TERMO.*RECEBIMENTO|RECEBIMENTO_DEFINITIVO"),
        ("EXTRATO", r"EXTRATO"),
    )
    for tipo, padrao in sinonimos:
        if re.search(padrao, compacto):
            return tipo
    return None
