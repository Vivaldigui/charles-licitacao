#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do Módulo de Padronização e Formatação Documental.

Cobrem os 12 testes obrigatórios do escopo do módulo (item 28). Os testes 5, 6,
11 e 12 rodam sobre as minutas-mãe reais de `05_minutas/`; os demais usam
documentos sintéticos construídos no próprio teste.

Rodar:
    python -m pytest 99_testes/padronizacao_documental/ -v
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

docx = pytest.importorskip("docx", reason="python-docx não instalado (requirements-docx.txt)")

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

import auditar_docx
import cabecalho_rodape_docx
import estilos_docx
import formatar_docx
import numeracao_docx
import relatorio_docx
import util_ooxml
import validar_conteudo_docx

RAIZ = Path(__file__).resolve().parents[2]
MINUTAS = sorted((RAIZ / "05_minutas").glob("*/*_MINUTA_MAE.docx"))


# --------------------------------------------------------------------------- #
# Fábricas de documentos sintéticos
# --------------------------------------------------------------------------- #

def _salvar(documento, tmp_path: Path, nome: str) -> Path:
    caminho = tmp_path / nome
    documento.save(str(caminho))
    return caminho


def doc_fontes_misturadas(tmp_path: Path) -> Path:
    documento = Document()
    dados = [
        ("TERMO DE REFERÊNCIA", "Arial", 18, WD_ALIGN_PARAGRAPH.CENTER),
        ("Parágrafo de corpo redigido em Calibri no tamanho padrão da Câmara, "
         "com extensão suficiente para ser tratado como texto corrido.",
         "Calibri", 12, None),
        ("Parágrafo de corpo redigido em Times New Roman fora do padrão, também "
         "com extensão suficiente para ser tratado como texto corrido do documento.",
         "Times New Roman", 14, None),
        ("Parágrafo de corpo em Verdana de tamanho divergente, igualmente longo "
         "para que o classificador o trate como corpo e não como título.",
         "Verdana", 9, None),
    ]
    for texto, fonte, tamanho, alinhamento in dados:
        paragrafo = documento.add_paragraph()
        paragrafo.alignment = alinhamento
        run = paragrafo.add_run(texto)
        run.font.name = fonte
        run.font.size = Pt(tamanho)
    return _salvar(documento, tmp_path, "fontes_misturadas.docx")


def doc_numeracao_incorreta(tmp_path: Path) -> Path:
    documento = Document()
    documento.add_paragraph("TERMO DE REFERÊNCIA")
    for rotulo in ["1.", "2.", "2.1.", "4.", "4.1.", "4.1."]:
        documento.add_paragraph(f"{rotulo} Descrição do tópico {rotulo}")
    return _salvar(documento, tmp_path, "numeracao.docx")


def doc_marcador_dividido(tmp_path: Path) -> Path:
    """`{{OBJETO}}` quebrado em cinco runs, como o Word costuma gravar."""
    documento = Document()
    paragrafo = documento.add_paragraph()
    for pedaco in ["Contratação de ", "{{", "OBJE", "TO", "}}", " para a Câmara."]:
        run = paragrafo.add_run(pedaco)
        run.bold = True
        run.font.size = Pt(12)
    return _salvar(documento, tmp_path, "marcador_dividido.docx")


def doc_tabela_extensa(tmp_path: Path) -> Path:
    documento = Document()
    documento.add_paragraph("QUADRO DE ITENS")
    tabela = documento.add_table(rows=4, cols=5)
    for coluna in tabela.columns:
        coluna.width = Cm(6)  # 5 x 6 cm = 30 cm > área útil de A4
    cabecalhos = ["Item", "Descrição", "Unidade", "Quantidade", "Valor"]
    for indice, texto in enumerate(cabecalhos):
        tabela.rows[0].cells[indice].text = texto
    for linha in range(1, 4):
        for coluna in range(5):
            tabela.rows[linha].cells[coluna].text = f"celula-{linha}-{coluna}"
    return _salvar(documento, tmp_path, "tabela_extensa.docx")


