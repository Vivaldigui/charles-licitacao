#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manifesto.py — núcleo comum: onde mora o processo e como ele se descreve.

Este módulo responde a três perguntas e não faz mais nada:

1. **Onde fica o processo?** Em `CHARLES_PROCESSOS_DIR`, quando configurado —
   fora do repositório, como manda o item 3 do escopo. Sem a variável, cai em
   `08_processos_em_andamento/`, que num repositório público só pode guardar
   exemplo fictício (ver `seguranca_repositorio.py`).
2. **Qual é o estado do processo?** `00_CONTROLE/PROCESSO.json` (item 11) e
   `00_CONTROLE/DOCUMENTOS.json` (item 10).
3. **O que aconteceu?** `00_CONTROLE/LOG_DOCUMENTAL.jsonl` (item 13), que só
   cresce.

As pastas nascem sob demanda (item 4: "não criar pastas vazias
desnecessariamente"): só o esqueleto de controle é criado no início.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))

from nomes_arquivos import (  # noqa: E402
    AREA_ASSINADOS,
    AREA_CONTROLE,
    AREA_ELABORACAO,
    AREA_EXECUCAO,
    AREA_EXTERNOS,
    AREA_HISTORICO,
    AREA_OFICIAIS,
    AREA_PUBLICACOES,
    AREA_QUARENTENA,
    AREA_TEMPORARIOS,
    CATEGORIAS_EXTERNAS,
    nome_canonico,
    obter_tipo,
    sanitizar_nome_processo,
)

SCHEMA_VERSION = "1.0"
RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]
PASTA_PADRAO_PROCESSOS = RAIZ_REPOSITORIO / "08_processos_em_andamento"
VARIAVEL_PROCESSOS = "CHARLES_PROCESSOS_DIR"

ARQUIVO_PROCESSO = "PROCESSO.json"
ARQUIVO_DOCUMENTOS = "DOCUMENTOS.json"
ARQUIVO_PAINEL = "PAINEL_PROCESSO.md"
ARQUIVO_LOG = "LOG_DOCUMENTAL.jsonl"
ARQUIVO_PENDENCIAS = "PENDENCIAS.md"


# --------------------------------------------------------------------------- #
# Ciclo de vida (item 6)
# --------------------------------------------------------------------------- #

STATUS = (
    "rascunho",
    "em_elaboracao",
    "em_revisao",
    "aprovado",
    "assinado",
    "publicado",
    "substituido",
    "cancelado",
    "arquivado",
)

#: Estados em que o documento NÃO pode ser sobrescrito (item 6 e regra 34).
STATUS_IMUTAVEIS = frozenset({"assinado", "publicado"})

#: Estados que exigem motivo e responsável para qualquer alteração (item 6).
STATUS_PROTEGIDOS = frozenset({"aprovado"})

#: Estados em que o documento ainda circula livremente.
STATUS_EDITAVEIS = frozenset({"rascunho", "em_elaboracao", "em_revisao"})

#: Promoções admitidas (item 16). O que não está aqui exige decisão humana.
PROMOCOES: dict[str, frozenset[str]] = {
    "rascunho": frozenset({"em_elaboracao", "em_revisao", "cancelado"}),
    "em_elaboracao": frozenset({"em_revisao", "aprovado", "cancelado"}),
    "em_revisao": frozenset({"aprovado", "em_elaboracao", "cancelado"}),
    "aprovado": frozenset({"assinado", "em_revisao", "cancelado"}),
    "assinado": frozenset({"publicado", "cancelado"}),
    "publicado": frozenset({"arquivado"}),
    "substituido": frozenset(),
    "cancelado": frozenset(),
    "arquivado": frozenset(),
}

ACOES = (
    "processo_criado",
    "documento_importado",
    "documento_gerado",
    "documento_substituido",
    "documento_promovido",
    "documento_assinado",
    "documento_publicado",
    "documento_retificado",
    "documento_arquivado",
    "documento_externo_classificado",
    "duplicado_descartado",
    "arquivo_colocado_em_quarentena",
    "erro_de_validacao",
    "restauracao_de_versao",
    "geracao_sem_alteracao",
    "lock_recuperado",
    "rollback_executado",
    "temporarios_limpos",
    "processo_migrado",
)


class ProcessoInexistente(FileNotFoundError):
    """A pasta indicada não é um processo gerido pelo Charles."""


