#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auditar_docx.py — MODO AUDITORIA DE FORMATAÇÃO.

Analisa um DOCX **sem alterá-lo** e produz diagnóstico completo: fontes,
tamanhos, cores, estilos, formatação direta, numeração, listas, recuos,
tabelas, paginação, cabeçalho/rodapé, campos pendentes, comentários e controle
de alterações.

Uso:
    python scripts/docx_cmi/auditar_docx.py \
      --entrada documento.docx --perfil tr --saida-relatorio relatorio.md
"""
from __future__ import annotations

import argparse
import collections
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import cabecalho_rodape_docx
import numeracao_docx
import tabelas_docx
import validar_conteudo_docx
from estilos_docx import (
    ESTILOS_GENERICOS,
    PAPEL_CABECALHO_TABELA,
    PAPEL_TABELA,
    carregar_padrao,
    classificar_paragrafo,
    nome_do_estilo,
    perfil_por_arquivo,
)
from util_ooxml import (
    contagem_controle_alteracoes,
    contagem_texto_oculto,
    exigir_python_docx,
    iter_paragrafos_corpo,
    iter_tabelas,
    paragrafo_vazio,
    possui_parte,
    propriedades_pessoais,
    qn,
    quebras_de_pagina,
    texto_paragrafo,
)

STATUS_APROVADO = "APROVADO NA VALIDAÇÃO AUTOMÁTICA"
STATUS_RESSALVAS = "APROVADO COM RESSALVAS"
STATUS_CONFERENCIA = "EXIGE CONFERÊNCIA HUMANA"
STATUS_BLOQUEADO_CONTEUDO = "BLOQUEADO POR ALTERAÇÃO DE CONTEÚDO"
STATUS_BLOQUEADO_ESTRUTURA = "BLOQUEADO POR ERRO ESTRUTURAL"


def _papeis(documento, padrao) -> list[tuple[Any, str]]:
    """Classifica cada parágrafo do corpo (fora de tabela) em um papel."""
    paragrafos = list(documento.paragraphs)
    total = len(paragrafos)
    return [
        (p, classificar_paragrafo(p, i, total, padrao))
        for i, p in enumerate(paragrafos)
    ]


def _inventario_formatacao(documento, padrao) -> dict[str, Any]:
    """Fontes, tamanhos, cores e estilos efetivamente usados."""
    fontes: collections.Counter = collections.Counter()
    tamanhos: collections.Counter = collections.Counter()
    cores: collections.Counter = collections.Counter()
    estilos: collections.Counter = collections.Counter()
    runs_com_formatacao_direta = 0
    runs_totais = 0

    normal = documento.styles["Normal"].font
    fonte_padrao = normal.name or "(herdada do tema)"
    tamanho_padrao = round(normal.size.pt, 1) if normal.size else None

    for paragrafo in iter_paragrafos_corpo(documento):
        if not texto_paragrafo(paragrafo).strip():
            continue
        estilos[nome_do_estilo(paragrafo)] += 1
        for run in paragrafo.runs:
            if not (run.text or "").strip():
                continue
            runs_totais += 1
            direto = False
            if run.font.name:
                fontes[run.font.name] += 1
                direto = True
            else:
                fontes[f"{fonte_padrao} (estilo)"] += 1
            if run.font.size:
                tamanhos[round(run.font.size.pt, 1)] += 1
                direto = True
            elif tamanho_padrao is not None:
                tamanhos[f"{tamanho_padrao} (estilo)"] += 1
            cor = run.font.color
            if cor is not None and cor.type is not None and cor.rgb is not None:
                cores[str(cor.rgb)] += 1
                direto = True
            if direto:
                runs_com_formatacao_direta += 1

    return {
        "fonte_do_estilo_normal": fonte_padrao,
        "tamanho_do_estilo_normal": tamanho_padrao,
        "fontes": dict(fontes),
        "tamanhos": {str(k): v for k, v in tamanhos.items()},
        "cores": dict(cores),
        "estilos": dict(estilos),
        "runs_totais": runs_totais,
        "runs_com_formatacao_direta": runs_com_formatacao_direta,
        "proporcao_formatacao_direta": (
            round(runs_com_formatacao_direta / runs_totais, 3) if runs_totais else 0.0
        ),
    }


def _problemas_paginacao(documento, padrao, papeis) -> list[str]:
    problemas: list[str] = []
    vazios_seguidos = 0
    maximo = 0
    for paragrafo in documento.paragraphs:
        if paragrafo_vazio(paragrafo):
            vazios_seguidos += 1
            maximo = max(maximo, vazios_seguidos)
        else:
            vazios_seguidos = 0
    limite = padrao.base["paginacao"].get("maximo_paragrafos_vazios_consecutivos", 1)
    if maximo > limite:
        problemas.append(
            f"Há sequência de {maximo} parágrafos vazios usados como espaçamento "
            f"(limite do padrão: {limite})."
        )

    quebras_seguidas = 0
    for paragrafo in documento.paragraphs:
        n = quebras_de_pagina(paragrafo)
        if n > 1:
            problemas.append(
                f"Parágrafo com {n} quebras de página manuais consecutivas."
            )
        if n and paragrafo_vazio(paragrafo):
            quebras_seguidas += 1
    if quebras_seguidas > 3:
        problemas.append(
            f"{quebras_seguidas} quebras de página manuais em parágrafos vazios — "
            "verificar se há páginas em branco."
        )

    titulos_soltos = 0
    for indice, (paragrafo, papel) in enumerate(papeis):
        if papel not in ("titulo_documento", "titulo_1", "titulo_2", "titulo_3"):
            continue
        if paragrafo.paragraph_format.keep_with_next is not True:
            titulos_soltos += 1
    if titulos_soltos:
        problemas.append(
            f"{titulos_soltos} título(s) sem 'manter com o próximo' — risco de "
            "título isolado no fim da página."
        )

    desligado = sum(
        1 for paragrafo in documento.paragraphs
        if paragrafo.paragraph_format.widow_control is False
    )
    if desligado:
        problemas.append(
            f"{desligado} parágrafo(s) com controle de linhas órfãs/viúvas desligado."
        )
    return problemas


def _problemas_estrutura(documento, padrao, papeis) -> list[str]:
    problemas: list[str] = []
    sem_estilo = sum(
        1 for paragrafo, papel in papeis
        if papel in ("titulo_documento", "titulo_1", "titulo_2", "titulo_3")
        and nome_do_estilo(paragrafo) in ESTILOS_GENERICOS
    )
    if sem_estilo:
        problemas.append(
            f"{sem_estilo} título(s) sem estilo nomeado — formatados como texto comum."
        )

    recuos: collections.Counter = collections.Counter()
    for paragrafo, papel in papeis:
        if papel != "corpo" or not texto_paragrafo(paragrafo).strip():
            continue
        pf = paragrafo.paragraph_format
        recuos[(
            round(pf.left_indent.cm, 2) if pf.left_indent else None,
            round(pf.first_line_indent.cm, 2) if pf.first_line_indent else None,
        )] += 1
    if len(recuos) > 3:
        problemas.append(
            f"{len(recuos)} combinações diferentes de recuo em parágrafos de corpo — "
            "recuos inconsistentes."
        )

    espacamentos = {
        paragrafo.paragraph_format.line_spacing
        for paragrafo, papel in papeis
        if papel == "corpo" and paragrafo.paragraph_format.line_spacing is not None
    }
    if len(espacamentos) > 2:
        problemas.append(
            f"{len(espacamentos)} valores diferentes de espaçamento entre linhas no corpo."
        )
    exatos = [e for e in espacamentos if not isinstance(e, float)]
    if exatos:
        problemas.append(
            f"{len(exatos)} parágrafo(s) com espaçamento entre linhas EXATO "
            "(herdado de conversão de formato) em vez de múltiplo."
        )
    return problemas


def _problemas_pagina(documento, padrao) -> list[str]:
    problemas: list[str] = []
    esperado = padrao.base["pagina"]
    for indice, secao in enumerate(documento.sections):
        atual = {
            "margem_superior_cm": round(secao.top_margin.cm, 2),
            "margem_inferior_cm": round(secao.bottom_margin.cm, 2),
            "margem_esquerda_cm": round(secao.left_margin.cm, 2),
            "margem_direita_cm": round(secao.right_margin.cm, 2),
        }
        divergentes = [
            f"{chave}={valor} (padrão {esperado[chave]})"
            for chave, valor in atual.items()
            if abs(valor - float(esperado[chave])) > 0.05
        ]
        if divergentes:
            problemas.append(
                f"Seção {indice}: margens divergem do padrão — "
                + "; ".join(divergentes)
                + ". Não corrigido automaticamente: a margem superior acomoda o brasão."
            )
    return problemas


def auditar(caminho: Path, perfil_id: Optional[str] = None,
            minuta_mae: Optional[Path] = None) -> dict[str, Any]:
    """Executa a auditoria completa e devolve o diagnóstico estruturado."""
    exigir_python_docx()
    from docx import Document

    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if perfil_id is None:
        perfil_id = perfil_por_arquivo(caminho.name) or "generico"
    padrao = carregar_padrao(perfil_id)

    documento = Document(str(caminho))
    papeis = _papeis(documento, padrao)
    paragrafos_corpo = list(documento.paragraphs)

    clausulas_extenso = padrao.perfil.get("titulos") == "clausulas_por_extenso"
    diag_num = numeracao_docx.analisar(paragrafos_corpo, clausulas_extenso)
    proposta = numeracao_docx.propor_renumeracao(diag_num)
    afetadas = numeracao_docx.referencias_afetadas(diag_num, proposta)
    fragmentacao = numeracao_docx.detectar_fragmentacao(paragrafos_corpo)

    diag_tabelas = tabelas_docx.diagnosticar(documento, padrao)
    resumo_hf = cabecalho_rodape_docx.resumir(documento, caminho)
    pendencias = validar_conteudo_docx.levantar_pendencias(documento)

    tem_comentarios = possui_parte(caminho, "word/comments.xml")
    revisoes = contagem_controle_alteracoes(caminho)
    ocultos = contagem_texto_oculto(caminho)
    pessoais = propriedades_pessoais(caminho)

    inventario = _inventario_formatacao(documento, padrao)
    problemas_paginacao = _problemas_paginacao(documento, padrao, papeis)
    problemas_estrutura = _problemas_estrutura(documento, padrao, papeis)
    problemas_pagina = _problemas_pagina(documento, padrao)
    problemas_tabelas = [p for d in diag_tabelas for p in d.problemas]

    divergencia_minuta: list[str] = []
    if minuta_mae is not None:
        divergencia_minuta = cabecalho_rodape_docx.comparar_com_minuta_mae(
            caminho, Path(minuta_mae)
        )

    fontes_fora = sorted(
        f for f in inventario["fontes"]
        if "(estilo)" not in f and f not in padrao.fontes_toleradas
    )

    corrigiveis: list[str] = []
    manuais: list[str] = []
    if fontes_fora:
        corrigiveis.append(f"Normalizar fontes fora do padrão: {', '.join(fontes_fora)}.")
    if problemas_estrutura:
        corrigiveis.append("Aplicar estilos nomeados CMI e uniformizar recuos/espaçamentos.")
    if problemas_tabelas:
        corrigiveis.append("Ajustar largura, cabeçalho repetido e quebra de linhas das tabelas.")
    if problemas_paginacao:
        corrigiveis.append("Aplicar controle de paginação (manter com o próximo, órfãs/viúvas).")
    for problema in diag_num.problemas:
        (corrigiveis if problema.corrigivel else manuais).append(
            f"Numeração — {problema.tipo}: {problema.detalhe}"
        )
    if afetadas:
        manuais.append(
            "Referências internas seriam invalidadas pela renumeração: "
            + "; ".join(afetadas)
        )
    if fragmentacao:
        manuais.append(f"Fragmentação: {fragmentacao}")
    if pendencias.total:
        manuais.append(
            f"{pendencias.total} pendência(s) de preenchimento a resolver antes da assinatura."
        )
    if tem_comentarios:
        manuais.append("O documento contém comentários internos (word/comments.xml).")
    if revisoes:
        manuais.append(f"O documento contém {revisoes} marca(s) de controle de alterações.")
    if ocultos:
        manuais.append(f"O documento contém {ocultos} trecho(s) de texto oculto.")
    if pessoais:
        manuais.append(
            "Metadados pessoais no pacote: "
            + ", ".join(f"{k}={v}" for k, v in sorted(pessoais.items()))
            + " (limpeza só com --limpar-metadados)."
        )
    if problemas_pagina:
        manuais.append("Margens divergentes do padrão — exigem decisão humana.")
    if resumo_hf.divergencia_entre_secoes:
        manuais.append(
            "Cabeçalho/rodapé divergem entre seções: "
            + "; ".join(resumo_hf.divergencia_entre_secoes)
        )
    if divergencia_minuta:
        manuais.append(
            "Divergência em relação à minuta-mãe: " + "; ".join(divergencia_minuta)
        )

    nota, status = _nota_e_status(
        inventario=inventario,
        fontes_fora=fontes_fora,
        problemas_numeracao=diag_num.problemas,
        problemas_tabelas=problemas_tabelas,
        problemas_paginacao=problemas_paginacao,
        problemas_estrutura=problemas_estrutura,
        pendencias=pendencias,
        tem_comentarios=tem_comentarios,
        revisoes=revisoes,
        divergencia_minuta=divergencia_minuta,
    )

    return {
        "documento": str(caminho),
        "minuta_mae": str(minuta_mae) if minuta_mae else None,
        "perfil": perfil_id,
        "perfil_nome": padrao.perfil.get("nome", perfil_id),
        "data": date.today().isoformat(),
        "modo": "auditoria",
        "inventario": inventario,
        "fontes_fora_do_padrao": fontes_fora,
        "numeracao": {
            "itens": len(diag_num.itens),
            "problemas": [
                {"tipo": p.tipo, "paragrafo": p.indice_paragrafo, "rotulo": p.rotulo,
                 "detalhe": p.detalhe, "corrigivel": p.corrigivel, "sugestao": p.sugestao}
                for p in diag_num.problemas
            ],
            "proposta_renumeracao": {
                str(k): {"antes": v[0], "depois": v[1]} for k, v in proposta.items()
            },
            "referencias_internas": len(diag_num.referencias_internas),
            "referencias_afetadas": afetadas,
            "mistura_manual_automatica": diag_num.mistura_manual_automatica,
            "fragmentacao": fragmentacao,
        },
        "tabelas": {
            "total": len(diag_tabelas),
            "problemas": problemas_tabelas,
            "detalhe": [
                {"indice": d.indice, "linhas": d.linhas, "colunas": d.colunas,
                 "largura_twips": d.largura_twips, "area_util_twips": d.largura_util_twips,
                 "excede_margens": d.excede_margens,
                 "cabecalho_repetido": d.cabecalho_repetido,
                 "linhas_divisiveis": d.linhas_divisiveis,
                 "celulas_mescladas": d.celulas_mescladas}
                for d in diag_tabelas
            ],
        },
        "paginacao": {"problemas": problemas_paginacao},
        "estrutura": {"problemas": problemas_estrutura},
        "pagina": {"problemas": problemas_pagina},
        "cabecalho_rodape": {
            "secoes": resumo_hf.secoes,
            "imagens_cabecalho": resumo_hf.imagens_cabecalho,
            "imagens_rodape": resumo_hf.imagens_rodape,
            "textos_cabecalho": resumo_hf.textos_cabecalho,
            "textos_rodape": resumo_hf.textos_rodape,
            "campo_pagina_no_rodape": resumo_hf.campo_pagina_no_rodape,
            "divergencia_entre_secoes": resumo_hf.divergencia_entre_secoes,
            "divergencia_minuta_mae": divergencia_minuta,
            "partes_protegidas": len(resumo_hf.partes),
        },
        "pendencias": {
            "campos_pendentes": pendencias.campos_pendentes,
            "blocos_ou": pendencias.blocos_ou,
            "opcoes_nao_marcadas": pendencias.opcoes_nao_marcadas,
            "texto_destacado": pendencias.texto_destacado,
            "total": pendencias.total,
        },
        "revisao": {
            "comentarios": tem_comentarios,
            "controle_alteracoes": revisoes,
            "texto_oculto": ocultos,
            "propriedades_pessoais": pessoais,
        },
        "correcoes_automaticas_possiveis": corrigiveis,
        "correcoes_que_exigem_humano": manuais,
        "nota_padronizacao": nota,
        "status": status,
    }


def _nota_e_status(**dados) -> tuple[int, str]:
    """Nota 0–100 de padronização e status resultante."""
    nota = 100
    nota -= 8 * len(dados["fontes_fora"])
    nota -= min(15, 3 * len(dados["problemas_numeracao"]))
    nota -= min(15, 3 * len(dados["problemas_tabelas"]))
    nota -= min(10, 3 * len(dados["problemas_paginacao"]))
    nota -= min(15, 4 * len(dados["problemas_estrutura"]))
    direta = dados["inventario"]["proporcao_formatacao_direta"]
    if direta > 0.5:
        nota -= 10
    elif direta > 0.25:
        nota -= 5
    nota -= min(15, dados["pendencias"].total)
    if dados["tem_comentarios"]:
        nota -= 5
    if dados["revisoes"]:
        nota -= 5
    nota -= 5 * len(dados["divergencia_minuta"])
    nota = max(0, min(100, nota))

    if dados["divergencia_minuta"]:
        return nota, STATUS_BLOQUEADO_ESTRUTURA
    if dados["pendencias"].total or dados["tem_comentarios"] or dados["revisoes"]:
        return nota, STATUS_CONFERENCIA
    if nota >= 90:
        return nota, STATUS_APROVADO
    if nota >= 70:
        return nota, STATUS_RESSALVAS
    return nota, STATUS_CONFERENCIA


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MODO AUDITORIA DE FORMATAÇÃO — analisa um DOCX sem alterá-lo."
    )
    parser.add_argument("--entrada", required=True, help="DOCX a auditar.")
    parser.add_argument("--perfil", default=None,
                        help="Perfil documental (tr, contrato, etp...). "
                             "Se omitido, é deduzido do nome do arquivo.")
    parser.add_argument("--minuta-mae", default=None,
                        help="Minuta-mãe de referência para comparar timbre e estrutura.")
    parser.add_argument("--saida-relatorio", default=None,
                        help="Caminho do relatório Markdown. O JSON usa o mesmo "
                             "nome com extensão .json.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    import relatorio_docx

    args = construir_parser().parse_args(argv)
    try:
        diagnostico = auditar(
            Path(args.entrada),
            args.perfil,
            Path(args.minuta_mae) if args.minuta_mae else None,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2

    markdown = relatorio_docx.render_markdown(diagnostico)
    if args.saida_relatorio:
        destino = Path(args.saida_relatorio)
        relatorio_docx.gravar(diagnostico, destino)
        print(f"Relatório gravado em: {destino}")
        print(f"JSON gravado em:      {destino.with_suffix('.json')}")
    else:
        print(markdown)
    print(f"\nNota de padronização: {diagnostico['nota_padronizacao']}/100")
    print(f"Status: {diagnostico['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
