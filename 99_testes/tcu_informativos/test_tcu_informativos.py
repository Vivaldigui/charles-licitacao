from __future__ import annotations

import json

from scripts import tcu_informativos as mod


def test_filtro_inclui_temas_e_rejeita_ocorrencias_incidentais() -> None:
    assert "dispensa de licitação" in mod.termos_relevantes(
        "É irregular a aquisição de imóvel por dispensa de licitação."
    )
    assert "contratação direta" in mod.termos_relevantes(
        "A regra também se aplica ao processo de contratação direta."
    )
    assert "inexigibilidade de licitação" in mod.termos_relevantes(
        "A contratação ocorreu por inexigibilidade de licitação."
    )
    assert "credenciamento" in mod.termos_relevantes(
        "Na contratação de serviços decorrente de credenciamento, use critérios objetivos."
    )
    assert mod.termos_relevantes(
        "O microempreendedor é dispensado da elaboração de balanço patrimonial."
    ) == []
    assert mod.termos_relevantes(
        "Serviços contínuos com dedicação exclusiva de mão de obra."
    ) == []


def test_sumario_preserva_item_orgao_e_enunciado() -> None:
    texto = """Número 999
SUMÁRIO
Plenário
1. Primeiro enunciado sobre dispensa de licitação.
Continuação do primeiro enunciado.
Segunda Câmara
1. Segundo enunciado.

PLENÁRIO
1. Primeiro enunciado sobre dispensa de licitação.
Narrativa.
Acórdão 1/2026 Plenário, Consulta, Relator Ministro Fulano.
"""
    itens, inicio_detalhes = mod.extrair_sumario(texto)
    assert [(i.numero, i.orgao) for i in itens] == [(1, "Plenário"), (1, "Segunda Câmara")]
    assert itens[0].enunciado.endswith("Continuação do primeiro enunciado.")
    assert texto[inicio_detalhes:].lstrip().startswith("PLENÁRIO")


def test_citacao_final_aceita_relator_e_revisor() -> None:
    texto = (
        "Acórdão 702/2023 Plenário, Representação, Relator Ministro-Substituto Augusto Sherman.\n"
        "Acórdão 1466/2025 Plenário, Pedido de Reexame, Revisor Ministro Jorge Oliveira."
    )
    grupos = [m.groups() for m in mod.ACORDAO_RE.finditer(texto)]
    assert grupos == [
        ("702/2023", "Plenário", "Representação", "Relator", "Ministro-Substituto Augusto Sherman"),
        ("1466/2025", "Plenário", "Pedido de Reexame", "Revisor", "Ministro Jorge Oliveira"),
    ]


def test_intervalo_conserva_paginas_exatas() -> None:
    texto, intervalos = mod.juntar_paginas(["abc", "defgh", "ij"])
    assert texto == "abc\n\ndefgh\n\nij"
    assert mod.paginas_do_intervalo(1, 8, intervalos) == [1, 2]
    assert mod.paginas_do_intervalo(intervalos[2][0], intervalos[2][1], intervalos) == [3]


def test_snapshot_integral_tem_80_originais_e_6_julgados() -> None:
    manifesto = mod.INDICES_DIR / "manifesto_informativos.jsonl"
    catalogo = mod.INDICES_DIR / "catalogo_julgados.jsonl"
    assert manifesto.exists()
    assert catalogo.exists()
    pubs = [json.loads(v) for v in manifesto.read_text(encoding="utf-8").splitlines()]
    julgados = [json.loads(v) for v in catalogo.read_text(encoding="utf-8").splitlines()]
    assert [p["informativo"] for p in pubs] == list(range(452, 532))
    assert len(julgados) == 6
    assert {j["informativo"] for j in julgados} == {455, 457, 462, 483, 514, 525}
    assert all(j["paginas"] and len(j["sha256"]) == 64 for j in julgados)
    assert all(j["url_inteiro_teor"] != mod.NAO_IDENTIFICADO for j in julgados)
