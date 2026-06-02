"""
Testes unitários para módulo text_utils.
"""

import pytest

from src.corrige_engsoftw.text_utils import (
    limpar_texto,
    chave,
    similaridade,
    deduplicar
)
from src.corrige_engsoftw.models import Campo


class TestLimparTexto:
    """Testes para função limpar_texto."""

    def test_remove_multiplos_espacos(self):
        """Deve remover múltiplos espaços."""
        assert limpar_texto("texto   com   espaços") == "texto com espaços"

    def test_remove_espaco_nao_quebravel(self):
        """Deve remover espaço não-quebrável (\\xa0)."""
        assert limpar_texto("texto\xa0com\xa0espaços") == "texto com espaços"

    def test_remove_espacos_antes_pontuacao(self):
        """Deve remover espaços antes de pontuação."""
        assert limpar_texto("texto , com . espaços") == "texto, com. espaços"

    def test_strip_geral(self):
        """Deve remover espaços no início e fim."""
        assert limpar_texto("   texto   ") == "texto"

    def test_texto_vazio(self):
        """Deve retornar string vazia para entrada vazia."""
        assert limpar_texto("") == ""
        assert limpar_texto("   ") == ""

    def test_preserva_conteudo_interno(self):
        """Deve preservar conteúdo interno válido."""
        assert limpar_texto("texto válido") == "texto válido"


class TestChave:
    """Testes para função chave (normalização)."""

    def test_converte_para_minusculas(self):
        """Deve converter para minúsculas."""
        assert "buscar" in chave("BUSCAR")

    def test_remove_acentos(self):
        """Deve remover acentuação."""
        assert "preco" in chave("Preço")
        assert "codigo" in chave("Código")

    def test_aplica_sinonimos_dominio(self):
        """Deve aplicar sinônimos do domínio."""
        assert "contas" in chave("comandas")
        assert "numero" in chave("código")
        assert "valor" in chave("preço")

    def test_normaliza_multiplas_formas(self):
        """Deve normalizar múltiplas formas ao mesmo resultado."""
        assert chave("preço unitário") == chave("preco unitario")
        assert chave("Preço Unitário") == chave("PREÇO UNITÁRIO")

    def test_texto_vazio(self):
        """Deve retornar vazio para entrada vazia."""
        assert chave("") == ""

    def test_casos_dominio_especifico(self):
        """Testa casos específicos do domínio."""
        assert "contas" in chave("comanda")
        assert "confere" in chave("valida")
        assert "insercao" in chave("inclusão")


class TestSimilaridade:
    """Testes para função similaridade."""

    def test_identicos(self):
        """Textos idênticos devem ter similaridade 1.0."""
        assert similaridade("Buscar", "Buscar") == 1.0

    def test_totalmente_diferentes(self):
        """Textos sem relação devem ter similaridade 0."""
        assert similaridade("xyz", "abc") < 0.1

    def test_sinonimos_dominio(self):
        """Sinônimos do domínio devem ter similaridade alta."""
        assert similaridade("buscar", "pesquisar") > 0.8
        assert similaridade("preço", "valor") > 0.8

    def test_contido(self):
        """Texto contido deve ter similaridade alta."""
        assert similaridade("buscar", "buscar usuário") > 0.8

    def test_vazios(self):
        """Textos vazios devem ter similaridade 0."""
        assert similaridade("", "") == 0.0
        assert similaridade("texto", "") == 0.0

    def test_case_insensitive(self):
        """Deve ser case-insensitive."""
        assert similaridade("BUSCAR", "buscar") == 1.0

    def test_acentos_removidos(self):
        """Acentos devem ser removidos antes da comparação."""
        assert similaridade("Código", "Codigo") == 1.0


class TestDeduplicar:
    """Testes para função deduplicar."""

    def test_remove_duplicatas_por_chave(self):
        """Deve remover duplicatas por chave normalizada."""
        campos = [
            Campo(nome="Email"),
            Campo(nome="email"),
            Campo(nome="EMAIL")
        ]
        resultado = deduplicar(campos, "nome")
        assert len(resultado) == 1

    def test_preserva_ordem(self):
        """Deve preservar ordem de primeira ocorrência."""
        campos = [
            Campo(nome="CPF"),
            Campo(nome="Email"),
            Campo(nome="cpf")
        ]
        resultado = deduplicar(campos, "nome")
        assert resultado[0].nome == "CPF"
        assert resultado[1].nome == "Email"

    def test_lista_vazia(self):
        """Deve retornar vazio para entrada vazia."""
        assert deduplicar([], "nome") == []

    def test_sem_duplicatas(self):
        """Deve retornar mesma lista se sem duplicatas."""
        campos = [
            Campo(nome="Email"),
            Campo(nome="CPF")
        ]
        resultado = deduplicar(campos, "nome")
        assert len(resultado) == 2

    def test_sinônimos_considerados_duplicatas(self):
        """Sinônimos devem ser considerados duplicatas."""
        campos = [
            Campo(nome="Código"),
            Campo(nome="Número")  # Sinônimo no domínio
        ]
        resultado = deduplicar(campos, "nome")
        assert len(resultado) == 1  # Ambos mapeiam para "numero"
