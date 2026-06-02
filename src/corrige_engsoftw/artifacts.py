from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .extractor import parse_docx


def carregar_artefato(caminho: str | Path) -> dict[str, Any]:
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".json":
        return json.loads(caminho.read_text(encoding="utf-8"))
    if caminho.suffix.lower() == ".docx":
        return parse_docx(caminho)
    raise ValueError(f"Formato não suportado: {caminho.suffix}")
