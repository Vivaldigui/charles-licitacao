#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
formatar_docx.py — MODO PADRONIZAÇÃO AUTOMÁTICA e MODO REVISÃO DE MINUTA-MÃE.

Aplica correções visuais seguras sobre uma CÓPIA do documento. O arquivo de
entrada nunca é sobrescrito, e uma minuta-mãe de `05_minutas/` só pode ser
alterada com `--revisar-minuta-mae`.

Exemplos:
    python scripts/docx_cmi/formatar_docx.py \
      --entrada documento.docx --saida documento_formatado.docx \
      --perfil tr --preservar-conteudo

    python scripts/docx_cmi/formatar_docx.py \
      --entrada documento.docx --saida documento_formatado.docx \
      --perfil contrato --corrigir-numeracao --validar-referencias-internas

    python scripts/docx_cmi/formatar_docx.py \
      --diretorio 08_processos_em_andamento/PROCESSO_X/ \
      --saida-diretorio 08_processos_em_andamento/PROCESSO_X/documentos_formatados/
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import auditar_docx
import cabecalho_rodape_docx
import numeracao_docx
import relatorio_docx
import tabelas_docx
import validar_conteudo_docx
from estilos_docx import (
    PAPEL_CABECALHO_TABELA,
    PAPEL_TABELA,
    aplicar_formatacao_paragrafo,
    carregar_padrao,
    classificar_paragrafo,
    garantir_estilos,
    perfil_por_arquivo,
)
from util_ooxml import (
    CAMPO_RE,
    assinaturas_partes,
    exigir_python_docx,
    iter_paragrafos_tabela,
    iter_tabelas,
    paragrafo_vazio,
    quebras_de_pagina,
    remover_paragrafo,
    remover_quebras_de_pagina,
    substituir_marcadores_paragrafo,
    texto_paragrafo,
)

RAIZ = Path(__file__).resolve().parents[2]
PASTA_MINUTAS = (RAIZ / "05_minutas").resolve()


# --------------------------------------------------------------------------- #
# Pipeline de formatação
# --------------------------------------------------------------------------- #

def _formatar_tabelas_paragrafos(documento, padrao, normalizar_cores: bool) -> list[str]:
    """Normaliza os parágrafos internos das tabelas."""
    mudancas: list[str] = []
    for indice_tabela, tabela in enumerate(iter_tabelas(documento)):
        for indice_linha, linha in enumerate(tabela.rows):
            for celula in linha.cells:
                for paragrafo in celula.paragraphs:
                    papel = (PAPEL_CABECALHO_TABELA if indice_linha == 0
                             else PAPEL_TABELA)
                    for item in aplicar_formatacao_paragrafo(
                        paragrafo, papel, padrao,
                        aplicar_estilo_nomeado=True,
                        normalizar_cores=normalizar_cores,
                    ):
                        mudancas.append(f"Tabela {indice_tabela}: {item}")
    return mudancas


def _limpar_espacamento(documento, padrao) -> list[str]:
    """
    Remove parágrafos vazios em excesso e quebras de página duplicadas.

    Só remove parágrafo VAZIO (sem texto, sem imagem, sem quebra de página) e
    apenas quando ele excede o limite de vazios consecutivos do padrão — é uma
    das diferenças autorizadas do item 21 do escopo.
    """
    config = padrao.base["paginacao"]
    mudancas: list[str] = []

    if config.get("remover_paragrafos_vazios_consecutivos"):
        limite = int(config.get("maximo_paragrafos_vazios_consecutivos", 1))
        sequencia: list[Any] = []
        removidos = 0
        for paragrafo in list(documento.paragraphs):
            if paragrafo_vazio(paragrafo):
                sequencia.append(paragrafo)
                continue
            if len(sequencia) > limite:
                for excedente in sequencia[limite:]:
                    if remover_paragrafo(excedente):
                        removidos += 1
            sequencia = []
        if len(sequencia) > limite:
            for excedente in sequencia[limite:]:
                if remover_paragrafo(excedente):
                    removidos += 1
        if removidos:
            mudancas.append(
                f"{removidos} parágrafo(s) vazio(s) em excesso removidos "
                f"(máximo de {limite} consecutivos)."
            )

    if config.get("remover_quebras_duplicadas"):
        removidas = 0
        anterior_com_quebra = False
        for paragrafo in list(documento.paragraphs):
            quantidade = quebras_de_pagina(paragrafo)
            if quantidade > 1:
                # Mantém uma; remove as demais recriando apenas a primeira.
                total = remover_quebras_de_pagina(paragrafo)
                removidas += total - 1
                _reinserir_quebra(paragrafo)
                anterior_com_quebra = True
                continue
            if quantidade == 1 and anterior_com_quebra and paragrafo_vazio(paragrafo):
                removidas += remover_quebras_de_pagina(paragrafo)
                continue
            anterior_com_quebra = quantidade == 1
        if removidas:
            mudancas.append(f"{removidas} quebra(s) de página duplicada(s) removida(s).")

    return mudancas