def doc_rodape_com_paginacao(tmp_path: Path) -> Path:
    from docx.oxml.ns import qn as _qn

    documento = Document()
    documento.add_paragraph("Documento com rodapé institucional e paginação.")
    rodape = documento.sections[0].footer
    paragrafo = rodape.paragraphs[0]
    paragrafo.add_run("Câmara Municipal de Itanhandu — página ")
    run = paragrafo.add_run()
    campo = run._r.makeelement(_qn("w:fldSimple"), {})
    campo.set(_qn("w:instr"), " PAGE ")
    run._r.addnext(campo)
    return _salvar(documento, tmp_path, "rodape_paginacao.docx")


def doc_titulo_no_fim(tmp_path: Path) -> Path:
    documento = Document()
    for _ in range(3):
        documento.add_paragraph(
            "Parágrafo de corpo com extensão suficiente para ocupar espaço na "
            "página e empurrar o título para o fim da mancha gráfica do texto."
        )
    documento.add_paragraph("3. OBRIGAÇÕES DA CONTRATADA")
    documento.add_paragraph(
        "Parágrafo que deve permanecer junto ao título imediatamente anterior, "
        "de modo que o título nunca fique isolado no rodapé da página."
    )
    return _salvar(documento, tmp_path, "titulo_fim.docx")


def doc_campos_pendentes(tmp_path: Path) -> Path:
    documento = Document()
    documento.add_paragraph("Objeto: {{OBJETO}}")
    documento.add_paragraph("Prazo: [PREENCHER: informar o prazo de entrega]")
    documento.add_paragraph("Vigência: ____________")
    documento.add_paragraph("Garantia: (definir o prazo de garantia)")
    documento.add_paragraph("OU")
    documento.add_paragraph("(  ) Opção não marcada pelo agente de contratação")
    paragrafo = documento.add_paragraph()
    run = paragrafo.add_run("Instrução de preenchimento em vermelho.")
    run.font.color.rgb = RGBColor.from_string("FF0000")
    return _salvar(documento, tmp_path, "campos_pendentes.docx")


# --------------------------------------------------------------------------- #
# Teste 1 — Fontes misturadas
# --------------------------------------------------------------------------- #

def test_1_fontes_misturadas_sao_normalizadas(tmp_path):
    entrada = doc_fontes_misturadas(tmp_path)
    saida = tmp_path / "saida.docx"
    diagnostico = formatar_docx.formatar(entrada, saida, "tr")

    assert diagnostico["arquivo_final"], diagnostico["status"]
    assert set(diagnostico["fontes_fora_do_padrao"]) == {"Arial", "Times New Roman", "Verdana"}

    documento = Document(str(saida))
    fontes = {
        run.font.name
        for paragrafo in documento.paragraphs
        for run in paragrafo.runs
        if run.text.strip() and run.font.name
    }
    assert fontes <= {"Calibri"}, f"Fonte fora do padrão remanescente: {fontes}"

    tamanhos = {
        run.font.size.pt
        for paragrafo in documento.paragraphs
        for run in paragrafo.runs
        if run.text.strip() and run.font.size
    }
    assert tamanhos <= {12.0, 14.0}, f"Tamanhos inesperados: {tamanhos}"
    assert diagnostico["validacao_conteudo"]["conteudo_preservado"]
    assert any("fonte" in c for c in diagnostico["correcoes_aplicadas"])


# --------------------------------------------------------------------------- #
# Teste 2 — Numeração incorreta
# --------------------------------------------------------------------------- #

def test_2_numeracao_incorreta_e_detectada(tmp_path):
    entrada = doc_numeracao_incorreta(tmp_path)
    diagnostico = auditar_docx.auditar(entrada, "tr")
    tipos = {p["tipo"] for p in diagnostico["numeracao"]["problemas"]}

    assert "numero_pulado" in tipos          # 2. -> 4.
    assert "numero_duplicado" in tipos       # 4.1. repetido
    assert diagnostico["numeracao"]["proposta_renumeracao"]