class OperacaoBloqueada(RuntimeError):
    """A operação fere uma regra inegociável (item 34) e não será executada."""


# --------------------------------------------------------------------------- #
# Localização dos processos (item 3)
# --------------------------------------------------------------------------- #

def raiz_processos(explicita: Optional[Path | str] = None) -> Path:
    """
    Diretório-base dos processos.

    Precedência: caminho passado > `CHARLES_PROCESSOS_DIR` > pasta do
    repositório. A variável de ambiente é o caminho recomendado para processos
    reais: mantém documento com dado pessoal fora do controle de versão.
    """
    if explicita:
        return Path(explicita).expanduser().resolve()
    do_ambiente = os.environ.get(VARIAVEL_PROCESSOS, "").strip()
    if do_ambiente:
        return Path(do_ambiente).expanduser().resolve()
    return PASTA_PADRAO_PROCESSOS.resolve()


def processos_em_diretorio_externo() -> bool:
    return bool(os.environ.get(VARIAVEL_PROCESSOS, "").strip())


def caminho_processo(
    identificador: str, base: Optional[Path | str] = None
) -> Path:
    """
    Resolve o processo por caminho direto ou por identificador de pasta.

    Aceita "PA 031/2026", "PA_031_2026" e um caminho absoluto para a pasta.
    """
    bruto = str(identificador).strip()
    candidato = Path(bruto).expanduser()
    if candidato.is_absolute() or os.sep in bruto or "/" in bruto:
        if (candidato / AREA_CONTROLE).is_dir() or candidato.is_dir():
            return candidato.resolve()

    raiz = raiz_processos(base)
    nome = sanitizar_nome_processo(bruto)
    exato = raiz / nome
    if (exato / AREA_CONTROLE).is_dir() or not raiz.is_dir():
        return exato

    # "PA_031_2026" também encontra "PA_031_2026_MATERIAL_DE_LIMPEZA" — desde que
    # a correspondência seja única. Havendo mais de um, quem escolhe é o operador.
    parecidos = [
        pasta for pasta in sorted(raiz.iterdir())
        if pasta.is_dir() and pasta.name.startswith(f"{nome}_")
        and (pasta / AREA_CONTROLE).is_dir()
    ]
    if len(parecidos) == 1:
        return parecidos[0].resolve()
    if len(parecidos) > 1:
        opcoes = ", ".join(p.name for p in parecidos)
        raise ProcessoInexistente(
            f"'{identificador}' corresponde a mais de um processo: {opcoes}. "
            f"Informe o identificador completo."
        )
    return exato


# --------------------------------------------------------------------------- #
# Estrutura (item 4)
# --------------------------------------------------------------------------- #

#: Esqueleto mínimo criado no início. O restante nasce com o primeiro documento.
ESTRUTURA_MINIMA = (AREA_CONTROLE, AREA_ELABORACAO, AREA_TEMPORARIOS)

#: Estrutura completa prevista no item 4 — referência para painel e validação.
ESTRUTURA_COMPLETA: tuple[str, ...] = (
    AREA_CONTROLE,
    AREA_ELABORACAO,
    *(f"{AREA_OFICIAIS}/{f}" for f in
      ("FASE_PREPARATORIA", "SELECAO_FORNECEDOR", "CONTRATACAO", "EXECUCAO")),
    *(f"{AREA_EXTERNOS}/{p}" for p in CATEGORIAS_EXTERNAS.values()),
    *(f"{AREA_PUBLICACOES}/{p}" for p in
      ("AVISOS", "EXTRATOS", "PNCP", "DIARIO_OFICIAL", "PACOTES")),
    *(f"{AREA_ASSINADOS}/{p}" for p in
      ("DFD", "ETP", "TR", "AVISO", "CONTRATO", "OUTROS")),
    *(f"{AREA_EXECUCAO}/{p}" for p in
      ("ORDENS", "NOTAS_FISCAIS", "RECEBIMENTOS", "RELATORIOS_FISCAL",
       "PAGAMENTOS", "OCORRENCIAS")),
    *(f"{AREA_HISTORICO}/{p}" for p in
      ("DFD", "ETP", "TR", "PESQUISA_DE_PRECOS", "AVISO", "CONTRATO", "OUTROS")),
    AREA_QUARENTENA,
    AREA_TEMPORARIOS,
)