def _reinserir_quebra(paragrafo) -> None:
    from util_ooxml import qn

    runs = paragrafo._p.findall(qn("w:r"))
    if not runs:
        run = paragrafo._p.makeelement(qn("w:r"), {})
        paragrafo._p.append(run)
        runs = [run]
    br = runs[0].makeelement(qn("w:br"), {})
    br.set(qn("w:type"), "page")
    runs[0].insert(0, br)


def aplicar_pipeline(documento, padrao, normalizar_cores: bool = False) -> list[str]:
    """
    Aplica toda a formatação segura. Não altera texto.

    Idempotente: uma segunda execução sobre o resultado devolve lista vazia.
    """
    mudancas: list[str] = []

    for estilo, itens in garantir_estilos(documento, padrao).items():
        mudancas.append(f"Estilo '{estilo}': {', '.join(itens)}")

    paragrafos = list(documento.paragraphs)
    total = len(paragrafos)
    for indice, paragrafo in enumerate(paragrafos):
        papel = classificar_paragrafo(paragrafo, indice, total, padrao)
        for item in aplicar_formatacao_paragrafo(
            paragrafo, papel, padrao, normalizar_cores=normalizar_cores
        ):
            mudancas.append(f"Parágrafo {indice} ({papel}): {item}")

    mudancas += _formatar_tabelas_paragrafos(documento, padrao, normalizar_cores)
    mudancas += tabelas_docx.padronizar(documento, padrao)
    mudancas += _limpar_espacamento(documento, padrao)
    return mudancas


# --------------------------------------------------------------------------- #
# Preenchimento de campos
# --------------------------------------------------------------------------- #

