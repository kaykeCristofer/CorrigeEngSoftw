"""Ferramentas para extrair e comparar protótipos de Engenharia de Software."""

from .artifacts import carregar_artefato
from .comparator import comparar
from .extractor import parse_docx

__all__ = ["carregar_artefato", "comparar", "parse_docx"]
