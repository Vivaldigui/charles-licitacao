#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrar_processo.py — "Charles, organize a pasta antiga sem apagar nada".

Itens 23, 24 e 33 do escopo. Recebe uma pasta poluída — com `TR.docx`,
`TR_final.docx`, `Cópia de TR.docx`, propostas soltas, PDFs de outro processo e
sobras de script — e produz **primeiro um plano**, nunca uma mudança.

    # 1. planejar (padrão): não move nada
    python scripts/gestao_documental/migrar_processo.py \
      --origem "pasta_antiga" --destino "PA_031_2026" --somente-planejar

    # 2. executar o plano conferido
    python scripts/gestao_documental/migrar_processo.py \
      --origem "pasta_antiga" --destino "PA_031_2026" --executar --plano plano.json

Três decisões que definem o comportamento:

* **a pasta de origem é preservada intacta.** A migração COPIA. A origem
  continua sendo o backup até que um humano valide o resultado (item 24). Nada
  é apagado por este script, em nenhum modo.
* **versão atual escolhida por data de modificação, e dito em voz alta.** Nome
  não decide nada: "TR_final.docx" pode ser mais antigo que "TR.docx". Quando
  duas candidatas empatam, a migração **bloqueia** e pede escolha humana em vez
  de chutar.
* **o que não se consegue classificar vai para `98_QUARENTENA/`**, não para o
  lixo e não para a pasta oficial.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from classificar_documento import classificar  # noqa: E402
from hashes import hash_conteudo, sha256_arquivo  # noqa: E402
from manifesto import (  # noqa: E402
    AREA_EXTERNOS,
    AREA_QUARENTENA,
    AREA_TRABALHO,
    OperacaoBloqueada,
    Processo,
    agora,
    evento,
    linha_log,
    manifesto_vazio,
    preparar_console,
)
from nomes_arquivos import (  # noqa: E402
    CATEGORIAS_EXTERNAS,
    nome_externo,
    nome_canonico,
    nome_historico,
    material_de_trabalho,
    obter_tipo,
    sanitizar_nome_arquivo,
    nome_suspeito,
    tipo_provavel,
)
from transacoes import Transacao  # noqa: E402

STATUS_PLANO = "PLANO GERADO — AGUARDANDO CONFIRMAÇÃO"
STATUS_BLOQUEADO = "BLOQUEADO POR AMBIGUIDADE"
STATUS_CONCLUIDA = "MIGRAÇÃO CONCLUÍDA"
STATUS_RESSALVAS = "MIGRAÇÃO CONCLUÍDA COM RESSALVAS"
STATUS_ROLLBACK = "ROLLBACK EXECUTADO"

EXTENSOES_TEMPORARIAS = {".tmp", ".temp", ".bak", ".part", ".crdownload", ".~lock"}
PREFIXOS_TEMPORARIOS = ("~$", ".~")
EXTENSOES_EDITAVEIS = {".docx", ".docm", ".odt", ".doc", ".rtf"}


@dataclass
class ItemInventario:
    origem: str
    nome: str
    tamanho: int
    modificado_em: str
    hash_sha256: str
    tipo_provavel: Optional[str] = None
    nome_suspeito: Optional[str] = None
    categoria_externa: Optional[str] = None
    confianca: str = "baixa"
    temporario: bool = False
    processos_citados: list[str] = field(default_factory=list)
    outro_processo: bool = False
    material_trabalho: Optional[str] = None


@dataclass
class Movimento:
    origem: str
    destino: str
    natureza: str  # documento_atual | versao_historica | externo |
                   # material_trabalho | quarentena
    tipo: Optional[str] = None
    versao: Optional[int] = None
    motivo: str = ""