def preencher_campos(documento, campos: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    """
    Substitui `{{CAMPO}}` preservando a formatação, inclusive quando o marcador
    está dividido entre vários runs.
    """
    from util_ooxml import iter_paragrafos_corpo

    preenchidos: list[str] = []
    substituicoes: dict[str, str] = {}

    def resolver(nome: str) -> Optional[str]:
        if nome in campos:
            substituicoes[f"{{{{{nome}}}}}"] = str(campos[nome])
            return str(campos[nome])
        return None

    for paragrafo in iter_paragrafos_corpo(documento):
        resultado = substituir_marcadores_paragrafo(paragrafo, resolver, CAMPO_RE)
        preenchidos += resultado.preenchidos
    return sorted(set(preenchidos)), substituicoes


# --------------------------------------------------------------------------- #
# Metadados
# --------------------------------------------------------------------------- #

def limpar_metadados(documento) -> list[str]:
    """Limpa autor/último editor/empresa. Só roda com --limpar-metadados."""
    propriedades = documento.core_properties
    limpos: list[str] = []
    for atributo in ("author", "last_modified_by", "category", "comments"):
        valor = getattr(propriedades, atributo, None)
        if valor:
            setattr(propriedades, atributo, "")
            limpos.append(atributo)
    return [f"Metadados pessoais limpos: {', '.join(limpos)}"] if limpos else []


# --------------------------------------------------------------------------- #
# Execução principal
# --------------------------------------------------------------------------- #

def _protegido_minuta_mae(destino: Path, autorizado: bool) -> None:
    try:
        dentro = destino.resolve().is_relative_to(PASTA_MINUTAS)
    except (OSError, ValueError):
        dentro = False
    if dentro and not autorizado:
        raise PermissionError(
            f"Gravar em {destino} sobrescreveria a biblioteca oficial de minutas. "
            "Use --revisar-minuta-mae, que faz backup, versiona e registra a "
            "alteração, ou escolha outro destino."
        )


def formatar(
    entrada: Path,
    saida: Path,
    perfil_id: Optional[str] = None,
    minuta_mae: Optional[Path] = None,
    campos: Optional[dict[str, str]] = None,
    corrigir_numeracao: bool = False,
    validar_referencias_internas: bool = False,
    normalizar_cores: bool = False,
    limpar_metadados_pessoais: bool = False,
    preservar_conteudo: bool = True,
    revisar_minuta_mae: bool = False,
    verificar_idempotencia: bool = True,
) -> dict[str, Any]:
    """Executa a padronização e devolve o diagnóstico consolidado."""
    exigir_python_docx()
    from docx import Document

    entrada, saida = Path(entrada), Path(saida)
    if not entrada.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")
    if entrada.resolve() == saida.resolve():
        raise ValueError(
            "A saída não pode ser igual à entrada — o arquivo original nunca é "
            "sobrescrito."
        )
    _protegido_minuta_mae(saida, revisar_minuta_mae)

    if perfil_id is None:
        perfil_id = perfil_por_arquivo(entrada.name) or "generico"
    padrao = carregar_padrao(perfil_id)

    diagnostico = auditar_docx.auditar(entrada, perfil_id, minuta_mae)
    diagnostico["modo"] = "revisão de minuta-mãe" if revisar_minuta_mae else "padronização automática"

    documento = Document(str(entrada))
    conteudo_antes = validar_conteudo_docx.extrair(documento)
    partes_antes = assinaturas_partes(entrada)

    aplicadas: list[str] = []
    substituicoes: dict[str, str] = {}
    if campos:
        preenchidos, substituicoes = preencher_campos(documento, campos)
        if preenchidos:
            aplicadas.append("Campos preenchidos: " + ", ".join(preenchidos))

    aplicadas += aplicar_pipeline(documento, padrao, normalizar_cores)

    # ---- numeração -------------------------------------------------------- #
    renumeracoes: dict[str, set[str]] = {}
    nao_aplicadas: list[str] = []
    diag_num = numeracao_docx.analisar(
        list(documento.paragraphs),
        padrao.perfil.get("titulos") == "clausulas_por_extenso",
    )
    proposta = numeracao_docx.propor_renumeracao(diag_num)
    afetadas = numeracao_docx.referencias_afetadas(diag_num, proposta)

    if corrigir_numeracao:
        bloqueios: list[str] = []
        if not padrao.renumeracao_automatica:
            bloqueios.append(
                f"O perfil '{perfil_id}' proíbe renumeração automática "
                "(cláusulas contratuais exigem análise jurídica)."
            )
        nao_corrigiveis = [p for p in diag_num.problemas if not p.corrigivel]
        if nao_corrigiveis:
            bloqueios.append(
                "Há problemas de numeração que exigem decisão humana: "
                + "; ".join(p.tipo for p in nao_corrigiveis)
            )
        if validar_referencias_internas and afetadas:
            bloqueios.append(
                "Referências internas ficariam inconsistentes: " + "; ".join(afetadas)
            )
        if bloqueios:
            nao_aplicadas += [f"Renumeração NÃO aplicada — {b}" for b in bloqueios]
        elif proposta:
            for antigo, novo in proposta.values():
                renumeracoes.setdefault(antigo, set()).add(novo)
            for item in numeracao_docx.aplicar_renumeracao(
                list(documento.paragraphs), proposta
            ):
                aplicadas.append(f"Renumeração: {item}")
    elif proposta:
        nao_aplicadas.append(
            f"{len(proposta)} rótulo(s) de numeração seriam alterados. "
            "Rode com --corrigir-numeracao para aplicar."
        )

    if limpar_metadados_pessoais:
        aplicadas += limpar_metadados(documento)

    # ---- gravação em área temporária e validação -------------------------- #
    with tempfile.TemporaryDirectory() as temporario:
        provisorio = Path(temporario) / "saida.docx"
        documento.save(str(provisorio))

        documento_depois = Document(str(provisorio))
        conteudo_depois = validar_conteudo_docx.extrair(documento_depois)
        validacao = validar_conteudo_docx.comparar(
            conteudo_antes, conteudo_depois,
            renumeracoes=renumeracoes, substituicoes=substituicoes,
        )
        intactas, divergencias_partes = cabecalho_rodape_docx.partes_protegidas_intactas(
            entrada, provisorio
        )

        testes: dict[str, str] = {}
        if verificar_idempotencia:
            segunda = Document(str(provisorio))
            mudancas_segunda = aplicar_pipeline(segunda, padrao, normalizar_cores)
            testes["idempotencia"] = (
                "OK — segunda execução não produziu alterações."
                if not mudancas_segunda
                else f"FALHOU — segunda execução ainda alteraria "
                     f"{len(mudancas_segunda)} item(ns): "
                     + "; ".join(mudancas_segunda[:5])
            )
        testes["validacao_visual"] = (
            "não executada — LibreOffice/soffice não disponível no ambiente; "
            "a conferência visual permanece a cargo do usuário."
        )

        bloqueado = preservar_conteudo and (
            not validacao.conteudo_preservado or not intactas
        )
        if not bloqueado:
            saida.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(provisorio, saida)

    diagnostico["correcoes_aplicadas"] = aplicadas if not bloqueado else []
    diagnostico["correcoes_nao_aplicadas"] = nao_aplicadas + (
        ["TODAS — a gravação foi bloqueada pela validação de conteúdo."]
        if bloqueado else []
    )
    diagnostico["validacao_conteudo"] = {
        "hash_antes": validacao.hash_antes,
        "hash_depois": validacao.hash_depois,
        "paragrafos_antes": validacao.paragrafos_antes,
        "paragrafos_depois": validacao.paragrafos_depois,
        "celulas_antes": validacao.celulas_antes,
        "celulas_depois": validacao.celulas_depois,
        "conteudo_preservado": validacao.conteudo_preservado,
        "partes_protegidas_intactas": intactas,
        "divergencias_partes_protegidas": divergencias_partes,
        "diferencas": [
            {"tipo": d.tipo, "autorizada": d.autorizada, "motivo": d.motivo,
             "antes": d.antes[:200], "depois": d.depois[:200]}
            for d in validacao.diferencas
        ],
    }
    diagnostico["testes"] = testes
    diagnostico["arquivo_final"] = None if bloqueado else str(saida)
    diagnostico["status"] = _status_final(
        diagnostico, validacao, intactas, bloqueado, testes
    )
    return diagnostico


def _status_final(diagnostico, validacao, intactas, bloqueado, testes) -> str:
    if bloqueado:
        return (auditar_docx.STATUS_BLOQUEADO_CONTEUDO if not validacao.conteudo_preservado
                else auditar_docx.STATUS_BLOQUEADO_ESTRUTURA)
    if not intactas:
        return auditar_docx.STATUS_BLOQUEADO_ESTRUTURA
    if testes.get("idempotencia", "").startswith("FALHOU"):
        return auditar_docx.STATUS_CONFERENCIA
    if diagnostico["pendencias"]["total"] or diagnostico["revisao"]["comentarios"]:
        return auditar_docx.STATUS_CONFERENCIA
    if diagnostico["correcoes_que_exigem_humano"]:
        return auditar_docx.STATUS_RESSALVAS
    return auditar_docx.STATUS_APROVADO


# --------------------------------------------------------------------------- #
# Modo revisão de minuta-mãe
# --------------------------------------------------------------------------- #

RE_VERSAO = re.compile(r"^versao:\s*([0-9]+)\.([0-9]+)\s*$", re.MULTILINE)


def revisar_minuta_mae(minuta: Path, perfil_id: Optional[str] = None,
                       **kwargs) -> dict[str, Any]:
    """
    MODO REVISÃO DE MINUTA-MÃE — só com pedido expresso do usuário.

    1) faz backup em `_arquivo/`; 2) gera relatório do estado anterior;
    3) aplica as correções; 4) incrementa a versão na ficha de uso;
    5) registra no changelog da pasta. Nada é alterado sem rastreabilidade.
    """
    minuta = Path(minuta)
    pasta = minuta.parent
    arquivo_versoes = pasta / "_arquivo"
    arquivo_versoes.mkdir(parents=True, exist_ok=True)

    ficha = next(iter(sorted(pasta.glob("*_FICHA_DE_USO.md"))), None)
    versao_atual, versao_nova = "1.0", "1.1"
    if ficha is not None:
        texto = ficha.read_text(encoding="utf-8")
        casamento = RE_VERSAO.search(texto)
        if casamento:
            maior, menor = int(casamento.group(1)), int(casamento.group(2))
            versao_atual = f"{maior}.{menor}"
            versao_nova = f"{maior}.{menor + 1}"

    backup = arquivo_versoes / f"{minuta.stem}_v{versao_atual}.docx"
    shutil.copyfile(minuta, backup)

    relatorio_anterior = auditar_docx.auditar(minuta, perfil_id)
    destino_relatorio = pasta / f"{minuta.stem}_ESTADO_ANTERIOR_v{versao_atual}.md"
    relatorio_docx.gravar(relatorio_anterior, destino_relatorio)

    with tempfile.TemporaryDirectory() as temporario:
        provisorio = Path(temporario) / minuta.name
        diagnostico = formatar(
            minuta, provisorio, perfil_id,
            revisar_minuta_mae=True, **kwargs
        )
        if diagnostico["arquivo_final"] is None:
            diagnostico["revisao_minuta"] = {
                "aplicada": False,
                "motivo": "A validação bloqueou a gravação; a minuta-mãe não foi tocada.",
                "backup": str(backup),
            }
            return diagnostico
        shutil.copyfile(provisorio, minuta)

    if ficha is not None:
        texto = ficha.read_text(encoding="utf-8")
        texto = RE_VERSAO.sub(f"versao: {versao_nova}", texto, count=1)
        texto = re.sub(r"^atualizado_em:.*$", f"atualizado_em: {date.today().isoformat()}",
                       texto, count=1, flags=re.MULTILINE)
        ficha.write_text(texto, encoding="utf-8")

    changelog = next(iter(sorted(pasta.glob("*_CHANGELOG.md"))), None)
    entrada_log = (
        f"\n## v{versao_nova} — {date.today().isoformat()}\n\n"
        f"Revisão de PADRONIZAÇÃO VISUAL pelo Módulo de Padronização Documental "
        f"(perfil `{diagnostico['perfil']}`).\n\n"
        f"- Backup da versão anterior: `{backup.relative_to(RAIZ)}`\n"
        f"- Relatório do estado anterior: `{destino_relatorio.relative_to(RAIZ)}`\n"
        f"- Correções aplicadas: {len(diagnostico['correcoes_aplicadas'])}\n"
        f"- Conteúdo preservado: "
        f"{'sim' if diagnostico['validacao_conteudo']['conteudo_preservado'] else 'NÃO'}\n"
        f"- Timbre (cabeçalho/rodapé/mídia) intacto: "
        f"{'sim' if diagnostico['validacao_conteudo']['partes_protegidas_intactas'] else 'NÃO'}\n"
    )
    if changelog is not None:
        changelog.write_text(
            changelog.read_text(encoding="utf-8") + entrada_log, encoding="utf-8"
        )

    diagnostico["arquivo_final"] = str(minuta)
    diagnostico["revisao_minuta"] = {
        "aplicada": True,
        "versao_anterior": versao_atual,
        "versao_nova": versao_nova,
        "backup": str(backup),
        "relatorio_estado_anterior": str(destino_relatorio),
        "ficha_atualizada": str(ficha) if ficha else None,
        "changelog_atualizado": str(changelog) if changelog else None,
        "pendencia": "Atualizar 05_minutas/_CONTROLE_MINUTAS.md com a nova versão.",
    }
    return diagnostico


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MODO PADRONIZAÇÃO AUTOMÁTICA — formata um DOCX sobre uma cópia."
    )
    parser.add_argument("--entrada", help="DOCX de entrada.")
    parser.add_argument("--saida", help="DOCX de saída (nunca igual à entrada).")
    parser.add_argument("--diretorio", help="Processa todos os DOCX de um diretório.")
    parser.add_argument("--saida-diretorio", help="Diretório de saída do modo lote.")
    parser.add_argument("--perfil", default=None,
                        help="Perfil documental. Se omitido, é deduzido do nome.")
    parser.add_argument("--minuta-mae", default=None,
                        help="Minuta-mãe de referência para comparação de timbre.")
    parser.add_argument("--campos", default=None,
                        help="JSON com os campos {{CAMPO}} a preencher.")
    parser.add_argument("--somente-auditoria", action="store_true",
                        help="Não grava nada; equivale a auditar_docx.py.")
    parser.add_argument("--preservar-conteudo", action="store_true", default=True,
                        help="Bloqueia a saída se o conteúdo mudar (padrão: ligado).")
    parser.add_argument("--sem-preservar-conteudo", dest="preservar_conteudo",
                        action="store_false",
                        help="Desliga o bloqueio. Use apenas com conferência humana.")
    parser.add_argument("--corrigir-numeracao", action="store_true",
                        help="Aplica a renumeração proposta, se for segura.")
    parser.add_argument("--validar-referencias-internas", action="store_true",
                        help="Bloqueia a renumeração que invalide referência interna.")
    parser.add_argument("--normalizar-cores", action="store_true",
                        help="Converte texto colorido em preto. NÃO usar em minuta "
                             "cujo vermelho marca campo a preencher.")
    parser.add_argument("--limpar-metadados", action="store_true",
                        help="Limpa autor/último editor do pacote.")
    parser.add_argument("--revisar-minuta-mae", action="store_true",
                        help="MODO REVISÃO: altera a minuta-mãe com backup, "
                             "versionamento e changelog.")
    parser.add_argument("--registrar-em-processo", default=None, metavar="PROCESSO",
                        help="entrega o documento formatado à Gestão Documental "
                             "(scripts/gestao_documental) como versão vigente.")
    parser.add_argument("--tipo-documento", default=None,
                        help="tipo documental do registro (TR, DFD, CONTRATO...). "
                             "Exigido por --registrar-em-processo.")
    parser.add_argument("--motivo-registro", default=None,
                        help="motivo da nova versão no manifesto do processo.")
    parser.add_argument("--saida-relatorio", default=None,
                        help="Caminho do relatório Markdown (JSON irmão automático).")
    return parser


