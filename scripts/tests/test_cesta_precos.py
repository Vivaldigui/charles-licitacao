from __future__ import annotations

import re

from cesta_precos import gerar_relatorio, montar_cesta


def _item(valor: str, data: str = "2026-01-10") -> dict:
    return {
        "fonte": "Manual",
        "orgao": "Câmara Teste",
        "objeto_encontrado": "Objeto compatível",
        "modalidade": "Dispensa",
        "data": data,
        "quantidade": "1",
        "unidade": "unid.",
        "valor_unitario": valor,
        "valor_total": "",
        "link": "https://teste.local",
        "data_acesso": "2026-07-01",
        "mesma_especificacao": "S",
        "mesma_unidade": "S",
        "quantidade_mesma_ordem": "S",
        "data_ate_1_ano": "S",
        "mesma_regiao": "S",
        "condicoes_equivalentes": "S",
    }


def test_item_sem_valor_e_data_antiga_sao_excluidos() -> None:
    itens, _outliers = montar_cesta([_item("100,00"), _item("", "2026-01-10"), _item("100,00", "2024-01-10")], {})
    assert itens[0]["situacao"] == "válido"
    assert itens[1]["situacao"] == "excluído por ausência de valor"
    assert "Preço unitário não identificado" in itens[1]["observacao"]
    assert itens[2]["situacao"] == "excluído por data antiga"


def test_relatorio_tem_blocos_e_tabelas_separadas() -> None:
    processo = {"objeto": "Objeto compatível", "quantidade": 1, "unidade": "unid."}
    itens, outliers = montar_cesta([_item("100,00"), _item("100,00"), _item("")], processo)
    relatorio = gerar_relatorio(processo, itens, outliers, None, None)
    assert "## 5. Ficha de comparabilidade" in relatorio
    assert "## 6. Tabela da cesta válida" in relatorio
    assert "## 7. Itens descartados com motivo" in relatorio
    assert "Declaração de método" in relatorio


def test_relatorio_nao_inventa_valor_monetario() -> None:
    processo = {"objeto": "Objeto compatível", "quantidade": 1, "unidade": "unid."}
    itens, outliers = montar_cesta([_item("100,00"), _item("100,00"), _item("100,00")], processo)
    relatorio = gerar_relatorio(processo, itens, outliers, None, None)
    valores = set(re.findall(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", relatorio))
    assert valores <= {"R$ 100,00"}
