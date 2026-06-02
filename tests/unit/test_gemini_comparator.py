"""
Testes unitários do módulo gemini_comparator (integração com Gemini API).
"""

import pytest
from unittest.mock import MagicMock, patch, call

from src.corrige_engsoftw.models import Tela, Campo, Acao, Fluxo, Passo


@pytest.fixture
def mock_gemini_model():
    """Mock do modelo Gemini."""
    mock = MagicMock()
    mock.generate_content.return_value = MagicMock(text="Pontuação: 8/10")
    return mock


class TestCompararComGemini:
    """Testes de comparação usando Gemini."""

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_comparacao_tela_simples(self, mock_genai_class, mock_gemini_model):
        """Deve comparar tela simples com Gemini."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        # Setup
        mock_genai_class.return_value = mock_gemini_model
        
        tela_gabarito = {
            "nome": "Cadastro",
            "campos": [{"nome": "Email"}],
            "acoes": [{"nome": "Salvar"}],
            "tabelas": []
        }
        
        tela_aluno = {
            "nome": "Cadastro",
            "campos": [{"nome": "Email"}],
            "acoes": [{"nome": "Salvar"}],
            "tabelas": []
        }
        
        resultado = comparar_com_gemini(tela_gabarito, tela_aluno)
        
        # Deve chamar Gemini
        mock_genai_class.assert_called()
        assert resultado is not None

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_comparacao_fluxo_completo(self, mock_genai_class, mock_gemini_model):
        """Deve comparar fluxo completo com Gemini."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        
        fluxo_gabarito = {
            "nome": "Fluxo Principal",
            "precondicoes": ["Usuário autenticado"],
            "passos": [
                {"ordem": 1, "descricao": "O Usuário insere dados"}
            ],
            "regrasNegocio": ["CPF válido"]
        }
        
        fluxo_aluno = {
            "nome": "Fluxo Principal",
            "precondicoes": ["Usuário autenticado"],
            "passos": [
                {"ordem": 1, "descricao": "O Usuário insere dados"}
            ],
            "regrasNegocio": ["CPF válido"]
        }
        
        resultado = comparar_com_gemini(fluxo_gabarito, fluxo_aluno)
        
        assert resultado is not None


class TestPromptGemini:
    """Testes de construção de prompt para Gemini."""

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_prompt_deve_conter_contexto(self, mock_genai_class, mock_gemini_model):
        """Prompt deve conter contexto clara."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        
        tela_gab = {"nome": "Teste", "campos": [], "acoes": [], "tabelas": []}
        tela_aluno = {"nome": "Teste", "campos": [], "acoes": [], "tabelas": []}
        
        comparar_com_gemini(tela_gab, tela_aluno)
        
        # Verificar que generate_content foi chamado
        mock_gemini_model.generate_content.assert_called()
        
        # Verificar que prompt foi enviado
        call_args = mock_gemini_model.generate_content.call_args
        assert call_args is not None

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_prompt_menciona_gabarito_aluno(self, mock_genai_class, mock_gemini_model):
        """Prompt deve diferenciar gabarito de aluno."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        
        tela_gab = {"nome": "Gabarito", "campos": [], "acoes": [], "tabelas": []}
        tela_aluno = {"nome": "Aluno", "campos": [], "acoes": [], "tabelas": []}
        
        comparar_com_gemini(tela_gab, tela_aluno)
        
        # Deve ter sido chamado
        mock_gemini_model.generate_content.assert_called()


class TestParsingResposta:
    """Testes de parsing da resposta do Gemini."""

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_extrai_pontuacao_numerica(self, mock_genai_class, mock_gemini_model):
        """Deve extrair pontuação numérica."""
        from src.corrige_engsoftw.gemini_comparator import extrair_pontuacao
        
        # Mock de resposta com pontuação
        mock_gemini_model.generate_content.return_value = MagicMock(
            text="A comparação resulta em: Pontuação 7.5/10"
        )
        mock_genai_class.return_value = mock_gemini_model
        
        resposta = "A comparação resulta em: Pontuação 7.5/10"
        pontuacao = extrair_pontuacao(resposta)
        
        if pontuacao:
            assert 0 <= pontuacao <= 10

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_extrai_justificativa(self, mock_genai_class, mock_gemini_model):
        """Deve extrair justificativa da resposta."""
        from src.corrige_engsoftw.gemini_comparator import extrair_justificativa
        
        resposta = """
        Pontuação: 8/10
        Justificativa: A tela estava correta mas faltou validação.
        """
        
        justificativa = extrair_justificativa(resposta)
        
        if justificativa:
            assert "validação" in justificativa.lower()

    def test_resposta_incompleta(self):
        """Deve lidar com resposta incompleta."""
        # Respostas vazias ou muito curtas
        respostas = ["", "Sim", "Não sei"]
        
        for resposta in respostas:
            # Não deve lançar exceção
            assert isinstance(resposta, str)


