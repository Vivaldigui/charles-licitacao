#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fontes_precos.py — Contrato comum das fontes da pesquisa de preços.

Todos os coletores (PNCP, Compras.gov, sítios/mídia, tabelas de referência,
NF-e) devolvem itens no MESMO formato, para que `cesta_precos.py` monte uma
única cesta e `normalizar_precos.py` faça a estatística comum.

O que este módulo concentra:
  - os PARÂMETROS do art. 4º da Portaria 03/2024 (I, II, III, V) e os tipos de
    fonte, como constantes — nunca strings soltas espalhadas pelo código;
  - `item_fonte()`: o dicionário-base de um item da cesta (superset do antigo
    `_item_base()` de cesta_precos.py, sem remover nenhum campo);
  - `http_get_json()` / `http_get_texto()`: acesso HTTP que **nunca levanta
    exceção** e sempre devolve uma EVIDÊNCIA estruturada (URL, parâmetros,
    timestamp, status HTTP, erro), para rastreabilidade;
  - `mascarar_dados_pessoais()`: CPF e e-mail que apareçam na fonte mas não
    sejam necessários ao relatório são mascarados antes de qualquer gravação.

REGRAS (07_checklists/regras-pesquisa-de-precos.md):
  - Campo ausente na fonte vira "" — nunca dado inventado.
  - Token/chave de API JAMAIS entra na evidência ou no relatório.
  - Comparabilidade é juízo humano: o coletor deixa `[VALIDAÇÃO HUMANA]`.
  - Indisponibilidade de fonte externa vira erro registrado, nunca dado fictício.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Parâmetros do art. 4º da Portaria 03/2024
# ---------------------------------------------------------------------------
PARAM_I = "I"
PARAM_II = "II"
PARAM_III = "III"
PARAM_V = "V"

# O inciso IV (pesquisa direta com fornecedores) NÃO é automatizado por decisão
# de projeto: depende de solicitação formal, propostas assinadas e juízo do
# agente (art. 4º, §2º). Fica registrado aqui só para não ser confundido com
# esquecimento.
PARAM_IV_NAO_AUTOMATIZADO = "IV"

PARAMETROS_PORTARIA: dict[str, str] = {
    PARAM_I: "Sistemas oficiais de governo / composição de custos unitários (art. 4º, I)",
    PARAM_II: "Contratações similares da Administração Pública (art. 4º, II)",
    PARAM_III: "Mídia especializada, tabela de referência e sítios eletrônicos (art. 4º, III)",
    PARAM_V: "Notas fiscais eletrônicas (art. 4º, V)",
}

# Tipos de fonte (metadado; não substitui a análise de comparabilidade).
FONTE_SISTEMA_OFICIAL = "sistema_oficial"
FONTE_CONTRATACAO_SIMILAR = "contratacao_similar"
FONTE_MIDIA_ESPECIALIZADA = "midia_especializada"
FONTE_SITIO_ESPECIALIZADO = "sitio_especializado"
FONTE_DOMINIO_AMPLO = "dominio_amplo"
FONTE_TABELA_REFERENCIA = "tabela_referencia"
FONTE_NOTA_FISCAL = "nota_fiscal_eletronica"
FONTE_MANUAL = "manual"

TIPOS_FONTE_PARAM_III = (
    FONTE_MIDIA_ESPECIALIZADA,
    FONTE_SITIO_ESPECIALIZADO,
    FONTE_DOMINIO_AMPLO,
    FONTE_TABELA_REFERENCIA,
)

MARCA_VALIDACAO = "[VALIDAÇÃO HUMANA]"

# Subcritérios de comparabilidade (art. 3º da Portaria 03/2024). Ficam aqui
# porque valem para TODAS as fontes; `cesta_precos.py` reexporta a lista.
CRITERIOS_COMPARABILIDADE = [
    ("mesma_especificacao", "Mesma especificação"),
    ("mesma_unidade", "Mesma unidade"),
    ("quantidade_mesma_ordem", "Quantidade na mesma ordem"),
    ("data_ate_1_ano", "Data até 1 ano"),
    ("mesma_regiao", "Mesma região"),
    ("condicoes_equivalentes", "Condições equivalentes (frete/instalação/garantia)"),
]

USER_AGENT_PADRAO = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Parâmetros de URL cujo valor nunca pode ser gravado na evidência.
PARAMETROS_SENSIVEIS = {
    "key", "api_key", "apikey", "chave", "chave-api-dados", "token",
    "access_token", "secret", "password", "senha",
}
CABECALHOS_SENSIVEIS = {
    "authorization", "chave-api-dados", "x-api-key", "api-key", "cookie",
}