@dataclass
class PlanoMigracao:
    origem: str
    destino: str
    gerado_em: str = field(default_factory=agora)
    status: str = STATUS_PLANO
    total_arquivos: int = 0
    inventario: list[ItemInventario] = field(default_factory=list)
    movimentos: list[Movimento] = field(default_factory=list)
    duplicados_exatos: list[dict[str, Any]] = field(default_factory=list)
    ambiguidades: list[str] = field(default_factory=list)
    pendencias_humanas: list[str] = field(default_factory=list)
    preservados: list[str] = field(default_factory=list)

    def como_dicionario(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Inventário
# --------------------------------------------------------------------------- #

def _temporario(caminho: Path) -> bool:
    return (
        caminho.suffix.lower() in EXTENSOES_TEMPORARIAS
        or caminho.name.startswith(PREFIXOS_TEMPORARIOS)
    )


def inventariar(origem: Path, numero_processo: Optional[str]) -> list[ItemInventario]:
    itens: list[ItemInventario] = []
    for caminho in sorted(origem.rglob("*")):
        if not caminho.is_file() or "__pycache__" in caminho.parts:
            continue
        relativo = caminho.relative_to(origem)
        motivo_trabalho = material_de_trabalho(relativo)
        # Evidência de pesquisa não é documento externo: poupa-se a extração de
        # texto e a heurística de fornecedor/data, que só produziriam pendência
        # inútil sobre um JSON que o próprio Charles gravou.
        analise = (
            classificar(caminho, numero_processo=numero_processo)
            if not motivo_trabalho
            else None
        )
        estatisticas = caminho.stat()
        item = ItemInventario(
            origem=str(relativo),
            nome=caminho.name,
            tamanho=estatisticas.st_size,
            modificado_em=datetime.fromtimestamp(estatisticas.st_mtime).isoformat(timespec="seconds"),
            hash_sha256=sha256_arquivo(caminho),
            tipo_provavel=tipo_provavel(caminho.name),
            nome_suspeito=nome_suspeito(caminho.name),
            confianca=analise.confianca if analise else "baixa",
            temporario=_temporario(caminho),
            processos_citados=analise.processos_citados if analise else [],
            outro_processo=bool(analise.alertas) if analise else False,
            material_trabalho=motivo_trabalho,
        )
        # Um arquivo editável com tipo reconhecido é peça do Charles; material de
        # trabalho fica onde está; o resto, tratado como externo, cai na
        # classificação heurística.
        if item.tipo_provavel and caminho.suffix.lower() in EXTENSOES_EDITAVEIS:
            item.categoria_externa = None
        elif motivo_trabalho:
            item.categoria_externa = None
        else:
            item.categoria_externa = analise.categoria
            if analise.confianca == "baixa":
                item.categoria_externa = None
        itens.append(item)
    return itens


# --------------------------------------------------------------------------- #
# Planejamento
# --------------------------------------------------------------------------- #

def planejar(
    origem: Path | str,
    destino_identificador: str,
    *,
    numero_processo: Optional[str] = None,
    escolhas: Optional[dict[str, str]] = None,
    base: Optional[Path | str] = None,
) -> PlanoMigracao:
    """Monta o plano de reorganização. Não toca em arquivo nenhum."""
    origem = Path(origem).resolve()
    if not origem.is_dir():
        raise FileNotFoundError(f"Pasta de origem não encontrada: {origem}")

    escolhas = {k.upper(): v for k, v in (escolhas or {}).items()}
    plano = PlanoMigracao(origem=str(origem), destino=destino_identificador)
    itens = inventariar(origem, numero_processo)
    plano.inventario = itens
    plano.total_arquivos = len(itens)

    # -- duplicados exatos: fica um, os outros vão para quarentena --------- #
    por_hash: dict[str, list[ItemInventario]] = defaultdict(list)
    for item in itens:
        por_hash[item.hash_sha256].append(item)
    descartaveis: set[str] = set()
    for digest, grupo in sorted(por_hash.items()):
        if len(grupo) > 1:
            mantido = min(grupo, key=lambda i: (len(i.origem), i.origem))
            plano.duplicados_exatos.append({
                "hash_sha256": digest,
                "mantido": mantido.origem,
                "copias": [i.origem for i in grupo if i is not mantido],
            })
            descartaveis.update(i.origem for i in grupo if i is not mantido)

    # -- agrupamento por tipo documental ----------------------------------- #
    por_tipo: dict[str, list[ItemInventario]] = defaultdict(list)
    externos: list[ItemInventario] = []
    trabalho: list[ItemInventario] = []
    quarentena: list[ItemInventario] = []

    for item in itens:
        if item.origem in descartaveis:
            quarentena.append(item)
            plano.pendencias_humanas.append(
                f"cópia exata de outro arquivo: {item.origem} (mantido "
                f"{[d['mantido'] for d in plano.duplicados_exatos if item.origem in d['copias']][0]})"
            )
            continue
        if item.temporario:
            quarentena.append(item)
            continue
        if item.outro_processo:
            quarentena.append(item)
            plano.pendencias_humanas.append(
                f"parece pertencer a outro processo ({', '.join(item.processos_citados)}): "
                f"{item.origem}"
            )
            continue
        if item.tipo_provavel and Path(item.nome).suffix.lower() in EXTENSOES_EDITAVEIS:
            por_tipo[item.tipo_provavel].append(item)
        elif item.material_trabalho:
            trabalho.append(item)
        elif item.categoria_externa:
            externos.append(item)
        else:
            quarentena.append(item)
            plano.pendencias_humanas.append(
                f"sem classificação suficiente: {item.origem}"
            )

    # -- versão atual x histórico ------------------------------------------ #
    for tipo, grupo in sorted(por_tipo.items()):
        ordenado = sorted(grupo, key=lambda i: (i.modificado_em, i.origem))
        escolhido: Optional[ItemInventario] = None
        if tipo in escolhas:
            candidatos = [i for i in ordenado if i.origem == escolhas[tipo] or i.nome == escolhas[tipo]]
            if not candidatos:
                raise OperacaoBloqueada(
                    f"A escolha para {tipo} ({escolhas[tipo]}) não está entre os "
                    f"arquivos encontrados: {[i.origem for i in ordenado]}"
                )
            escolhido = candidatos[-1]
        else:
            escolhido = ordenado[-1]
            empatados = [i for i in ordenado if i.modificado_em == escolhido.modificado_em]
            if len(empatados) > 1:
                plano.status = STATUS_BLOQUEADO
                plano.ambiguidades.append(
                    f"{tipo}: {len(empatados)} arquivos com a mesma data de modificação "
                    f"({', '.join(i.origem for i in empatados)}). Não escolho a versão "
                    f"vigente no chute — indique com --escolher {tipo}=<arquivo>."
                )
                continue

        versao = 0
        for item in ordenado:
            if item is escolhido:
                continue
            versao += 1
            plano.movimentos.append(Movimento(
                origem=item.origem,
                destino=(
                    f"90_HISTORICO/{obter_tipo(tipo).pasta_historico}/"
                    + nome_historico(
                        tipo, versao,
                        datetime.fromisoformat(item.modificado_em),
                        "migracao", Path(item.nome).suffix,
                    )
                ),
                natureza="versao_historica",
                tipo=tipo,
                versao=versao,
                motivo=f"versão anterior identificada por data ({item.modificado_em})"
                       + (f"; nome {item.nome_suspeito}" if item.nome_suspeito else ""),
            ))
        versao += 1
        plano.movimentos.append(Movimento(
            origem=escolhido.origem,
            destino=f"01_EM_ELABORACAO/{nome_canonico(tipo, Path(escolhido.nome).suffix)}",
            natureza="documento_atual",
            tipo=tipo,
            versao=versao,
            motivo=(
                f"versão mais recente ({escolhido.modificado_em})"
                if tipo not in escolhas else "escolhida pelo operador"
            ),
        ))
        if escolhido.nome_suspeito:
            plano.pendencias_humanas.append(
                f"a versão vigente de {tipo} veio de um arquivo com nome solto "
                f"('{escolhido.nome}': {escolhido.nome_suspeito}); confirme se é mesmo "
                f"a vigente"
            )

    # -- externos ----------------------------------------------------------- #
    # Dois PDFs sem data nem origem legíveis produzem o MESMO nome padronizado.
    # Isso não é ambiguidade de versão — é só falta de metadado — e se resolve
    # com o hash no nome, como faz a importação. Bloquear a migração inteira por
    # causa disso seria desproporcional.
    usados: set[str] = set()
    for item in externos:
        caminho = origem / item.origem
        analise = classificar(caminho, numero_processo=numero_processo)
        nome_final = nome_externo(
            analise.data_documento, analise.origem, analise.tipo,
            None, Path(item.nome).suffix,
        )
        destino_externo = f"{AREA_EXTERNOS}/{CATEGORIAS_EXTERNAS[analise.categoria]}/{nome_final}"
        if destino_externo in usados:
            radical = Path(nome_final)
            nome_final = f"{radical.stem}_{item.hash_sha256[:8]}{radical.suffix}"
            destino_externo = (
                f"{AREA_EXTERNOS}/{CATEGORIAS_EXTERNAS[analise.categoria]}/{nome_final}"
            )
            plano.pendencias_humanas.append(
                f"{item.origem}: nome padronizado colidiu com outro documento sem "
                f"data e sem origem identificadas; desempatado pelo hash — confirme "
                f"a origem e renomeie"
            )
        usados.add(destino_externo)
        plano.movimentos.append(Movimento(
            origem=item.origem,
            destino=destino_externo,
            natureza="externo",
            motivo=f"classificado como {analise.tipo or 'documento externo'} "
                   f"({analise.confianca}, {analise.fonte_da_analise})",
        ))
        for pendencia in analise.pendencias:
            plano.pendencias_humanas.append(f"{item.origem}: {pendencia}")

    # -- material de trabalho ------------------------------------------------ #
    # Nome original e subpasta preservados de propósito: `pncp-itens-20260724-
    # 095611.json` diz quando foi coletado e de que consulta veio — é o que
    # torna a evidência conferível contra o relatório que a citou.
    for item in trabalho:
        destino_trabalho = f"{AREA_TRABALHO}/{Path(item.origem).as_posix()}"
        usados.add(destino_trabalho)
        plano.movimentos.append(Movimento(
            origem=item.origem,
            destino=destino_trabalho,
            natureza="material_trabalho",
            motivo=item.material_trabalho or "material de trabalho",
        ))
    if trabalho:
        plano.pendencias_humanas.append(
            f"{len(trabalho)} arquivo(s) de material de trabalho foram copiados sem "
            f"análise de conteúdo: não se verificou se citam outro processo nem se "
            f"contêm dado pessoal de terceiro (a pesquisa de similares baixa "
            f"documento de outro órgão). Conferência humana antes de publicar."
        )

    # -- quarentena --------------------------------------------------------- #
    for item in quarentena:
        nome_quarentena = sanitizar_nome_arquivo(item.nome)
        destino_quarentena = f"{AREA_QUARENTENA}/{nome_quarentena}"
        if destino_quarentena in usados:
            radical = Path(nome_quarentena)
            destino_quarentena = (
                f"{AREA_QUARENTENA}/{radical.stem}_{item.hash_sha256[:8]}{radical.suffix}"
            )
        usados.add(destino_quarentena)
        plano.movimentos.append(Movimento(
            origem=item.origem,
            destino=destino_quarentena,
            natureza="quarentena",
            motivo="temporário" if item.temporario else "sem classificação segura",
        ))

    plano.preservados.append(
        f"{origem} — a pasta original permanece intacta como backup"
    )
    destinos = [m.destino for m in plano.movimentos]
    if len(destinos) != len(set(destinos)):
        repetidos = sorted({d for d in destinos if destinos.count(d) > 1})
        plano.status = STATUS_BLOQUEADO
        plano.ambiguidades.append(
            f"destinos repetidos no plano: {', '.join(repetidos)}"
        )
    return plano


# --------------------------------------------------------------------------- #
# Execução
# --------------------------------------------------------------------------- #

def executar(
    plano: PlanoMigracao,
    destino_identificador: str,
    *,
    base: Optional[Path | str] = None,
    responsavel: str = "Charles",
    forcar: bool = False,
) -> PlanoMigracao:
    """Aplica o plano por CÓPIA. A origem não é alterada nem removida."""
    if plano.status == STATUS_BLOQUEADO and not forcar:
        raise OperacaoBloqueada(
            "O plano está bloqueado por ambiguidade e não será executado:\n- "
            + "\n- ".join(plano.ambiguidades)
        )
    origem = Path(plano.origem)
    processo = Processo.abrir(destino_identificador, base)
    manifesto = processo.ler_documentos()
    if not manifesto.get("documentos"):
        manifesto = manifesto_vazio(processo.ler_processo().get("processo_id", processo.identificador))

    copiados = 0
    with Transacao(processo.temporarios, f"migrar {origem.name}") as tx:
        for movimento in plano.movimentos:
            arquivo_origem = origem / movimento.origem
            if not arquivo_origem.is_file():
                raise OperacaoBloqueada(
                    f"O plano cita {movimento.origem}, que não está mais em {origem}. "
                    f"Refaça o plano — nada foi migrado."
                )
            destino = processo.raiz / movimento.destino
            destino.parent.mkdir(parents=True, exist_ok=True)
            tx.copiar(arquivo_origem, destino)
            copiados += 1

            if movimento.natureza in ("documento_atual", "versao_historica"):
                _registrar_no_manifesto(processo, manifesto, movimento, destino, responsavel)
            elif movimento.natureza in ("externo", "quarentena"):
                _registrar_externo(processo, manifesto, movimento, destino, origem)

        manifesto["atualizado_em"] = agora()
        tx.gravar_json(processo.arquivo_documentos, manifesto)
        tx.acrescentar_linha(processo.arquivo_log, linha_log(evento(
            "processo_migrado",
            responsavel=responsavel,
            motivo=f"migração de {origem} ({copiados} arquivo(s) copiados)",
            origem=str(origem),
        )))
        from gerar_painel import montar_painel

        tx.gravar_texto(processo.arquivo_painel, montar_painel(processo, manifesto=manifesto))

    # -- conferência de quantidade (item 24, passo 14) --------------------- #
    esperado = len(plano.movimentos)
    if copiados != esperado:
        plano.status = STATUS_RESSALVAS
        plano.pendencias_humanas.append(
            f"foram copiados {copiados} de {esperado} arquivos previstos"
        )
    else:
        plano.status = STATUS_RESSALVAS if plano.pendencias_humanas else STATUS_CONCLUIDA
    return plano


def _registrar_no_manifesto(
    processo: Processo, manifesto: dict, movimento: Movimento, destino: Path, responsavel: str
) -> None:
    tipo = movimento.tipo or ""
    descricao = obter_tipo(tipo)
    registro = manifesto["documentos"].setdefault(tipo, {
        "titulo": descricao.titulo,
        "versao_atual": 0,
        "status": "em_elaboracao",
        "arquivo_atual": None,
        "hash_sha256": None,
        "hash_conteudo": None,
        "criado_em": agora(),
        "atualizado_em": agora(),
        "gerado_por": responsavel,
        "minuta_origem": None,
        "processo": processo.ler_processo().get("numero") or processo.identificador,
        "fase": descricao.fase,
        "substitui_versao": None,
        "motivo_ultima_alteracao": "migração de pasta antiga",
        "validacao": {"conteudo": "nao_executada", "formatacao": "nao_executada"},
        "representacoes": {"docx": None, "pdf": None, "assinado": None},
        "historico": [],
        "origem_da_versao": {"tipo": "migracao", "pasta": movimento.origem},
    })
    digest = sha256_arquivo(destino)
    if movimento.natureza == "versao_historica":
        registro["historico"].append({
            "versao": movimento.versao,
            "arquivo": processo.relativo(destino),
            "hash_sha256": digest,
            "status_ao_arquivar": "desconhecido_na_migracao",
            "arquivado_em": agora(),
            "motivo": movimento.motivo,
            "responsavel": responsavel,
            "nome_original": movimento.origem,
        })
    else:
        registro.update({
            "versao_atual": movimento.versao,
            "arquivo_atual": processo.relativo(destino),
            "hash_sha256": digest,
            "hash_conteudo": hash_conteudo(destino),
            "atualizado_em": agora(),
            "motivo_ultima_alteracao": movimento.motivo,
        })
        registro["representacoes"]["docx"] = registro["arquivo_atual"]


def _registrar_externo(
    processo: Processo, manifesto: dict, movimento: Movimento, destino: Path, origem: Path
) -> None:
    from importar_documento_externo import metadados_externos

    analise = classificar(origem / movimento.origem)
    registro = metadados_externos(
        analise,
        nome_original=Path(movimento.origem).name,
        nome_padronizado=destino.name if movimento.natureza == "externo" else None,
        numero_processo=processo.ler_processo().get("numero") or processo.identificador,
        hash_sha256=sha256_arquivo(destino),
        fonte="migracao_de_pasta_antiga",
        email_origem=None,
        classificacao_sigilo="uso_interno",
        status_validacao="em_quarentena" if movimento.natureza == "quarentena" else "a_confirmar",
        caminho_relativo=processo.relativo(destino),
        observacoes=movimento.motivo,
    )
    manifesto.setdefault("documentos_externos", []).append(registro)


# --------------------------------------------------------------------------- #
# Relatório (item 33)
# --------------------------------------------------------------------------- #

def relatorio(plano: PlanoMigracao) -> str:
    por_natureza: dict[str, list[Movimento]] = defaultdict(list)
    for movimento in plano.movimentos:
        por_natureza[movimento.natureza].append(movimento)

    versoes = defaultdict(list)
    for movimento in plano.movimentos:
        if movimento.tipo:
            versoes[movimento.tipo].append(movimento)

    linhas = [
        "# Relatório de Organização do Processo",
        "",
        "## Pasta analisada",
        "",
        f"`{plano.origem}` → `{plano.destino}`",
        "",
        "## Total de arquivos",
        "",
        f"{plano.total_arquivos} arquivo(s) inventariado(s); "
        f"{len(plano.movimentos)} movimento(s) previsto(s).",
        "",
        "## Documentos gerados pelo Charles",
        "",
    ]
    if versoes:
        for tipo, movimentos in sorted(versoes.items()):
            atual = [m for m in movimentos if m.natureza == "documento_atual"]
            linhas.append(
                f"- **{tipo}** — {len(movimentos)} arquivo(s); vigente: "
                + (f"`{atual[0].origem}`" if atual else "**não definida**")
            )
    else:
        linhas.append("_Nenhum documento de tipo reconhecido._")

    linhas += ["", "## Documentos externos", ""]
    externos = por_natureza.get("externo", [])
    linhas += ([f"- `{m.origem}` → `{m.destino}` ({m.motivo})" for m in externos]
               or ["_Nenhum._"])

    linhas += ["", "## Material de trabalho", ""]
    material = por_natureza.get("material_trabalho", [])
    if material:
        linhas.append(
            f"{len(material)} arquivo(s) mantêm nome e subpasta originais em "
            f"`{AREA_TRABALHO}/`. Não são documentos externos e não foram "
            f"analisados quanto a conteúdo."
        )
        linhas.append("")
        for movimento in material[:10]:
            linhas.append(f"- `{movimento.origem}` → `{movimento.destino}` ({movimento.motivo})")
        if len(material) > 10:
            linhas.append(f"- _(+{len(material) - 10} arquivo(s); a lista completa está no plano JSON)_")
    else:
        linhas.append("_Nenhum._")

    linhas += ["", "## Possíveis versões", ""]
    historicas = por_natureza.get("versao_historica", [])
    linhas += ([f"- `{m.origem}` → `{m.destino}` — {m.motivo}" for m in historicas]
               or ["_Nenhuma versão anterior identificada._"])

    linhas += ["", "## Versões atuais identificadas", ""]
    atuais = por_natureza.get("documento_atual", [])
    linhas += ([f"- **{m.tipo}**: `{m.origem}` — {m.motivo}" for m in atuais]
               or ["_Nenhuma._"])

    linhas += ["", "## Duplicados exatos", ""]
    linhas += ([f"- mantido `{d['mantido']}`; cópias: {', '.join(d['copias'])}"
                for d in plano.duplicados_exatos] or ["_Nenhum._"])

    linhas += ["", "## Duplicados prováveis", "",
               "_Rode `detectar_duplicados.py` sobre o processo migrado para a "
               "análise de semelhança textual; duplicado provável não se resolve "
               "na migração._"]

    linhas += ["", "## Arquivos temporários", ""]
    temporarios = [i.origem for i in plano.inventario if i.temporario]
    linhas += ([f"- `{t}` (movido para quarentena, não apagado)" for t in temporarios]
               or ["_Nenhum._"])

    linhas += ["", "## Arquivos de outro processo", ""]
    outros = [i for i in plano.inventario if i.outro_processo]
    linhas += ([f"- `{i.origem}` — cita {', '.join(i.processos_citados)}" for i in outros]
               or ["_Nenhum._"])

    linhas += ["", "## Arquivos sem classificação", ""]
    quarentenados = por_natureza.get("quarentena", [])
    linhas += ([f"- `{m.origem}` — {m.motivo}" for m in quarentenados] or ["_Nenhum._"])

    linhas += ["", "## Estrutura proposta", "",
               "```", "01_EM_ELABORACAO/   — um arquivo por tipo documental",
               "03_DOCUMENTOS_EXTERNOS/ — propostas, certidões, e-mails classificados",
               "07_MATERIAL_DE_TRABALHO/ — evidência de pesquisa, com nome original",
               "90_HISTORICO/       — versões anteriores, com versão e carimbo de tempo",
               "98_QUARENTENA/      — o que depende de decisão humana", "```"]

    linhas += ["", "## Movimentações propostas", "",
               "| Origem | Destino | Natureza |", "|---|---|---|"]
    linhas += [f"| `{m.origem}` | `{m.destino}` | {m.natureza} |" for m in plano.movimentos]

    linhas += ["", "## Arquivos preservados", ""]
    linhas += [f"- {p}" for p in plano.preservados]

    linhas += ["", "## Pendências humanas", ""]
    linhas += ([f"- {p}" for p in plano.pendencias_humanas] or ["_Nenhuma._"])
    if plano.ambiguidades:
        linhas += ["", "### Ambiguidades bloqueantes", ""]
        linhas += [f"- {a}" for a in plano.ambiguidades]

    linhas += ["", "## Resultado", "", f"**{plano.status}**", ""]
    if plano.status == STATUS_PLANO:
        linhas.append(
            "Nenhum arquivo foi copiado, movido ou apagado. Confira o plano e "
            "execute com `--executar --plano <arquivo>`."
        )
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Organiza uma pasta de processo antiga sem apagar nada."
    )
    analisador.add_argument("--origem", required=True)
    analisador.add_argument("--destino", required=True, help="processo de destino")
    analisador.add_argument("--somente-planejar", action="store_true", default=True)
    analisador.add_argument("--executar", action="store_true",
                            help="aplica o plano (por cópia)")
    analisador.add_argument("--plano", help="arquivo JSON do plano a executar/gravar")
    analisador.add_argument("--relatorio", help="grava o relatório em Markdown")
    analisador.add_argument("--numero-processo", help='ex.: "PA 031/2026"')
    analisador.add_argument("--escolher", action="append", default=[],
                            metavar="TIPO=ARQUIVO",
                            help="define a versão vigente de um tipo ambíguo")
    analisador.add_argument("--forcar", action="store_true",
                            help="executa mesmo com ambiguidade (não recomendado)")
    analisador.add_argument("--responsavel", default="Charles")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    escolhas = {}
    for item in argumentos.escolher:
        if "=" not in item:
            print(f"ERRO: --escolher espera TIPO=ARQUIVO, recebi {item!r}", file=sys.stderr)
            return 2
        chave, valor = item.split("=", 1)
        escolhas[chave.strip()] = valor.strip()

    try:
        numero = argumentos.numero_processo
        if not numero:
            try:
                numero = Processo.abrir(argumentos.destino, argumentos.base).ler_processo().get("numero")
            except Exception:  # noqa: BLE001 - destino pode ainda não existir
                numero = None

        plano = planejar(
            argumentos.origem, argumentos.destino,
            numero_processo=numero, escolhas=escolhas, base=argumentos.base,
        )
        if argumentos.executar:
            plano = executar(
                plano, argumentos.destino, base=argumentos.base,
                responsavel=argumentos.responsavel, forcar=argumentos.forcar,
            )
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    texto = relatorio(plano)
    if argumentos.plano:
        Path(argumentos.plano).write_text(
            json.dumps(plano.como_dicionario(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Plano gravado em: {argumentos.plano}")
    if argumentos.relatorio:
        Path(argumentos.relatorio).write_text(texto, encoding="utf-8")
        print(f"Relatório gravado em: {argumentos.relatorio}")
    print(texto)
    return 0 if plano.status != STATUS_BLOQUEADO else 1


if __name__ == "__main__":
    raise SystemExit(main())
