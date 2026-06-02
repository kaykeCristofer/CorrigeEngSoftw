import pytest
import json
from pathlib import Path

from src.corrige_engsoftw.comparator import comparar
from src.corrige_engsoftw.artifacts import carregar_artefato


class TestPipelineExtracao:
    """Testes do pipeline de extração."""

    def test_extrai_documento_valido(self):
        """Deve extrair documento DOCX válido (requer fixture com DOCX)."""
        # Este teste requerer arquivo DOCX real
        # Será implementado com fixtures quando DOCX estiver disponível
        pass


class TestPipelineComparacaoDeterministica:
    """Testes do pipeline de comparação determinística."""

    def test_comparacao_completa_gababrito_aluno(self, gabarito_json, aluno_json_completo):
        """Deve comparar gabarito com aluno completo."""
        resultado = comparar(gabarito_json, aluno_json_completo, 0.72)
        
        # Verificações básicas
        assert "limiteSimilaridade" in resultado
        assert "resumo" in resultado
        assert resultado["resumo"]["percentualCobertura"] > 0

    def test_comparacao_detecta_faltantes(self, gabarito_json, aluno_json_parcial):
        """Deve detectar items faltantes."""
        resultado = comparar(gabarito_json, aluno_json_parcial, 0.72)
        
        # Deve ter items faltantes
        assert resultado["resumo"]["itensCobertos"] < resultado["resumo"]["itensEsperados"]

    def test_comparacao_com_diferentes_limites(self, gabarito_json, aluno_json_parcial):
        """Comportamento muda com limite de similaridade."""
        resultado_flexivel = comparar(gabarito_json, aluno_json_parcial, 0.3)
        resultado_rigoroso = comparar(gabarito_json, aluno_json_parcial, 0.9)
        
        # Com limite mais flexível, deve ter mais itens cobertos
        assert resultado_flexivel["resumo"]["itensCobertos"] >= resultado_rigoroso["resumo"]["itensCobertos"]

    def test_comparacao_retorna_estrutura_valida(self, gabarito_json, aluno_json_completo):
        """Resultado deve ter estrutura válida."""
        resultado = comparar(gabarito_json, aluno_json_completo)
        
        # Verificar chaves principais
        assert isinstance(resultado, dict)
        assert "telas" in resultado
        assert "fluxos" in resultado
        assert "resumo" in resultado
        
        # Verificar resumo
        resumo = resultado["resumo"]
        assert "itensEsperados" in resumo
        assert "itensCobertos" in resumo
        assert "percentualCobertura" in resumo
        assert resumo["percentualCobertura"] >= 0
        assert resumo["percentualCobertura"] <= 100

    def test_comparacao_simetria_telas(self):
        """Comparação de telas deve funcionar bidirecionalmente."""
        gabarito = {
            "telas": [
                {
                    "nome": "Cadastro",
                    "campos": [{"nome": "Email"}],
                    "acoes": [{"nome": "Salvar"}],
                    "tabelas": []
                }
            ],
            "fluxos": []
        }
        
        aluno = {
            "telas": [
                {
                    "nome": "Cadastro",
                    "campos": [{"nome": "Email"}],
                    "acoes": [{"nome": "Salvar"}],
                    "tabelas": []
                }
            ],
            "fluxos": []
        }
        
        resultado = comparar(gabarito, aluno, 0.72)
        assert resultado["resumo"]["percentualCobertura"] == 100.0

    def test_comparacao_fluxos(self):
        """Comparação deve considerar fluxos."""
        gabarito = {
            "telas": [],
            "fluxos": [
                {
                    "nome": "Fluxo principal",
                    "precondicoes": ["Usuário autenticado"],
                    "passos": [{"ordem": 1, "descricao": "O Sistema valida"}],
                    "regrasNegocio": ["CPF válido"]
                }
            ]
        }
        
        aluno = {
            "telas": [],
            "fluxos": [
                {
                    "nome": "Fluxo principal",
                    "precondicoes": ["Usuário autenticado"],
                    "passos": [{"ordem": 1, "descricao": "O Sistema valida"}],
                    "regrasNegocio": ["CPF válido"]
                }
            ]
        }
        
        resultado = comparar(gabarito, aluno, 0.5)
        assert len(resultado["fluxos"]) > 0