#: Áreas onde só pode existir o arquivo atual de cada tipo (item 1).
AREAS_CORRENTES = (AREA_ELABORACAO, AREA_OFICIAIS)


# --------------------------------------------------------------------------- #
# Processo
# --------------------------------------------------------------------------- #

@dataclass
class Processo:
    """Uma pasta de processo e os três arquivos que a descrevem."""

    raiz: Path

    # -- abertura ---------------------------------------------------------- #

    @classmethod
    def abrir(
        cls, identificador: str, base: Optional[Path | str] = None
    ) -> "Processo":
        raiz = caminho_processo(identificador, base)
        if not (raiz / AREA_CONTROLE / ARQUIVO_PROCESSO).exists():
            raise ProcessoInexistente(
                f"Não encontrei {AREA_CONTROLE}/{ARQUIVO_PROCESSO} em {raiz}. "
                f"Crie o processo com iniciar_processo.py ou migre a pasta "
                f"antiga com migrar_processo.py."
            )
        return cls(raiz=raiz.resolve())

    @classmethod
    def criar(cls, raiz: Path | str) -> "Processo":
        raiz = Path(raiz)
        for pasta in ESTRUTURA_MINIMA:
            (raiz / pasta).mkdir(parents=True, exist_ok=True)
        return cls(raiz=raiz.resolve())

    # -- caminhos ---------------------------------------------------------- #

    @property
    def controle(self) -> Path:
        return self.raiz / AREA_CONTROLE

    @property
    def arquivo_processo(self) -> Path:
        return self.controle / ARQUIVO_PROCESSO

    @property
    def arquivo_documentos(self) -> Path:
        return self.controle / ARQUIVO_DOCUMENTOS

    @property
    def arquivo_painel(self) -> Path:
        return self.controle / ARQUIVO_PAINEL

    @property
    def arquivo_log(self) -> Path:
        return self.controle / ARQUIVO_LOG

    @property
    def arquivo_pendencias(self) -> Path:
        return self.controle / ARQUIVO_PENDENCIAS

    @property
    def temporarios(self) -> Path:
        return self.raiz / AREA_TEMPORARIOS

    @property
    def quarentena(self) -> Path:
        return self.raiz / AREA_QUARENTENA

    @property
    def identificador(self) -> str:
        return self.raiz.name

    def garantir(self, *partes: str) -> Path:
        """Cria a subpasta sob demanda e devolve o caminho."""
        destino = self.raiz.joinpath(*partes)
        destino.mkdir(parents=True, exist_ok=True)
        return destino

    def relativo(self, caminho: Path | str) -> str:
        """Caminho relativo à raiz, com barra normal — é o que vai no manifesto."""
        caminho = Path(caminho)
        try:
            return caminho.resolve().relative_to(self.raiz).as_posix()
        except ValueError:
            return caminho.as_posix()

    def absoluto(self, relativo: str) -> Path:
        return self.raiz / str(relativo).replace("\\", "/")

    # -- área corrente de cada documento (itens 5, 6 e 7) ------------------- #

    def area_corrente(self, tipo: str, status: str) -> Path:
        """
        Onde vive a representação editável neste estado.

        Enquanto o documento se move (rascunho, elaboração, revisão) ele fica em
        `01_EM_ELABORACAO/`. Aprovado, passa a documento oficial da fase. Uma vez
        assinado ou publicado, ele NÃO volta: a peça oficial permanece onde está
        e as representações assinada e publicada vão para as áreas próprias.
        """
        descricao = obter_tipo(tipo)
        if status in STATUS_EDITAVEIS:
            return self.raiz / AREA_ELABORACAO
        return self.raiz / AREA_OFICIAIS / descricao.fase

    def caminho_corrente(
        self, tipo: str, status: str, extensao: str = ".docx"
    ) -> Path:
        return self.area_corrente(tipo, status) / nome_canonico(tipo, extensao)

    def pasta_historico(self, tipo: str) -> Path:
        return self.raiz / AREA_HISTORICO / obter_tipo(tipo).pasta_historico

    def pasta_assinados(self, tipo: str) -> Path:
        return self.raiz / AREA_ASSINADOS / obter_tipo(tipo).pasta_assinados

    # -- PROCESSO.json (item 11) ------------------------------------------- #

    def ler_processo(self) -> dict[str, Any]:
        return _ler_json(self.arquivo_processo, padrao={})

    def ler_documentos(self) -> dict[str, Any]:
        dados = _ler_json(self.arquivo_documentos, padrao=None)
        if dados is None:
            dados = manifesto_vazio(self.ler_processo().get("processo_id", self.identificador))
        dados.setdefault("documentos", {})
        dados.setdefault("documentos_externos", [])
        return dados

    def documento(self, tipo: str) -> Optional[dict[str, Any]]:
        return self.ler_documentos()["documentos"].get(obter_tipo(tipo).tipo)

    # -- log (item 13) ----------------------------------------------------- #

    def eventos(self) -> Iterator[dict[str, Any]]:
        if not self.arquivo_log.exists():
            return iter(())
        def _gerar() -> Iterator[dict[str, Any]]:
            with open(self.arquivo_log, encoding="utf-8") as arquivo:
                for linha in arquivo:
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        yield json.loads(linha)
                    except json.JSONDecodeError:
                        yield {"acao": "linha_ilegivel", "conteudo": linha}
        return _gerar()


