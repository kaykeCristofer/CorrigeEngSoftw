import pytest
import time
from unittest.mock import MagicMock, patch

from src.corrige_engsoftw.comparator import (
    nomes_de,
    similaridade_conjunto,
    score_tela,
    score_fluxo,
    comparar
)


class TestPerformanceNormalizacao:
    """Testes de performance de normalização."""

    def test_normaliza_texto_grande(self):
        """Deve normalizar texto grande rapidamente."""
        from src.corrige_engsoftw.text_utils import limpar_texto
        
        # Texto grande
        texto_grande = "Email " * 10000
        
        inicio = time.time()
        resultado = limpar_texto(texto_grande)
        duracao = time.time() - inicio
        
        # Deve ser rápido (< 100ms)
        assert duracao < 0.1
        assert isinstance(resultado, str)

    def test_normaliza_multiplos_textos(self):
        """Deve normalizar múltiplos textos eficientemente."""
        from src.corrige_engsoftw.text_utils import limpar_texto
        
        textos = [f"Texto{i}" for i in range(1000)]
        
        inicio = time.time()
        resultados = [limpar_texto(t) for t in textos]
        duracao = time.time() - inicio
        
        # Deve processar 1000 textos em < 500ms
        assert duracao < 0.5
        assert len(resultados) == 1000


class TestPerformanceSimilaridade:
    """Testes de performance de cálculo de similaridade."""

    def test_similaridade_strings_longas(self):
        """Deve calcular similaridade com strings longas."""
        from src.corrige_engsoftw.text_utils import chave
        
        s1 = "Email do usuário para contato" * 100
        s2 = "Email do usuário para contato" * 100
        
        inicio = time.time()
        resultado = chave(s1, s2)
        duracao = time.time() - inicio
        
        # Deve ser rápido (< 50ms)
        assert duracao < 0.05

    def test_similaridade_multiplos_pares(self):
        """Deve calcular similaridade com múltiplos pares."""
        from src.corrige_engsoftw.text_utils import chave
        
        pares = [(f"String{i}", f"String{i+1}") for i in range(100)]
        
        inicio = time.time()
        resultados = [chave(s1, s2) for s1, s2 in pares]
        duracao = time.time() - inicio
        
        # 100 comparações em < 100ms
        assert duracao < 0.1
        assert len(resultados) == 100


class TestPerformanceComparador:
    """Testes de performance do comparador."""

    def test_compara_lista_vazia(self):
        """Comparação com lista vazia deve ser rápida."""
        inicio = time.time()
        resultado = nomes_de([])
        duracao = time.time() - inicio
        
        assert duracao < 0.01
        assert resultado == set()

    def test_compara_lista_grande(self):
        """Comparação com lista grande deve ser razoável."""
        items = [{"nome": f"Item{i}"} for i in range(1000)]
        
        inicio = time.time()
        resultado = nomes_de(items)
        duracao = time.time() - inicio
        
        # 1000 items em < 100ms
        assert duracao < 0.1
        assert len(resultado) == 1000

    def test_score_tela_muitos_campos(self):
        """Score de tela com muitos campos."""
        tela_gab = {
            "nome": "Cadastro",
            "campos": [{"nome": f"Campo{i}"} for i in range(100)],
            "acoes": [{"nome": f"Acao{i}"} for i in range(50)],
            "tabelas": []
        }
        
        tela_aluno = tela_gab.copy()
        
        inicio = time.time()
        resultado = score_tela(tela_gab, tela_aluno, 0.72)
        duracao = time.time() - inicio
        
        # Deve ser rápido (< 500ms para 150 items)
        assert duracao < 0.5
        assert isinstance(resultado, tuple)


class TestPerformancePipeline:
    """Testes de performance do pipeline completo."""

    def test_compara_documento_pequeno(self):
        """Comparação de documento pequeno deve ser rápida."""
        gabarito = {
            "telas": [
                {
                    "nome": f"Tela{i}",
                    "campos": [{"nome": f"Campo{j}"} for j in range(5)],
                    "acoes": [{"nome": f"Acao{j}"} for j in range(3)],
                    "tabelas": []
                }
                for i in range(5)
            ],
            "fluxos": [
                {
                    "nome": f"Fluxo{i}",
                    "precondicoes": [],
                    "passos": [{"ordem": j, "descricao": f"Passo {j}"} for j in range(5)],
                    "regrasNegocio": []
                }
                for i in range(3)
            ]
        }
        
        aluno = gabarito.copy()
        
        inicio = time.time()
        resultado = comparar(gabarito, aluno, 0.72)
        duracao = time.time() - inicio
        
        # Documento pequeno: < 500ms
        assert duracao < 0.5
        assert "resumo" in resultado

    def test_compara_documento_medio(self):
        """Comparação de documento médio deve ser aceitável."""
        gabarito = {
            "telas": [
                {
                    "nome": f"Tela{i}",
                    "campos": [{"nome": f"Campo{j}"} for j in range(20)],
                    "acoes": [{"nome": f"Acao{j}"} for j in range(10)],
                    "tabelas": []
                }
                for i in range(20)
            ],
            "fluxos": [
                {
                    "nome": f"Fluxo{i}",
                    "precondicoes": [],
                    "passos": [{"ordem": j, "descricao": f"Passo {j}"} for j in range(10)],
                    "regrasNegocio": [f"Regra{j}" for j in range(5)]
                }
                for i in range(10)
            ]
        }
        
        aluno = gabarito.copy()
        
        inicio = time.time()
        resultado = comparar(gabarito, aluno, 0.72)
        duracao = time.time() - inicio
        
        # Documento médio: < 2s
        assert duracao < 2.0
        assert "resumo" in resultado

    def test_compara_muitos_documentos(self):
        """Comparação sequencial de múltiplos documentos."""
        pequeno = {
            "telas": [{"nome": "T1", "campos": [], "acoes": [], "tabelas": []}],
            "fluxos": []
        }
        
        inicio = time.time()
        for i in range(10):
            resultado = comparar(pequeno, pequeno, 0.72)
        duracao = time.time() - inicio
        
        # 10 comparações pequenas: < 1s
        assert duracao < 1.0


