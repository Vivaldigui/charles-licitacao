"""Caminhos e constantes do auditor TCE-MG."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "TCE-MG_JULGADOS"
DEFAULT_OUTPUT = REPO_ROOT / "03_jurisprudencia" / "tce_mg" / "contratacao_direta"
RAW_REFERENCE_DIR = DEFAULT_OUTPUT / "inteiro_teor_bruto"
TEXT_DIR = DEFAULT_OUTPUT / "texto_extraido"
FICHAS_DIR = DEFAULT_OUTPUT / "fichas"
INDICES_DIR = DEFAULT_OUTPUT / "indices"
CONSOLIDATIONS_DIR = DEFAULT_OUTPUT / "consolidacoes"
REPORTS_DIR = DEFAULT_OUTPUT / "relatorios_processamento"
DATABASE_PATH = INDICES_DIR / "auditor_tcemg.sqlite3"
CATALOG_JSONL = INDICES_DIR / "catalogo_julgados.jsonl"
CATALOG_CSV = INDICES_DIR / "catalogo_julgados.csv"
ORIGINALS_MANIFEST_JSONL = INDICES_DIR / "manifesto_originais.jsonl"

TODAY = "2026-07-31"
NOT_IDENTIFIED = "Não identificado no documento"
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm", ".docx"}
DEFAULT_RELEVANCES = ("direta", "parcial")

THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "planejamento da contratação": ("planejamento da contratação", "planejamento da contratacao"),
    "documento de formalização da demanda": ("documento de formalização da demanda", "dfd"),
    "estudo técnico preliminar": ("estudo técnico preliminar", "etp"),
    "termo de referência": ("termo de referência", "termo de referencia"),
    "definição do objeto": ("definição do objeto", "definicao do objeto", "especificação do objeto"),
    "estimativa de quantitativos": ("estimativa de quantitativos", "quantitativos estimados"),
    "pesquisa de preços": ("pesquisa de preços", "pesquisa de precos", "cotação de preços"),
    "justificativa do preço": ("justificativa do preço", "justificativa de preço"),
    "escolha do fornecedor": ("escolha do fornecedor", "escolha do contratado"),
    "razão da escolha do contratado": ("razão da escolha", "razao da escolha"),
    "aviso de contratação direta": ("aviso de contratação direta", "aviso de contratacao direta"),
    "dispensa com disputa": ("dispensa com disputa", "dispensa eletrônica"),
    "dispensa sem disputa": ("dispensa sem disputa", "sem disputa"),
    "publicidade": ("publicidade", "publicação", "divulgação"),
    "pncp": ("pncp", "portal nacional de contratações públicas"),
    "habilitação": ("habilitação", "inabilitação"),
    "regularidade fiscal": ("regularidade fiscal", "certidão fiscal"),
    "qualificação técnica": ("qualificação técnica", "capacidade técnica"),
    "fracionamento de despesas": ("fracionamento", "parcelamento indevido"),
    "aferição dos limites da dispensa": ("limite da dispensa", "limites da dispensa", "art. 75, § 1"),
    "unidade gestora": ("unidade gestora",),
    "ramo de atividade": ("ramo de atividade", "cnae"),
    "objetos da mesma natureza": ("mesma natureza", "objetos de mesma natureza"),
    "emergência": ("emergência", "emergencial"),
    "urgência fabricada": ("emergência fabricada", "urgência fabricada", "falta de planejamento"),
    "inexigibilidade": ("inexigibilidade", "inviabilidade de competição"),
    "exclusividade": ("exclusividade", "fornecedor exclusivo"),
    "notória especialização": ("notória especialização", "notoria especializacao"),
    "serviços técnicos especializados": ("serviços técnicos especializados",),
    "credenciamento": ("credenciamento",),
    "sobrepreço": ("sobrepreço", "sobrepreco"),
    "superfaturamento": ("superfaturamento",),
    "execução contratual": ("execução contratual", "execucao contratual"),
    "fiscalização": ("fiscalização do contrato", "fiscal do contrato"),
    "liquidação": ("liquidação", "liquidacao"),
    "pagamento": ("pagamento",),
    "alterações contratuais": ("alteração contratual", "termo aditivo"),
    "prorrogação": ("prorrogação", "prorrogacao"),
    "responsabilização": ("responsabilização", "multa", "sanção"),
    "parecer jurídico": ("parecer jurídico", "assessoria jurídica", "controle prévio de legalidade"),
    "segregação de funções": ("segregação de funções", "segregacao de funcoes"),
    "formalização processual": ("formalização processual", "instrução processual", "processo de contratação direta"),
}
