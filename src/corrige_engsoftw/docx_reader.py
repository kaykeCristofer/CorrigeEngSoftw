from __future__ import annotations

from typing import Iterable

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from .text_utils import limpar_texto


def texto_celula(celula) -> str:
    return limpar_texto(" ".join(p.text for p in celula.paragraphs if p.text.strip()))


def celulas_linha(linha) -> list[str]:
    celulas: list[str] = []
    anterior = None
    for celula in linha.cells:
        texto = texto_celula(celula)
        if texto != anterior:
            celulas.append(texto)
        anterior = texto
    return celulas


def iter_blocos(documento: Document) -> Iterable[Paragraph | Table]:
    for child in documento.element.body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, documento)
        elif tag == "tbl":
            yield Table(child, documento)