def test_2b_renumeracao_corrige_e_preserva_o_texto(tmp_path):
    entrada = doc_numeracao_incorreta(tmp_path)
    saida = tmp_path / "renumerado.docx"
    diagnostico = formatar_docx.formatar(
        entrada, saida, "tr", corrigir_numeracao=True,
        validar_referencias_internas=True,
    )
    assert diagnostico["arquivo_final"], diagnostico["correcoes_nao_aplicadas"]

    documento = Document(str(saida))
    rotulos = [
        numeracao_docx.RE_ROTULO.match(p.text).group(2)
        for p in documento.paragraphs
        if numeracao_docx.RE_ROTULO.match(p.text)
    ]
    assert rotulos == ["1", "2", "2.1", "3", "3.1", "3.2"], rotulos
    # A renumeração é a única mudança de texto e vem classificada como autorizada.
    for diferenca in diagnostico["validacao_conteudo"]["diferencas"]:
        assert diferenca["autorizada"], diferenca
    assert diagnostico["validacao_conteudo"]["conteudo_preservado"]


def test_2c_perfil_contrato_recusa_renumeracao_automatica(tmp_path):
    entrada = doc_numeracao_incorreta(tmp_path)
    saida = tmp_path / "contrato.docx"
    diagnostico = formatar_docx.formatar(
        entrada, saida, "contrato", corrigir_numeracao=True
    )
    assert any("proíbe renumeração automática" in item
               for item in diagnostico["correcoes_nao_aplicadas"])
    documento = Document(str(saida))
    assert any(p.text.startswith("4.") for p in documento.paragraphs)


def test_2d_numeracao_juridica_nao_e_tocada():
    protegidos = [
        "Art. 75, II, da Lei nº 14.133/2021 autoriza a dispensa.",
        "1. Lei nº 14.133/2021 — disposições preliminares",
        "CLÁUSULA PRIMEIRA — DO OBJETO",
        "Processo nº 12/2026 da Câmara Municipal.",
    ]
    for texto in protegidos:
        assert numeracao_docx.eh_numeracao_protegida(texto), texto


def test_2e_referencia_interna_bloqueia_renumeracao(tmp_path):
    documento = Document()
    for rotulo in ["1.", "2.", "4."]:
        documento.add_paragraph(f"{rotulo} Tópico {rotulo}")
    documento.add_paragraph("O prazo observará o disposto no item 4.")
    entrada = _salvar(documento, tmp_path, "ref.docx")

    saida = tmp_path / "ref_saida.docx"
    diagnostico = formatar_docx.formatar(
        entrada, saida, "tr", corrigir_numeracao=True,
        validar_referencias_internas=True,
    )
    assert any("Referências internas" in item
               for item in diagnostico["correcoes_nao_aplicadas"])
    assert "4" in [p.text.split(".")[0] for p in Document(str(saida)).paragraphs]


# --------------------------------------------------------------------------- #
# Teste 3 — Marcador dividido em runs
# --------------------------------------------------------------------------- #

def test_3_marcador_dividido_entre_runs(tmp_path):
    entrada = doc_marcador_dividido(tmp_path)
    saida = tmp_path / "preenchido.docx"
    diagnostico = formatar_docx.formatar(
        entrada, saida, "tr", campos={"OBJETO": "recarga de extintores"}
    )
    assert diagnostico["arquivo_final"], diagnostico["status"]

    documento = Document(str(saida))
    texto = documento.paragraphs[0].text
    assert texto == "Contratação de recarga de extintores para a Câmara."
    assert "{{" not in texto and "}}" not in texto
    # A formatação-base do campo foi preservada (negrito do run de origem).
    assert all(run.bold for run in documento.paragraphs[0].runs if run.text)
    assert not validar_conteudo_docx.levantar_pendencias(documento).campos_pendentes


def test_3b_substituicao_sem_criar_novos_runs(tmp_path):
    entrada = doc_marcador_dividido(tmp_path)
    documento = Document(str(entrada))
    antes = len(documento.paragraphs[0].runs)
    formatar_docx.preencher_campos(documento, {"OBJETO": "objeto muito mais longo que o marcador"})
    assert len(documento.paragraphs[0].runs) == antes


# --------------------------------------------------------------------------- #
# Teste 4 — Tabela extensa
# --------------------------------------------------------------------------- #

