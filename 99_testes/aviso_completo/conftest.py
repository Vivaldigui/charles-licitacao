from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

for caminho in (
    RAIZ / "scripts" / "aviso_completo",
    RAIZ / "scripts" / "docx_cmi",
    RAIZ / "scripts",
):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: depende de ferramenta externa (Word ou LibreOffice) e é pulado "
        "quando ela não existe no ambiente",
    )
