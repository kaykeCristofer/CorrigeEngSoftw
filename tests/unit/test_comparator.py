import pytest

from src.corrige_engsoftw.comparator import (
    nomes_de,
    similaridade_conjuntos,
    score_tela,
    score_fluxo,
    melhor_match,
    comparar_lista,
    comparar,
)
from src.corrige_engsoftw.models import Campo, Tela, Fluxo


class TestNomesDe:
    """Testes para função nomes_de."""

    def test_extrai_nomes_de_colecao(self):
        """Deve extrair nomes de coleção de dicts."""
        colecao = [
            {"nome": "Email"},
            {"nome": "CPF"},
            {"nome": "Telefone"}
        ]
        nomes = nomes_de(colecao)
        assert len(nomes) == 3
        assert "Email" in nomes

    def test_ignora_items_sem_nome(self):
        """Deve ignorar items sem campo 'nome'."""
        colecao = [
            {"nome": "Email"},
            {"descricao": "Sem nome"},
            {"nome": "CPF"}
        ]
        nomes = nomes_de(colecao)
        assert len(nomes) == 2

    def test_campo_customizado(self):
        """Deve extrair campo customizado."""
        colecao = [
            {"descricao": "Passo 1"},
            {"descricao": "Passo 2"}
        ]
        nomes = nomes_de(colecao, campo="descricao")
        assert len(nomes) == 2
        assert "Passo 1" in nomes

    def test_lista_vazia(self):
        """Deve retornar lista vazia para entrada vazia."""
        assert nomes_de([]) == []


class TestSimilaridadeConjuntos:
    """Testes para função similaridade_conjuntos."""

    def test_ambos_vazios(self):
        """Conjuntos vazios devem ter similaridade 1.0."""
        assert similaridade_conjuntos([], []) == 1.0

    def test_um_vazio(self):
        """Um vazio deve retornar 0.0."""
        assert similaridade_conjuntos(["a"], []) == 0.0
        assert similaridade_conjuntos([], ["a"]) == 0.0

    def test_identicos(self):
        """Conjuntos idênticos devem ter similaridade 1.0."""
        assert similaridade_conjuntos(["Email", "CPF"], ["Email", "CPF"]) == 1.0

    def test_parcialmente_sobrepostos(self):
        """Conjuntos parcialmente sobrepostos."""
        resultado = similaridade_conjuntos(
            ["Email", "CPF", "Nome"],
            ["Email", "CPF"]
        )
        assert 0 < resultado < 1

    def test_diferentes(self):
        """Conjuntos sem intersecção devem ter similaridade baixa."""
        resultado = similaridade_conjuntos(
            ["Email", "CPF"],
            ["Telefone", "Celular"]
        )
        assert resultado < 0.5


class TestScoreTela:
    """Testes para função score_tela."""

    def test_telas_identicas(self):
        """Telas idênticas devem ter score 1.0."""
        tela1 = {
            "nome": "Cadastro",
            "campos": [{"nome": "Email"}],
            "acoes": [{"nome": "Salvar"}],
            "tabelas": [{"nome": "Produtos"}]
        }
        tela2 = tela1.copy()
        assert score_tela(tela1, tela2) == 1.0

    def test_telas_diferentes(self):
        """Telas sem relação devem ter score baixo."""
        tela1 = {
            "nome": "Cadastro",
            "campos": [],
            "acoes": [],
            "tabelas": []
        }
        tela2 = {
            "nome": "Consulta",
            "campos": [{"nome": "CPF"}],
            "acoes": [{"nome": "Pesquisar"}],
            "tabelas": []
        }
        score = score_tela(tela1, tela2)
        assert score < 0.5

    def test_mesma_tela_nomes_diferentes(self):
        """Mesma tela com nomes ligeiramente diferentes."""
        tela1 = {
            "nome": "Tela de Cadastro",
            "campos": [{"nome": "Email"}],
            "acoes": [],
            "tabelas": []
        }
        tela2 = {
            "nome": "Cadastro",
            "campos": [{"nome": "Email"}],
            "acoes": [],
            "tabelas": []
        }
        score = score_tela(tela1, tela2)
        assert score > 0.8


class TestScoreFluxo:
    """Testes para função score_fluxo."""

    def test_fluxos_identicos(self):
        """Fluxos idênticos devem ter score 1.0."""
        fluxo1 = {
            "nome": "Fluxo principal",
            "passos": [{"descricao": "O Sistema valida"}],
            "regrasNegocio": ["CPF válido"]
        }
        fluxo2 = fluxo1.copy()
        assert score_fluxo(fluxo1, fluxo2) == 1.0

    def test_fluxos_diferentes(self):
        """Fluxos sem relação devem ter score baixo."""
        fluxo1 = {
            "nome": "Fluxo A",
            "passos": [{"descricao": "Passo A"}],
            "regrasNegocio": []
        }
        fluxo2 = {
            "nome": "Fluxo B",
            "passos": [{"descricao": "Passo B"}],
            "regrasNegocio": []
        }
        score = score_fluxo(fluxo1, fluxo2)
        assert score < 0.5