# --------------------------------------------------------------------------- #
# Estruturas de dados
# --------------------------------------------------------------------------- #

def preparar_console() -> None:
    """
    Deixa o terminal aceitar o texto dos relatórios.

    O console do Windows costuma vir em cp1252, que não tem "→" nem "×". Sem
    isto, um relatório perfeitamente correto derruba o comando com
    `UnicodeEncodeError` — e o operador conclui que a operação falhou, quando na
    verdade ela terminou e só a impressão quebrou. `errors="replace"` prefere um
    caractere trocado a uma execução perdida.
    """
    for fluxo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(fluxo, "reconfigure", None)
        if reconfigurar is None:
            continue
        try:
            reconfigurar(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - fluxo redirecionado
            pass


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def manifesto_vazio(processo_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "processo_id": processo_id,
        "atualizado_em": agora(),
        "documentos": {},
        "documentos_externos": [],
    }


def evento(
    acao: str,
    *,
    documento: Optional[str] = None,
    versao: Optional[int] = None,
    arquivo: Optional[str] = None,
    hash_sha256: Optional[str] = None,
    responsavel: str = "Charles",
    motivo: str = "",
    **extras: Any,
) -> dict[str, Any]:
    """
    Monta um evento do log. Ação fora da lista é erro de programação, não dado.
    """
    if acao not in ACOES:
        raise ValueError(f"Ação de log desconhecida: {acao!r}. Previstas: {ACOES}")
    registro: dict[str, Any] = {
        "data": agora(),
        "acao": acao,
        "documento": documento,
        "versao": versao,
        "arquivo": arquivo,
        "hash": hash_sha256,
        "responsavel": responsavel or "Charles",
        "motivo": motivo or "",
    }
    registro.update(extras)
    return registro


def linha_log(registro: dict[str, Any]) -> str:
    return json.dumps(registro, ensure_ascii=False)


def promocao_permitida(atual: str, novo: str) -> bool:
    return novo in PROMOCOES.get(atual, frozenset())


def validar_status(status: str) -> str:
    if status not in STATUS:
        raise ValueError(f"Status desconhecido: {status!r}. Previstos: {STATUS}")
    return status


# --------------------------------------------------------------------------- #
# Leitura auxiliar
# --------------------------------------------------------------------------- #

def _ler_json(caminho: Path, padrao: Any) -> Any:
    if not caminho.exists():
        return padrao
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise OperacaoBloqueada(
            f"{caminho} está corrompido ({erro}). Corrija ou restaure o arquivo "
            f"antes de qualquer operação — o Charles não sobrescreve manifesto "
            f"ilegível."
        ) from erro


RE_NUMERO_PROCESSO = re.compile(
    r"\b(?:PA|SC|SOLICITA[ÇC][ÃA]O|PROCESSO|DISPENSA|PROC\.?)\s*"
    r"n?[ºo°]?\s*(\d{1,5})\s*[/\-.]\s*(\d{4})\b",
    re.IGNORECASE,
)


def numeros_de_processo(texto: str) -> set[str]:
    """
    Pares número/ano citados num texto — insumo do item 21 (documento de outro
    processo). É indício: número citado não prova pertencimento.
    """
    return {
        f"{int(numero):03d}/{ano}"
        for numero, ano in RE_NUMERO_PROCESSO.findall(texto or "")
    }
