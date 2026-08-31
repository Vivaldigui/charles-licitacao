from __future__ import annotations

import json
from pathlib import Path

from controle_cnae import carregar_contratacoes, gravar_contratacao, simular


def test_simular_limite_nao_confirmado(tmp_path: Path) -> None:
    csv_path = tmp_path / "contratacoes.csv"
    limites_path = tmp_path / "limites.json"
    gravar_contratacao(
        {
            "data_conclusao": "2026-01-01",
            "processo": "PA 1",
            "objeto": "Objeto",
            "cnae_subclasse": "0000-0/00",
            "cnae_descricao": "Teste",
            "fundamento": "Dispensa — art. 75, II",
            "valor": "100.00",
            "conta_para_limite": "S",
            "exercicio": "2026",
            "inciso": "II",
        },
        csv_path,
    )
    limites_path.write_text(json.dumps({"2026": {"II": None, "fonte": "fonte.md"}}), encoding="utf-8")
    res = simular(
        objeto="Novo",
        cnae="0000-0/00",
        valor="50,00",
        csv_path=csv_path,
        limites_path=limites_path,
    )
    assert res["total_simulado"].to_eng_string() == "150.00"
    assert res["faixa"] == "limite_nao_confirmado"


def test_registro_csv() -> None:
    registros = carregar_contratacoes()
    assert isinstance(registros, list)