class TestMelhorMatch:
    """Testes para função melhor_match."""

    def test_encontra_match_acima_limite(self):
        """Deve encontrar match acima do limite."""
        candidatos = [
            {"nome": "Email"},
            {"nome": "CPF"},
            {"nome": "Nome"}
        ]
        melhor, score = melhor_match("Email", candidatos, 0.5)
        assert melhor is not None
        assert melhor["nome"] == "Email"
        assert score == 1.0

    def test_rejeita_match_abaixo_limite(self):
        """Deve rejeitar match abaixo do limite."""
        candidatos = [
            {"nome": "Telefone"},
            {"nome": "Celular"}
        ]
        melhor, score = melhor_match("Email", candidatos, 0.8)
        assert melhor is None

    def test_sem_candidatos(self):
        """Deve retornar None sem candidatos."""
        melhor, score = melhor_match("Email", [], 0.5)
        assert melhor is None


class TestCompararLista:
    """Testes para função comparar_lista."""

    def test_listas_identicas(self):
        """Listas idênticas devem ter todos cobertos."""
        esperados = [{"nome": "Email"}, {"nome": "CPF"}]
        encontrados = [{"nome": "Email"}, {"nome": "CPF"}]
        resultado = comparar_lista(esperados, encontrados, "campo", 0.5)
        assert len(resultado["cobertos"]) == 2
        assert len(resultado["faltantes"]) == 0
        assert len(resultado["extras"]) == 0

    def test_listas_vazias(self):
        """Listas vazias devem ter resultado vazio."""
        resultado = comparar_lista([], [], "campo", 0.5)
        assert len(resultado["cobertos"]) == 0
        assert len(resultado["faltantes"]) == 0
        assert len(resultado["extras"]) == 0

    def test_items_faltantes(self):
        """Deve detectar items faltantes."""
        esperados = [{"nome": "Email"}, {"nome": "CPF"}]
        encontrados = [{"nome": "Email"}]
        resultado = comparar_lista(esperados, encontrados, "campo", 0.9)
        assert len(resultado["cobertos"]) == 1
        assert len(resultado["faltantes"]) == 1

    def test_items_extras(self):
        """Deve detectar items extras."""
        esperados = [{"nome": "Email"}]
        encontrados = [{"nome": "Email"}, {"nome": "CPF"}]
        resultado = comparar_lista(esperados, encontrados, "campo", 0.9)
        assert len(resultado["cobertos"]) == 1
        assert len(resultado["extras"]) == 1


class TestComparar:
    """Testes para função comparar (integração)."""

    def test_gababrito_aluno_identicos(self, gabarito_json, aluno_json_completo):
        """Gabarito e aluno idênticos devem ter 100% cobertura."""
        resultado = comparar(gabarito_json, aluno_json_completo, 0.5)
        assert resultado["resumo"]["percentualCobertura"] == 100.0

    def test_aluno_vazio(self, gabarito_json, aluno_json_vazio):
        """Aluno vazio deve ter 0% cobertura."""
        resultado = comparar(gabarito_json, aluno_json_vazio, 0.5)
        assert resultado["resumo"]["percentualCobertura"] == 0.0

    def test_aluno_parcial(self, gabarito_json, aluno_json_parcial):
        """Aluno parcial deve ter cobertura entre 0 e 100."""
        resultado = comparar(gabarito_json, aluno_json_parcial, 0.5)
        cobertura = resultado["resumo"]["percentualCobertura"]
        assert 0 < cobertura < 100

    def test_retorna_estrutura_completa(self, gabarito_json, aluno_json_completo):
        """Deve retornar estrutura completa de relatório."""
        resultado = comparar(gabarito_json, aluno_json_completo)
        assert "limiteSimilaridade" in resultado
        assert "telas" in resultado
        assert "fluxos" in resultado
        assert "resumo" in resultado
        assert "itensEsperados" in resultado["resumo"]
        assert "itensCobertos" in resultado["resumo"]
        assert "percentualCobertura" in resultado["resumo"]

    def test_limite_similariidade_afeta_resultado(self, gabarito_json, aluno_json_parcial):
        """Limite de similaridade deve afetar resultado."""
        resultado_baixo = comparar(gabarito_json, aluno_json_parcial, 0.3)
        resultado_alto = comparar(gabarito_json, aluno_json_parcial, 0.9)
        
        # Limite mais alto deve resultar em menos items cobertos
        assert resultado_baixo["resumo"]["itensCobertos"] >= resultado_alto["resumo"]["itensCobertos"]
