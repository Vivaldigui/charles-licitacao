from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "scripts" / "gestao_documental"

for caminho in (str(MODULO), str(RAIZ / "scripts")):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)