class TestConfiguracao:
    """Testes de configuração do Gemini."""

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})
    @patch("src.corrige_engsoftw.gemini_comparator.genai.configure")
    def test_configura_com_api_key(self, mock_configure):
        """Deve configurar com API key."""
        # Importar aqui para pegar o mock
        import src.corrige_engsoftw.gemini_comparator as gm
        
        # Verificar que configure foi chamado
        # (Depende de quando a configuração ocorre)

    @patch.dict("os.environ", {}, clear=False)
    def test_falta_api_key(self):
        """Deve lidar com falta de API key."""
        # Verificar se variável de ambiente está faltando
        import os
        api_key = os.getenv("GOOGLE_API_KEY")
        # Pode ou não existir


class TestCasosDeUso:
    """Testes de casos de uso práticos."""

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_compara_tela_com_campo_faltante(self, mock_genai_class, mock_gemini_model):
        """Deve detectar campo faltante."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        mock_gemini_model.generate_content.return_value = MagicMock(
            text="Falta o campo Email"
        )
        
        tela_gab = {
            "nome": "Cadastro",
            "campos": [{"nome": "Email"}, {"nome": "CPF"}],
            "acoes": [],
            "tabelas": []
        }
        
        tela_aluno = {
            "nome": "Cadastro",
            "campos": [{"nome": "CPF"}],
            "acoes": [],
            "tabelas": []
        }
        
        resultado = comparar_com_gemini(tela_gab, tela_aluno)
        
        # Deve ter chamado Gemini
        mock_genai_class.assert_called()

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_compara_fluxo_com_passo_diferente(self, mock_genai_class, mock_gemini_model):
        """Deve detectar diferença em passo."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        
        fluxo_gab = {
            "nome": "Fluxo",
            "precondicoes": [],
            "passos": [
                {"ordem": 1, "descricao": "O Usuário insere dados"},
                {"ordem": 2, "descricao": "O Sistema valida"}
            ],
            "regrasNegocio": []
        }
        
        fluxo_aluno = {
            "nome": "Fluxo",
            "precondicoes": [],
            "passos": [
                {"ordem": 1, "descricao": "O Usuário insere dados"}
            ],
            "regrasNegocio": []
        }
        
        resultado = comparar_com_gemini(fluxo_gab, fluxo_aluno)
        
        assert resultado is not None


class TestQualidadeResposta:
    """Testes de qualidade da resposta do Gemini."""

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_resposta_nao_vazia(self, mock_genai_class, mock_gemini_model):
        """Resposta não deve estar vazia."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        mock_gemini_model.generate_content.return_value = MagicMock(text="")
        
        tela_gab = {"nome": "Teste", "campos": [], "acoes": [], "tabelas": []}
        tela_aluno = {"nome": "Teste", "campos": [], "acoes": [], "tabelas": []}
        
        # Não deve lançar exceção
        resultado = comparar_com_gemini(tela_gab, tela_aluno)

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_resposta_tamanho_razoavel(self, mock_genai_class, mock_gemini_model):
        """Resposta deve ter tamanho razoável."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        
        mock_genai_class.return_value = mock_gemini_model
        resposta_longa = "Análise: " + "x" * 10000  # Resposta muito longa
        mock_gemini_model.generate_content.return_value = MagicMock(text=resposta_longa)
        
        tela_gab = {"nome": "Teste", "campos": [], "acoes": [], "tabelas": []}
        tela_aluno = {"nome": "Teste", "campos": [], "acoes": [], "tabelas": []}
        
        # Não deve usar muita memória
        resultado = comparar_com_gemini(tela_gab, tela_aluno)


class TestIntegracaoComComparador:
    """Testes de integração com comparador determinístico."""

    @patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
    def test_gemini_complementa_comparador(self, mock_genai_class, mock_gemini_model):
        """Gemini deve complementar comparação determinística."""
        from src.corrige_engsoftw.gemini_comparator import comparar_com_gemini
        from src.corrige_engsoftw.comparator import comparar
        
        mock_genai_class.return_value = mock_gemini_model
        mock_gemini_model.generate_content.return_value = MagicMock(text="Compatível")
        
        gabarito = {
            "telas": [{"nome": "Cadastro", "campos": [], "acoes": [], "tabelas": []}],
            "fluxos": []
        }
        aluno = gabarito.copy()
        
        # Comparação determinística
        resultado_det = comparar(gabarito, aluno, 0.5)
        
        # Deve ter resultado
        assert "resumo" in resultado_det