def test_4_tabela_extensa_e_ajustada(tmp_path):
    entrada = doc_tabela_extensa(tmp_path)
    diagnostico_inicial = auditar_docx.auditar(entrada, "tr")
    assert diagnostico_inicial["tabelas"]["detalhe"][0]["excede_margens"]

    saida = tmp_path / "tabela.docx"
    diagnostico = formatar_docx.formatar(entrada, saida, "tr")
    assert diagnostico["arquivo_final"], diagnostico["status"]

    depois = auditar_docx.auditar(saida, "tr")
    detalhe = depois["tabelas"]["detalhe"][0]
    assert not detalhe["excede_margens"]
    assert detalhe["cabecalho_repetido"]
    assert detalhe["linhas_divisiveis"] == 0

    documento = Document(str(saida))
    tabela = documento.tables[0]
    assert len(tabela.rows) == 4 and len(tabela.columns) == 5
    assert tabela.rows[0].cells[1].text == "Descrição"
    assert tabela.rows[3].cells[4].text == "celula-3-4"
    assert diagnostico["validacao_conteudo"]["conteudo_preservado"]
    assert diagnostico["validacao_conteudo"]["celulas_antes"] == \
        diagnostico["validacao_conteudo"]["celulas_depois"]


# --------------------------------------------------------------------------- #
# Teste 5 — Cabeçalho com brasão
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
def test_5_cabecalho_com_brasao_e_preservado(tmp_path):
    minuta = RAIZ / "05_minutas" / "TR" / "TR_MINUTA_MAE.docx"
    saida = tmp_path / "tr.docx"
    diagnostico = formatar_docx.formatar(minuta, saida, "tr", minuta_mae=minuta)
    assert diagnostico["arquivo_final"], diagnostico["status"]

    intactas, divergencias = cabecalho_rodape_docx.partes_protegidas_intactas(minuta, saida)
    assert intactas, divergencias

    antes = cabecalho_rodape_docx.resumir(Document(str(minuta)))
    depois = cabecalho_rodape_docx.resumir(Document(str(saida)))
    assert depois.imagens_cabecalho == antes.imagens_cabecalho > 0
    assert depois.imagens_rodape == antes.imagens_rodape > 0
    assert not cabecalho_rodape_docx.comparar_com_minuta_mae(saida, minuta)

    # As dimensões das imagens do cabeçalho não podem mudar.
    with zipfile.ZipFile(minuta) as za, zipfile.ZipFile(saida) as zb:
        assert (util_ooxml.assinatura_semantica_cabecalho(za.read("word/header1.xml"))
                == util_ooxml.assinatura_semantica_cabecalho(zb.read("word/header1.xml")))


def test_5b_alteracao_de_imagem_do_cabecalho_e_detectada():
    """A assinatura semântica precisa ACUSAR perda real de brasão."""
    original = (b'<w:hdr><w:p><w:r><w:t>CAMARA</w:t></w:r>'
                b'<w:drawing><wp:extent cx="100" cy="200"/>'
                b'<a:blip r:embed="rId1"/></w:drawing></w:p></w:hdr>')
    sem_imagem = b'<w:hdr><w:p><w:r><w:t>CAMARA</w:t></w:r></w:p></w:hdr>'
    redimensionada = original.replace(b'cx="100" cy="200"', b'cx="50" cy="100"')
    reserializada = original.replace(b"<w:hdr>", b"<w:hdr >")

    assinar = util_ooxml.assinatura_semantica_cabecalho
    assert assinar(original) != assinar(sem_imagem)
    assert assinar(original) != assinar(redimensionada)
    assert assinar(original) == assinar(reserializada)


# --------------------------------------------------------------------------- #
# Teste 6 — Rodapé com paginação
# --------------------------------------------------------------------------- #

def test_6_rodape_com_campo_de_pagina_e_preservado(tmp_path):
    entrada = doc_rodape_com_paginacao(tmp_path)
    assert cabecalho_rodape_docx.resumir(Document(str(entrada))).campo_pagina_no_rodape

    saida = tmp_path / "rodape.docx"
    diagnostico = formatar_docx.formatar(entrada, saida, "generico")
    assert diagnostico["arquivo_final"], diagnostico["status"]

    resumo = cabecalho_rodape_docx.resumir(Document(str(saida)))
    assert resumo.campo_pagina_no_rodape
    assert any("Itanhandu" in texto for texto in resumo.textos_rodape)
    intactas, divergencias = cabecalho_rodape_docx.partes_protegidas_intactas(entrada, saida)
    assert intactas, divergencias


# --------------------------------------------------------------------------- #
# Teste 7 — Título no fim da página
# --------------------------------------------------------------------------- #