def _saida_relatorio_padrao(saida: Path) -> Path:
    return saida.with_name(f"{saida.stem}_RELATORIO.md")


def main(argv: Optional[list[str]] = None) -> int:
    args = construir_parser().parse_args(argv)

    campos: Optional[dict[str, str]] = None
    if args.campos:
        campos = json.loads(Path(args.campos).read_text(encoding="utf-8"))
        if not isinstance(campos, dict):
            print("[ERRO] --campos deve conter um objeto JSON.", file=sys.stderr)
            return 2

    comuns = dict(
        perfil_id=args.perfil,
        minuta_mae=Path(args.minuta_mae) if args.minuta_mae else None,
        campos=campos,
        corrigir_numeracao=args.corrigir_numeracao,
        validar_referencias_internas=args.validar_referencias_internas,
        normalizar_cores=args.normalizar_cores,
        limpar_metadados_pessoais=args.limpar_metadados,
        preservar_conteudo=args.preservar_conteudo,
    )

    try:
        if args.diretorio:
            return _modo_lote(args, comuns)

        if not args.entrada:
            print("[ERRO] Informe --entrada ou --diretorio.", file=sys.stderr)
            return 2
        entrada = Path(args.entrada)

        if args.somente_auditoria:
            diagnostico = auditar_docx.auditar(
                entrada, args.perfil,
                Path(args.minuta_mae) if args.minuta_mae else None,
            )
        elif args.revisar_minuta_mae:
            comuns.pop("perfil_id")
            diagnostico = revisar_minuta_mae(entrada, args.perfil, **comuns)
        else:
            if not args.saida:
                print("[ERRO] Informe --saida.", file=sys.stderr)
                return 2
            diagnostico = formatar(entrada, Path(args.saida), **comuns)
    except (FileNotFoundError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2

    destino = Path(args.saida_relatorio) if args.saida_relatorio else (
        _saida_relatorio_padrao(Path(args.saida)) if args.saida else None
    )
    if destino:
        relatorio_docx.gravar(diagnostico, destino)
        print(f"Relatório: {destino}")
        print(f"JSON:      {destino.with_suffix('.json')}")
    else:
        print(relatorio_docx.render_markdown(diagnostico))

    print(f"\nArquivo final: {diagnostico.get('arquivo_final') or '(não gravado)'}")
    print(f"Status: {diagnostico['status']}")

    if args.registrar_em_processo:
        codigo = _registrar_no_processo(args, diagnostico)
        if codigo:
            return codigo
    return 0 if diagnostico.get("arquivo_final") or args.somente_auditoria else 1


def _registrar_no_processo(args, diagnostico: dict) -> int:
    """
    Entrega o documento formatado à Gestão Documental (item 26 do escopo).

    A formatação não escolhe onde o documento fica: ela produz o arquivo e o
    módulo de gestão decide se ele vira a versão vigente, arquiva a anterior e
    atualiza manifesto, log e painel. Documento não gravado (padronização
    bloqueada) não é registrado — não se versiona o que não existe.
    """
    arquivo_final = diagnostico.get("arquivo_final")
    if not arquivo_final:
        print("[AVISO] Nada a registrar: a padronização não gravou arquivo final.",
              file=sys.stderr)
        return 1
    if not args.tipo_documento:
        print("[ERRO] --registrar-em-processo exige --tipo-documento (ex.: TR).",
              file=sys.stderr)
        return 2

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gestao_documental"))
    from registrar_documento import registrar_saida_gerada  # noqa: E402

    status_padronizacao = str(diagnostico.get("status") or "")
    try:
        resultado = registrar_saida_gerada(
            args.registrar_em_processo,
            args.tipo_documento,
            arquivo_final,
            minuta_origem=args.minuta_mae,
            motivo=args.motivo_registro or "padronização documental aplicada",
            validacao={
                "conteudo": (
                    "aprovado"
                    if diagnostico.get("validacao_conteudo", {}).get("conteudo_preservado")
                    else "nao_executada"
                ),
                "formatacao": (
                    "aprovado" if status_padronizacao.upper().startswith("PADRONIZA")
                    and "RESSALVA" not in status_padronizacao.upper()
                    else "aprovado_com_ressalvas"
                ),
            },
        )
    except Exception as exc:  # noqa: BLE001 - a mensagem é o produto do CLI
        print(f"[ERRO] Registro no processo recusado: {exc}", file=sys.stderr)
        return 1

    print()
    print(resultado.texto())
    return 0


def _modo_lote(args, comuns) -> int:
    if not args.saida_diretorio:
        print("[ERRO] --diretorio exige --saida-diretorio.", file=sys.stderr)
        return 2
    origem = Path(args.diretorio)
    destino = Path(args.saida_diretorio)
    if destino.resolve() == origem.resolve():
        print("[ERRO] O diretório de saída não pode ser o de entrada.", file=sys.stderr)
        return 2
    destino.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(
        caminho for caminho in origem.glob("*.docx")
        if not caminho.name.startswith("~$")
    )
    if not arquivos:
        print(f"Nenhum DOCX em {origem}.")
        return 0

    falhas = 0
    for caminho in arquivos:
        saida = destino / f"{caminho.stem}_FORMATADO.docx"
        try:
            diagnostico = formatar(caminho, saida, **comuns)
        except (FileNotFoundError, ValueError, PermissionError, RuntimeError) as exc:
            print(f"[ERRO] {caminho.name}: {exc}")
            falhas += 1
            continue
        relatorio_docx.gravar(diagnostico, destino / f"{caminho.stem}_FORMATADO_RELATORIO.md")
        marcador = "OK " if diagnostico.get("arquivo_final") else "BLOQ"
        print(f"[{marcador}] {caminho.name} -> {diagnostico['status']} "
              f"(nota {diagnostico['nota_padronizacao']}/100)")
        if not diagnostico.get("arquivo_final"):
            falhas += 1
    print(f"\n{len(arquivos) - falhas}/{len(arquivos)} documento(s) formatado(s).")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
