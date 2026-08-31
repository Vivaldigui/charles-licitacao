from __future__ import annotations

from normalizar_precos import (
    detectar_outliers,
    estatisticas,
    parse_brl,
    parse_brl_verboso,
    recalcular_unitario,
)


def test_parse_brl_casos_principais() -> None:
    assert parse_brl("R$ 1.234,56") == 1234.56
    assert parse_brl("1.234") is None
    assert parse_brl_verboso("1.234")[1] == "valor ambíguo — validação humana"
    assert parse_brl("1.234,00") == 1234.0
    assert parse_brl("1234.56") == 1234.56
    assert parse_brl("") is None
    assert parse_brl("-5") is None
    assert parse_brl(0) is None


def test_recalcular_unitario_quantidade_invalida() -> None:
    assert recalcular_unitario("100,00", 0) is None
    assert recalcular_unitario("100,00", None) is None
    assert recalcular_unitario("100,00", 4) == 25.0


def test_detectar_outliers_amostra_pequena_e_outlier() -> None:
    pequeno = detectar_outliers([10.0, 11.0, 50.0])
    assert pequeno["indices_discrepantes"] == []
    assert "Amostra pequena" in pequeno["observacao"]

    resultado = detectar_outliers([10.0, 11.0, 12.0, 100.0])
    assert resultado["valores_discrepantes"] == [100.0]


def test_estatisticas_alertas() -> None:
    vazio = estatisticas([])
    assert vazio["n"] == 0
    assert vazio["media"] is None
    assert "Nenhum preço válido" in vazio["alerta_minimo"]

    poucos = estatisticas([10.0, 20.0])
    assert poucos["media"] == 15.0
    assert "Apenas 2" in poucos["alerta_minimo"]