# ---------------------------------------------------------------------------
# Tempo
# ---------------------------------------------------------------------------
def agora_iso() -> str:
    """Data/hora atual em ISO-8601 COM timezone (exigência do art. 4º, III)."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Item da cesta — contrato comum
# ---------------------------------------------------------------------------
def bloco_atualizacao(
    *,
    aplicada: bool = False,
    indice: Optional[str] = None,
    fonte: Optional[str] = None,
    data_base: Optional[str] = None,
    data_final: Optional[str] = None,
    fator: Optional[float] = None,
    formula: Optional[str] = None,
    justificativa: Optional[str] = None,
) -> dict:
    """Bloco de atualização monetária (art. 4º, I/II e §3º).

    O software NÃO escolhe índice nem corrige preço sozinho. Este bloco só
    documenta uma atualização DECLARADA pelo responsável, com todos os dados.
    """
    return {
        "aplicada": bool(aplicada),
        "indice": indice,
        "fonte": fonte,
        "data_base": data_base,
        "data_final": data_final,
        "fator": fator,
        "formula": formula,
        "justificativa": justificativa,
    }


def item_fonte(**campos: Any) -> dict:
    """Dicionário-base de um item da cesta, comum a todas as fontes.

    Mantém integralmente os campos do formato antigo (`fonte`, `orgao`,
    `objeto_encontrado`, `modalidade`, `data`, `quantidade`, `unidade`,
    `valor_unitario`, `valor_total`, `link`, `comparabilidade`, `data_acesso`,
    `situacao`, `observacao`, `comparabilidade_grau` + subcritérios) e
    acrescenta os campos opcionais dos novos parâmetros.
    """
    item: dict[str, Any] = {
        # --- campos históricos (não remover: exemplos e modo manual dependem) ---
        "fonte": "",
        "orgao": "",
        "objeto_encontrado": "",
        "modalidade": "",
        "data": "",
        "quantidade": "",
        "unidade": "",
        "valor_unitario": "",
        "valor_total": "",
        "link": "",
        "comparabilidade": "",
        "data_acesso": "",
        "situacao": "",
        "observacao": "",
        "comparabilidade_grau": "",
        # --- ampliação do contrato (novos parâmetros) ---
        "parametro_portaria": "",
        "fonte_tipo": "",
        "codigo_item": "",
        "marca": "",
        "fornecedor": "",
        "municipio": "",
        "uf": "",
        "escopo_fonte": "",
        "identificador_registro": "",
        "data_publicacao_fonte": "",
        "atualizacao": bloco_atualizacao(),
        "evidencia": {},
    }
    for chave, _rotulo in CRITERIOS_COMPARABILIDADE:
        item[chave] = MARCA_VALIDACAO
    item.update(campos)
    return item


# ---------------------------------------------------------------------------
# Privacidade — só o necessário à pesquisa de preços
# ---------------------------------------------------------------------------
_RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def mascarar_dados_pessoais(valor: Any) -> Any:
    """Mascara CPF e e-mail em texto vindo da fonte.

    CNPJ e razão social de fornecedor NÃO são mascarados: identificam a
    contratação e são necessários à rastreabilidade do preço.
    """
    if not isinstance(valor, str):
        return valor
    texto = _RE_CPF.sub("[CPF SUPRIMIDO]", valor)
    return _RE_EMAIL.sub("[E-MAIL SUPRIMIDO]", texto)


def limpar_registro(registro: dict, campos_permitidos: tuple[str, ...]) -> dict:
    """Mantém apenas os campos necessários e mascara dados pessoais residuais."""
    saida = {}
    for campo in campos_permitidos:
        if campo in registro:
            saida[campo] = mascarar_dados_pessoais(registro[campo])
    return saida


# ---------------------------------------------------------------------------
# HTTP com evidência — nunca levanta exceção
# ---------------------------------------------------------------------------
def url_sem_segredo(url: str) -> str:
    """Remove o VALOR de parâmetros sensíveis da URL antes de registrá-la."""
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError:
        return url
    if not partes.query:
        return url
    pares = urllib.parse.parse_qsl(partes.query, keep_blank_values=True)
    limpos = [
        (chave, "[OMITIDO]" if chave.lower() in PARAMETROS_SENSIVEIS else valor)
        for chave, valor in pares
    ]
    return urllib.parse.urlunsplit(
        (partes.scheme, partes.netloc, partes.path, urllib.parse.urlencode(limpos), partes.fragment)
    )


def montar_url(base: str, parametros: dict[str, Any]) -> str:
    """Monta URL descartando parâmetros vazios (None/'')."""
    limpos = {k: v for k, v in parametros.items() if v not in (None, "")}
    if not limpos:
        return base
    return f"{base}?{urllib.parse.urlencode(limpos)}"


def nova_evidencia(fonte: str, url: str, *, parametros: Optional[dict] = None) -> dict:
    """Evidência de uma chamada HTTP, sem segredo algum."""
    return {
        "fonte": fonte,
        "url_chamada": url_sem_segredo(url),
        "parametros": {
            k: ("[OMITIDO]" if k.lower() in PARAMETROS_SENSIVEIS else v)
            for k, v in (parametros or {}).items()
        },
        "data_hora": agora_iso(),
        "status_http": None,
        "erro": None,
        "identificador_registro": "",
    }


def _requisicao(url: str, cabecalhos: Optional[dict], timeout: int):
    headers = {"User-Agent": USER_AGENT_PADRAO, "Accept": "application/json"}
    headers.update(cabecalhos or {})
    return urllib.request.Request(url, headers=headers)


def http_get(
    url: str,
    *,
    fonte: str,
    cabecalhos: Optional[dict] = None,
    parametros: Optional[dict] = None,
    timeout: int = 30,
    limite_bytes: int = 5_000_000,
) -> tuple[Optional[str], dict]:
    """GET que devolve (corpo, evidência). Falha externa NUNCA levanta exceção.

    A evidência guarda URL chamada (sem segredo), parâmetros, timestamp, status
    HTTP e o erro ocorrido — o que a Portaria exige para auditabilidade.
    """
    evidencia = nova_evidencia(fonte, url, parametros=parametros)
    try:
        with urllib.request.urlopen(_requisicao(url, cabecalhos, timeout), timeout=timeout) as resp:
            evidencia["status_http"] = getattr(resp, "status", None) or resp.getcode()
            bruto = resp.read(limite_bytes + 1)
            if len(bruto) > limite_bytes:
                evidencia["erro"] = (
                    f"Resposta maior que o limite de {limite_bytes} bytes; conteúdo descartado "
                    "para não truncar dado pela metade. Consultar manualmente."
                )
                return None, evidencia
            encoding = resp.headers.get_content_charset() or "utf-8"
            return bruto.decode(encoding, errors="replace"), evidencia
    except urllib.error.HTTPError as e:
        evidencia["status_http"] = e.code
        evidencia["erro"] = f"HTTP {e.code} em {fonte}: {e.reason}."
    except urllib.error.URLError as e:
        evidencia["erro"] = f"Falha de rede em {fonte}: {e.reason}."
    except TimeoutError:
        evidencia["erro"] = f"Tempo esgotado ({timeout}s) em {fonte}."
    except Exception as e:  # noqa: BLE001 — nenhuma fonte pode derrubar a pesquisa
        evidencia["erro"] = f"Erro inesperado em {fonte}: {e}"
    return None, evidencia


def http_get_json(
    url: str,
    *,
    fonte: str,
    cabecalhos: Optional[dict] = None,
    parametros: Optional[dict] = None,
    timeout: int = 30,
) -> tuple[Any, dict]:
    """GET + parse JSON. Devolve (dados|None, evidência)."""
    corpo, evidencia = http_get(
        url, fonte=fonte, cabecalhos=cabecalhos, parametros=parametros, timeout=timeout
    )
    if corpo is None:
        return None, evidencia
    try:
        return json.loads(corpo), evidencia
    except json.JSONDecodeError as e:
        evidencia["erro"] = f"Resposta de {fonte} não é JSON válido: {e}"
        return None, evidencia


def instrucao_consulta_manual(fonte: str, url: str, motivo: str) -> str:
    """Texto padrão quando a automação não pôde consultar a fonte."""
    return (
        f"Fonte {fonte} não consultada automaticamente ({motivo}). "
        f"Consulta manual: {url_sem_segredo(url)} — registrar data/hora de acesso "
        "e anexar o comprovante ao processo. Não preencher preço sem o documento."
    )


# ---------------------------------------------------------------------------
# Estatística de um conjunto de preços de UMA fonte oficial
# ---------------------------------------------------------------------------
def resumo_estatistico(precos: list[float], *, total_registros: int) -> dict:
    """Resumo exigido do parâmetro I: n, menor, maior, média, mediana, válidos.

    Importa `normalizar_precos` tardiamente para manter este módulo sem
    dependências internas obrigatórias.
    """
    from normalizar_precos import estatisticas

    stats = estatisticas(precos)
    return {
        "registros_localizados": total_registros,
        "registros_validos": stats["n"],
        "menor": stats["menor"],
        "maior": stats["maior"],
        "media": stats["media"],
        "mediana": stats["mediana"],
        "alerta_minimo": stats["alerta_minimo"],
    }