def test_7_titulo_fica_junto_do_proximo_paragrafo(tmp_path):
    entrada = doc_titulo_no_fim(tmp_path)
    saida = tmp_path / "titulo.docx"
    diagnostico = formatar_docx.formatar(entrada, saida, "tr")
    assert diagnostico["arquivo_final"], diagnostico["status"]

    documento = Document(str(saida))
    titulo = next(p for p in documento.paragraphs
                  if p.text.startswith("3. OBRIGAÇÕES"))
    assert titulo.paragraph_format.keep_with_next is True
    assert titulo.paragraph_format.keep_together is True
    assert "CMI Titulo" in (titulo.style.name or "")


# --------------------------------------------------------------------------- #
# Teste 8 — Campos pendentes
# --------------------------------------------------------------------------- #

def test_8_campos_pendentes_sao_identificados_e_bloqueiam_a_conclusao(tmp_path):
    entrada = doc_campos_pendentes(tmp_path)
    diagnostico = auditar_docx.auditar(entrada, "tr")
    pendencias = diagnostico["pendencias"]

    achados = " ".join(pendencias["campos_pendentes"])
    assert "{{OBJETO}}" in achados
    assert "[PREENCHER" in achados
    assert "____" in achados
    assert "definir" in achados
    assert pendencias["blocos_ou"]
    assert pendencias["opcoes_nao_marcadas"]
    assert pendencias["texto_destacado"]
    assert diagnostico["status"] == auditar_docx.STATUS_CONFERENCIA


def test_8b_vermelho_institucional_nao_e_alterado_por_padrao(tmp_path):
    entrada = doc_campos_pendentes(tmp_path)
    saida = tmp_path / "vermelho.docx"
    formatar_docx.formatar(entrada, saida, "contrato")
    documento = Document(str(saida))
    cores = {
        str(run.font.color.rgb)
        for paragrafo in documento.paragraphs
        for run in paragrafo.runs
        if run.font.color is not None and run.font.color.type is not None
        and run.font.color.rgb is not None
    }
    assert "FF0000" in cores, "O vermelho de campo a preencher não pode ser apagado."


# --------------------------------------------------------------------------- #
# Teste 9 — Preservação de conteúdo
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
@pytest.mark.parametrize("minuta", MINUTAS, ids=lambda p: p.stem)
def test_9_conteudo_preservado_em_todas_as_minutas(minuta, tmp_path):
    perfil = estilos_docx.perfil_por_arquivo(minuta.name) or "generico"
    saida = tmp_path / f"{minuta.stem}.docx"
    diagnostico = formatar_docx.formatar(minuta, saida, perfil)
    validacao = diagnostico["validacao_conteudo"]

    assert validacao["conteudo_preservado"], [
        d for d in validacao["diferencas"] if not d["autorizada"]
    ]
    assert validacao["partes_protegidas_intactas"], \
        validacao["divergencias_partes_protegidas"]
    assert validacao["celulas_antes"] == validacao["celulas_depois"]
    assert diagnostico["arquivo_final"]


def test_9b_alteracao_de_conteudo_bloqueia_a_saida(tmp_path):
    """A validação precisa realmente BLOQUEAR quando o texto muda."""
    documento = Document()
    documento.add_paragraph("Valor global de R$ 10.000,00 conforme a proposta.")
    entrada = _salvar(documento, tmp_path, "valor.docx")

    antes = validar_conteudo_docx.extrair(Document(str(entrada)))
    adulterado = Document(str(entrada))
    adulterado.paragraphs[0].runs[0].text = "Valor global de R$ 90.000,00 conforme a proposta."
    depois = validar_conteudo_docx.extrair(adulterado)

    resultado = validar_conteudo_docx.comparar(antes, depois)
    assert not resultado.conteudo_preservado
    assert resultado.nao_autorizadas[0].tipo == "texto_alterado"


