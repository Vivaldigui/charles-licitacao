from __future__ import annotations

import json
from pathlib import Path

import indexar_base
import validar_base


def _ficha(texto_data: str = "2026-07-01") -> str:
    return f"""---
tipo: checklist
hierarquia: operacional
tema: teste
fonte: teste
vigencia: vigente
atualizado_em: {texto_data}
tags: [teste]
---

# Ficha Teste

Conteúdo.
"""


def test_validar_base_caso_feliz(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "00_indices").mkdir()
    (tmp_path / "07_checklists").mkdir()
    (tmp_path / "07_checklists" / "ficha-teste.md").write_text(_ficha(), encoding="utf-8")
    indice = indexar_base.gerar_indice(tmp_path)
    (tmp_path / "00_indices" / "BASE_INDEXADA.json").write_text(
        json.dumps(indice, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(validar_base, "RAIZ", tmp_path)
    monkeypatch.setattr(validar_base, "SAIDA_PADRAO", tmp_path / "00_indices" / "BASE_INDEXADA.json")
    erros, _avisos = validar_base.validar()
    assert erros == []


def test_validar_base_data_invalida(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "00_indices").mkdir()
    (tmp_path / "07_checklists").mkdir()
    (tmp_path / "07_checklists" / "ficha-teste.md").write_text(_ficha("01/07/2026"), encoding="utf-8")
    (tmp_path / "00_indices" / "BASE_INDEXADA.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(validar_base, "RAIZ", tmp_path)
    monkeypatch.setattr(validar_base, "SAIDA_PADRAO", tmp_path / "00_indices" / "BASE_INDEXADA.json")
    erros, _avisos = validar_base.validar()
    assert any("atualizado_em inválido" in erro for erro in erros)

