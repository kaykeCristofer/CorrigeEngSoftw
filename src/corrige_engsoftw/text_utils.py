from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


def limpar_texto(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto.replace("\xa0", " ")).strip()
    texto = re.sub(r"\s+([,.?;:])", r"\1", texto)
    return texto


def chave(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return limpar_texto(texto)


def similaridade(a: str, b: str) -> float:
    ca, cb = chave(a), chave(b)
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0
    if ca in cb or cb in ca:
        return 0.9
    return SequenceMatcher(None, ca, cb).ratio()


def deduplicar(items: list[Any], attr: str) -> list[Any]:
    vistos: set[str] = set()
    saida = []
    for item in items:
        valor = chave(getattr(item, attr))
        if valor not in vistos:
            vistos.add(valor)
            saida.append(item)
    return saida