def test_9c_perda_de_clausula_e_detectada(tmp_path):
    documento = Document()
    documento.add_paragraph("CLÁUSULA PRIMEIRA — DO OBJETO")
    documento.add_paragraph("CLÁUSULA SEGUNDA — DO PREÇO")
    entrada = _salvar(documento, tmp_path, "clausulas.docx")

    antes = validar_conteudo_docx.extrair(Document(str(entrada)))
    mutilado = Document(str(entrada))
    util_ooxml.remover_paragrafo(mutilado.paragraphs[1])
    depois = validar_conteudo_docx.extrair(mutilado)

    resultado = validar_conteudo_docx.comparar(antes, depois)
    assert not resultado.conteudo_preservado
    assert any(d.tipo == "conteudo_perdido" for d in resultado.nao_autorizadas)


# --------------------------------------------------------------------------- #
# Teste 10 — Idempotência
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
@pytest.mark.parametrize("minuta", MINUTAS, ids=lambda p: p.stem)
def test_10_idempotencia(minuta, tmp_path):
    perfil = estilos_docx.perfil_por_arquivo(minuta.name) or "generico"
    primeira = tmp_path / "primeira.docx"
    segunda = tmp_path / "segunda.docx"

    diagnostico = formatar_docx.formatar(minuta, primeira, perfil)
    assert diagnostico["testes"]["idempotencia"].startswith("OK"), \
        diagnostico["testes"]["idempotencia"]

    novo = formatar_docx.formatar(primeira, segunda, perfil)
    assert novo["correcoes_aplicadas"] == [], novo["correcoes_aplicadas"][:5]
    assert (validar_conteudo_docx.extrair(Document(str(primeira))).assinatura
            == validar_conteudo_docx.extrair(Document(str(segunda))).assinatura)


# --------------------------------------------------------------------------- #
# Teste 11 — Diferentes minutas / perfis
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
@pytest.mark.parametrize("perfil", ["dfd", "etp", "tr", "pesquisa_precos",
                                    "aviso", "contrato", "extrato"])
def test_11_perfis_principais_existem_e_sao_coerentes(perfil):
    padrao = estilos_docx.carregar_padrao(perfil)
    assert padrao.perfil["estilos_permitidos"]
    assert isinstance(padrao.niveis_numeracao, int)
    for nome in padrao.perfil["estilos_permitidos"]:
        estilos_docx._spec_do_estilo(padrao, nome)  # levanta KeyError se faltar spec

    if perfil == "extrato":
        assert padrao.niveis_numeracao == 0
        assert padrao.perfil["tabelas"] == "nenhuma"
    if perfil == "contrato":
        assert padrao.renumeracao_automatica is False


@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
@pytest.mark.parametrize("minuta", MINUTAS, ids=lambda p: p.stem)
def test_11b_auditoria_roda_em_todas_as_minutas(minuta):
    diagnostico = auditar_docx.auditar(minuta)
    assert 0 <= diagnostico["nota_padronizacao"] <= 100
    assert diagnostico["status"]
    markdown = relatorio_docx.render_markdown(diagnostico)
    for secao in relatorio_docx.SECOES:
        assert f"## {secao}" in markdown, secao


# --------------------------------------------------------------------------- #
# Teste 12 — Compatibilidade
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
@pytest.mark.parametrize("minuta", MINUTAS[:6], ids=lambda p: p.stem)
def test_12_arquivo_gerado_e_docx_valido(minuta, tmp_path):
    perfil = estilos_docx.perfil_por_arquivo(minuta.name) or "generico"
    saida = tmp_path / "saida.docx"
    formatar_docx.formatar(minuta, saida, perfil)

    with zipfile.ZipFile(saida) as zf:
        assert zf.testzip() is None
        nomes = set(zf.namelist())
        assert "word/document.xml" in nomes
        assert "[Content_Types].xml" in nomes
        assert any(n.startswith("word/header") for n in nomes)
    documento = Document(str(saida))          # reabre sem erro
    assert len(documento.paragraphs) > 0


# --------------------------------------------------------------------------- #
# Garantias transversais
# --------------------------------------------------------------------------- #

def test_saida_nunca_igual_a_entrada(tmp_path):
    entrada = doc_numeracao_incorreta(tmp_path)
    with pytest.raises(ValueError, match="não pode ser igual"):
        formatar_docx.formatar(entrada, entrada, "tr")