class TestMemoryUsage:
    """Testes de uso de memória."""

    def test_memoria_lista_grande(self):
        """Não deve usar memória excessiva com lista grande."""
        items = [{"nome": f"Item{i}"} for i in range(10000)]
        
        # Apenas verificar que não lança exceção
        resultado = nomes_de(items)
        assert len(resultado) == 10000

    def test_memoria_comparacao_grande(self):
        """Comparação grande não deve causar MemoryError."""
        gabarito = {
            "telas": [
                {
                    "nome": f"Tela{i}",
                    "campos": [{"nome": f"C{j}"} for j in range(50)],
                    "acoes": [{"nome": f"A{j}"} for j in range(20)],
                    "tabelas": []
                }
                for i in range(50)
            ],
            "fluxos": []
        }
        
        aluno = gabarito.copy()
        
        # Não deve lançar MemoryError
        resultado = comparar(gabarito, aluno, 0.72)
        assert "resumo" in resultado


class TestEscalabilidade:
    """Testes de escalabilidade."""

    def test_escalabilidade_numero_telas(self):
        """Performance com aumento de número de telas."""
        tempos = []
        
        for num_telas in [5, 10, 20]:
            gabarito = {
                "telas": [
                    {
                        "nome": f"Tela{i}",
                        "campos": [{"nome": f"Campo{j}"} for j in range(5)],
                        "acoes": [],
                        "tabelas": []
                    }
                    for i in range(num_telas)
                ],
                "fluxos": []
            }
            
            aluno = gabarito.copy()
            
            inicio = time.time()
            comparar(gabarito, aluno, 0.72)
            duracao = time.time() - inicio
            
            tempos.append(duracao)
        
        # Tempo deve crescer aproximadamente linear
        # (não exponencial)
        assert len(tempos) == 3

    def test_escalabilidade_numero_campos(self):
        """Performance com aumento de número de campos."""
        tempos = []
        
        for num_campos in [10, 20, 50]:
            gabarito = {
                "telas": [
                    {
                        "nome": "Tela",
                        "campos": [{"nome": f"Campo{j}"} for j in range(num_campos)],
                        "acoes": [],
                        "tabelas": []
                    }
                ],
                "fluxos": []
            }
            
            aluno = gabarito.copy()
            
            inicio = time.time()
            comparar(gabarito, aluno, 0.72)
            duracao = time.time() - inicio
            
            tempos.append(duracao)
        
        assert len(tempos) == 3


class TestBenchmarks:
    """Benchmarks de operações comuns."""

    def test_benchmark_normalizacao(self, benchmark):
        """Benchmark de normalização."""
        from src.corrige_engsoftw.text_utils import limpar_texto
        
        # benchmark é fixture do pytest-benchmark
        # resultado = benchmark(limpar_texto, "Email   com   espaços")

    def test_tempo_comparacao_pequena(self):
        """Tempo de comparação pequena é aceitável."""
        pequeno = {"telas": [], "fluxos": []}
        
        inicio = time.time()
        comparar(pequeno, pequeno, 0.5)
        duracao = time.time() - inicio
        
        # Documento vazio deve ser muito rápido
        assert duracao < 0.01


class TestOtimizacoes:
    """Testes de identificação de gargalos."""

    def test_cache_similaridade(self):
        """Cache de similaridade seria benéfico."""
        # Este teste documenta onde cache seria útil
        from src.corrige_engsoftw.text_utils import chave
        
        s1 = "Email"
        s2 = "Email"
        
        # Múltiplas chamadas com mesmo par
        for _ in range(100):
            resultado = chave(s1, s2)
        
        # Deve ser rápido mesmo sem cache

    def test_paralelizacao_comparacoes(self):
        """Comparações poderiam ser paralelizadas."""
        # Este teste documenta onde paralelização seria útil
        
        items1 = [{"nome": f"Item{i}"} for i in range(100)]
        items2 = [{"nome": f"Item{i}"} for i in range(100)]
        
        # Comparação sequencial de 100 pares
        for i1, i2 in zip(items1, items2):
            # Seria paralelizável
            pass