class TestIntegracaoCarregamentoeComparacao:
    """Testes de integração entre carregamento e comparação."""

    def test_carrega_json_e_compara(self, temp_dir):
        """Deve carregar JSONs e comparar."""
        gabarito_data = {
            "telas": [{"nome": "Cadastro", "campos": [], "acoes": [], "tabelas": []}],
            "fluxos": []
        }
        aluno_data = gabarito_data.copy()
        
        # Salvar arquivos
        arquivo_gabarito = temp_dir / "gabarito.json"
        arquivo_aluno = temp_dir / "aluno.json"
        
        arquivo_gabarito.write_text(json.dumps(gabarito_data), encoding="utf-8")
        arquivo_aluno.write_text(json.dumps(aluno_data), encoding="utf-8")
        
        # Carregar
        gabarito = carregar_artefato(str(arquivo_gabarito))
        aluno = carregar_artefato(str(arquivo_aluno))
        
        # Comparar
        resultado = comparar(gabarito, aluno, 0.5)
        
        # Verificar
        assert resultado["resumo"]["percentualCobertura"] == 100.0


class TestCasosDeUsoPraticos:
    """Testes de casos de uso práticos."""

    def test_aluno_com_campos_nomeados_diferente(self):
        """Aluno usa sinônimos para campos."""
        gabarito = {
            "telas": [
                {
                    "nome": "Cadastro",
                    "campos": [
                        {"nome": "Valor Unitário"},
                        {"nome": "Código"}
                    ],
                    "acoes": [],
                    "tabelas": []
                }
            ],
            "fluxos": []
        }
        
        aluno = {
            "telas": [
                {
                    "nome": "Cadastro",
                    "campos": [
                        {"nome": "Preço Unitário"},  # Sinônimo
                        {"nome": "Número"}  # Sinônimo de Código
                    ],
                    "acoes": [],
                    "tabelas": []
                }
            ],
            "fluxos": []
        }
        
        resultado = comparar(gabarito, aluno, 0.72)
        
        # Com sinônimos, deve reconhecer equivalência
        assert resultado["telas"][0]["campos"]["cobertos"] > 0

    def test_aluno_com_tela_extra(self):
        """Aluno adicionou tela que não estava no gabarito."""
        gabarito = {
            "telas": [
                {
                    "nome": "Cadastro",
                    "campos": [],
                    "acoes": [{"nome": "Salvar"}],
                    "tabelas": []
                }
            ],
            "fluxos": []
        }
        
        aluno = {
            "telas": [
                {
                    "nome": "Cadastro",
                    "campos": [],
                    "acoes": [{"nome": "Salvar"}],
                    "tabelas": []
                },
                {
                    "nome": "Tela Extra",  # Tela não prevista
                    "campos": [],
                    "acoes": [],
                    "tabelas": []
                }
            ],
            "fluxos": []
        }
        
        resultado = comparar(gabarito, aluno, 0.5)
        
        # Primeira tela deve estar coberta
        assert resultado["telas"][0]["telaEncontrada"] is not None

    def test_aluno_omitiu_fluxo_alternativo(self):
        """Aluno omitiu fluxo alternativo."""
        gabarito = {
            "telas": [],
            "fluxos": [
                {
                    "nome": "Fluxo principal",
                    "precondicoes": [],
                    "passos": [{"ordem": 1, "descricao": "Passo 1"}],
                    "regrasNegocio": []
                },
                {
                    "nome": "Fluxo alternativo - Erro",
                    "precondicoes": [],
                    "passos": [{"ordem": 1, "descricao": "Mostrar erro"}],
                    "regrasNegocio": []
                }
            ]
        }
        
        aluno = {
            "telas": [],
            "fluxos": [
                {
                    "nome": "Fluxo principal",
                    "precondicoes": [],
                    "passos": [{"ordem": 1, "descricao": "Passo 1"}],
                    "regrasNegocio": []
                }
            ]
        }
        
        resultado = comparar(gabarito, aluno, 0.5)
        
        # Cobertura < 100% pois fluxo alternativo está faltando
        assert resultado["resumo"]["percentualCobertura"] < 100.0