@pytest.mark.skipif(not MINUTAS, reason="biblioteca de minutas indisponível")
def test_minuta_mae_nao_pode_ser_sobrescrita_sem_modo_revisao(tmp_path):
    entrada = doc_numeracao_incorreta(tmp_path)
    destino = RAIZ / "05_minutas" / "TR" / "TR_MINUTA_MAE.docx"
    with pytest.raises(PermissionError, match="biblioteca oficial de minutas"):
        formatar_docx.formatar(entrada, destino, "tr")


def test_perfil_inexistente_falha_com_mensagem_util():
    with pytest.raises(ValueError, match="Perfil 'inexistente' inexistente"):
        estilos_docx.carregar_padrao("inexistente")


def test_relatorio_gera_markdown_e_json(tmp_path):
    entrada = doc_campos_pendentes(tmp_path)
    diagnostico = auditar_docx.auditar(entrada, "tr")
    destino = tmp_path / "relatorio.md"
    md, js = relatorio_docx.gravar(diagnostico, destino)

    assert md.exists() and js.exists()
    texto = md.read_text(encoding="utf-8")
    assert texto.startswith("# Relatório de Padronização Documental")
    for secao in relatorio_docx.SECOES:
        assert f"## {secao}" in texto
    assert "Não executados nesta rodada" in texto  # auditoria não roda testes


def test_validacao_visual_nao_e_simulada(tmp_path):
    entrada = doc_numeracao_incorreta(tmp_path)
    saida = tmp_path / "s.docx"
    diagnostico = formatar_docx.formatar(entrada, saida, "tr")
    assert "não executada" in diagnostico["testes"]["validacao_visual"]


def test_deteccao_de_comentarios_e_metadados(tmp_path):
    minuta = (RAIZ / "05_minutas" / "CONTRATO_COMPRAS"
              / "CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_MINUTA_MAE.docx")
    if not minuta.exists():
        pytest.skip("minuta indisponível")
    diagnostico = auditar_docx.auditar(minuta, "contrato")
    assert diagnostico["revisao"]["comentarios"] is True
    assert any("comentários internos" in item
               for item in diagnostico["correcoes_que_exigem_humano"])


def test_fragmentacao_e_apenas_sinalizada(tmp_path):
    documento = Document()
    for indice in range(1, 25):
        documento.add_paragraph(f"{indice}. Tópico curto {indice}")
    entrada = _salvar(documento, tmp_path, "fragmentado.docx")

    diagnostico = auditar_docx.auditar(entrada, "tr")
    assert diagnostico["numeracao"]["fragmentacao"]

    saida = tmp_path / "frag.docx"
    resultado = formatar_docx.formatar(entrada, saida, "tr")
    # Sinalizado, nunca consolidado: a contagem de parágrafos não muda.
    assert (resultado["validacao_conteudo"]["paragrafos_antes"]
            == resultado["validacao_conteudo"]["paragrafos_depois"])


def test_midia_orfa_nao_conta_como_timbre(tmp_path):
    minuta = RAIZ / "05_minutas" / "TR" / "TR_MINUTA_MAE.docx"
    if not minuta.exists():
        pytest.skip("minuta indisponível")
    referenciada = util_ooxml.midia_referenciada(minuta)
    orfa = util_ooxml.midia_orfa(minuta)
    assert referenciada and not (referenciada & orfa)
    assert all(n not in util_ooxml.assinaturas_partes(minuta) for n in orfa)


def test_quebra_de_secao_nao_e_tratada_como_linha_em_branco(tmp_path):
    """
    Parágrafo que hospeda um `w:sectPr` é visualmente vazio, mas carrega
    orientação, margens e as referências de cabeçalho e rodapé do trecho.
    Removê-lo como "linha em branco" apagaria o timbre da seção.
    """
    import copy

    documento = Document()
    documento.add_paragraph("Primeira seção.")
    portador = documento.add_paragraph()
    documento.add_paragraph("Segunda seção.")

    sectPr = documento.element.body.find(util_ooxml.qn("w:sectPr"))
    portador._p.get_or_add_pPr().append(copy.deepcopy(sectPr))

    assert not util_ooxml.paragrafo_vazio(portador)

    entrada = _salvar(documento, tmp_path, "com_secao.docx")
    saida = tmp_path / "formatado.docx"
    formatar_docx.formatar(entrada, saida, "generico")

    resultado = Document(str(saida))
    assert len(resultado.sections) == 2
