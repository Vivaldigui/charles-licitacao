from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "scripts" / "docx_cmi"

for caminho in (str(MODULO), str(RAIZ / "scripts")):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: depende de ferramenta externa (LibreOffice ou Word) e é pulado "
        "quando ela não existe no ambiente",
    )
