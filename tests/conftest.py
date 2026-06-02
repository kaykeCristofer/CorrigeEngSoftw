"""
Fixtures compartilhadas para testes.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from src.corrige_engsoftw.models import Campo, Acao, Tabela, Tela, Passo, Fluxo


@pytest.fixture
def sample_campo():
    """Fixture: campo simples."""
    return Campo(
        nome="Email",
        obrigatorio=True,
        validacao="email válido",
        exemplo="user@example.com",
        opcoes=[]
    )


@pytest.fixture
def sample_acao():
    """Fixture: ação simples."""
    return Acao(nome="Salvar")


@pytest.fixture
def sample_tabela():
    """Fixture: tabela simples."""
    return Tabela(
        nome="Produtos",
        colunas=["ID", "Nome", "Preço"]
    )


@pytest.fixture
def sample_tela(sample_campo, sample_acao, sample_tabela):
    """Fixture: tela completa."""
    return Tela(
        nome="Tela de Cadastro",
        campos=[sample_campo],
        acoes=[sample_acao],
        tabelas=[sample_tabela]
    )


@pytest.fixture
def sample_passo():
    """Fixture: passo de fluxo."""
    return Passo(
        ordem=1,
        descricao="O Sistema valida os dados"
    )


@pytest.fixture
def sample_fluxo(sample_passo):
    """Fixture: fluxo completo."""
    return Fluxo(
        nome="Fluxo principal",
        precondicoes=["Usuário autenticado"],
        passos=[sample_passo],
        regrasNegocio=["CPF deve ser válido"]
    )


@pytest.fixture
def gabarito_json(sample_tela, sample_fluxo):
    """Fixture: JSON do gabarito."""
    from dataclasses import asdict
    return {
        "telas": [asdict(sample_tela)],
        "fluxos": [asdict(sample_fluxo)]
    }


@pytest.fixture
def aluno_json_completo(sample_tela, sample_fluxo):
    """Fixture: JSON do aluno (implementação completa)."""
    from dataclasses import asdict
    return {
        "telas": [asdict(sample_tela)],
        "fluxos": [asdict(sample_fluxo)]
    }


@pytest.fixture
def aluno_json_parcial():
    """Fixture: JSON do aluno (implementação parcial)."""
    return {
        "telas": [
            {
                "nome": "Tela de Cadastro",
                "campos": [
                    {
                        "nome": "Email",
                        "obrigatorio": False,
                        "validacao": None,
                        "exemplo": None,
                        "opcoes": []
                    }
                ],
                "acoes": [],
                "tabelas": []
            }
        ],
        "fluxos": []
    }


@pytest.fixture
def aluno_json_vazio():
    """Fixture: JSON do aluno (vazio)."""
    return {
        "telas": [],
        "fluxos": []
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture: diretório temporário para testes."""
    return tmp_path


@pytest.fixture
def comparison_result():
    """Fixture: resultado esperado de comparação."""
    return {
        "limiteSimilaridade": 0.72,
        "telas": [
            {
                "telaEsperada": "Tela de Cadastro",
                "telaEncontrada": "Tela de Cadastro",
                "similaridade": 1.0,
                "campos": {
                    "cobertos": [],
                    "faltantes": [],
                    "extras": []
                },
                "acoes": {
                    "cobertos": [],
                    "faltantes": [],
                    "extras": []
                },
                "tabelas": {
                    "cobertos": [],
                    "faltantes": [],
                    "extras": []
                }
            }
        ],
        "fluxos": [],
        "resumo": {
            "itensEsperados": 0,
            "itensCobertos": 0,
            "percentualCobertura": 0.0
        }
    }


@pytest.fixture(autouse=True)
def mock_gemini_api(monkeypatch):
    """
    Fixture: mocka API do Gemini para não fazer chamadas reais.
    Aplicado automaticamente a todos os testes.
    """
    def mock_configure(*args, **kwargs):
        pass

    def mock_generate_content(prompt, **kwargs):
        class MockResponse:
            text = json.dumps({
                "nota": 8.0,
                "percentual_cobertura_semantica": 80,
                "veredito": "Bom",
                "equivalencias_aceitas": [],
                "itens_cobertos": [],
                "itens_parciais": [],
                "itens_faltantes": [],
                "itens_extras_ou_inventados": [],
                "problemas_de_fluxo": [],
                "feedback": "Protótipo bem estruturado"
            })
        return MockResponse()

    def mock_generative_model(*args, **kwargs):
        class MockModel:
            def generate_content(self, prompt, **kwargs):
                return mock_generate_content(prompt, **kwargs)
        return MockModel(*args, **kwargs)

    try:
        import google.generativeai as genai
        monkeypatch.setattr(genai, "configure", mock_configure)
        monkeypatch.setattr(genai, "GenerativeModel", mock_generative_model)
    except ImportError:
        pass


@pytest.fixture
def caplog_handler(caplog):
    """Fixture: captura logs para verificação."""
    return caplog
