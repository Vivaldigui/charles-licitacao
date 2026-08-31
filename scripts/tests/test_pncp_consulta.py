from __future__ import annotations

import json
from pathlib import Path

import pncp_consulta


def test_normalizar_item_e_montar_link() -> None:
    item = {
        "description": "Aquisição de cadeiras",
        "orgao_cnpj": "12345678000199",
        "orgao_nome": "Câmara Teste",
        "ano": "2026",
        "numero_sequencial": "15",
        "valor_global": "1000.00",
    }
    normalizado = pncp_consulta._normalizar_item(item)
    assert normalizado["objeto_encontrado"] == "Aquisição de cadeiras"
    assert normalizado["link"] == "https://pncp.gov.br/app/editais/12345678000199/2026/15"


def test_consulta_textual_com_fixture_sem_rede(monkeypatch, tmp_path: Path) -> None:
    fixture = json.loads((Path(__file__).parent / "fixtures" / "pncp_busca_textual.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(pncp_consulta, "_http_get_json", lambda url: fixture)
    res = pncp_consulta.consultar_pncp_textual("cadeiras", evidencia=tmp_path)
    assert res["erro"] is None
    assert len(res["itens"]) == 1
    assert (tmp_path / "consultas.log").exists()


def test_esquema_inesperado_preenche_erro(monkeypatch) -> None:
    monkeypatch.setattr(pncp_consulta, "_http_get_json", lambda url: {"inesperado": True})
    res = pncp_consulta.consultar_pncp_textual("cadeiras")
    assert res["itens"] == []
    assert "esquema inesperado" in res["erro"]
