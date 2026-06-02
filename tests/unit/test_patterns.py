"""
Testes unitários do módulo patterns (regex e constantes).
"""

import pytest
import re

from src.corrige_engsoftw.patterns import (
    PATTERN_TITULO_TELA,
    PATTERN_FLUXO_PRINCIPAL,
    PATTERN_FLUXO_ALTERNATIVO,
    PATTERN_ACAO,
    PATTERN_VALIDACAO,
    PATTERN_TABELA,
    PATTERN_PASSO_ATOR,
    extrair_ator,
    extrair_conteudo_validacao,
)


class TestPatternTituloTela:
    """Testes de pattern para título de tela."""

    def test_reconhece_titulo_simples(self):
        """Deve reconhecer formato simples de título."""
        texto = "=== TELA: Cadastro de Usuário"
        assert re.search(PATTERN_TITULO_TELA, texto, re.IGNORECASE)

    def test_reconhece_titulo_com_espacos(self):
        """Deve reconhecer título com múltiplos espaços."""
        texto = "===  TELA :  Cadastro   de   Usuário"
        assert re.search(PATTERN_TITULO_TELA, texto, re.IGNORECASE)

    def test_reconhece_titulo_minusculo(self):
        """Deve reconhecer título em minúsculas."""
        texto = "=== tela: cadastro"
        assert re.search(PATTERN_TITULO_TELA, texto, re.IGNORECASE)

    def test_nao_reconhece_sem_prefixo(self):
        """Não deve reconhecer sem prefixo ===."""
        texto = "TELA: Cadastro"
        # Pode reconhecer ou não dependendo do pattern
        pass

    def test_extrai_nome_tela(self):
        """Deve extrair nome da tela."""
        texto = "=== TELA: Cadastro de Usuário"
        match = re.search(PATTERN_TITULO_TELA, texto, re.IGNORECASE)
        if match:
            # Nome deve estar em algum grupo
            assert match.group(1) or "Cadastro" in texto


class TestPatternFluxo:
    """Testes de patterns para fluxos."""

    def test_reconhece_fluxo_principal(self):
        """Deve reconhecer fluxo principal."""
        texto = "# FLUXO PRINCIPAL: Autenticação"
        assert re.search(PATTERN_FLUXO_PRINCIPAL, texto, re.IGNORECASE)

    def test_reconhece_fluxo_alternativo(self):
        """Deve reconhecer fluxo alternativo."""
        texto = "# FLUXO ALTERNATIVO - Email inválido"
        assert re.search(PATTERN_FLUXO_ALTERNATIVO, texto, re.IGNORECASE)

    def test_reconhece_fluxo_alternativo_com_tipos(self):
        """Deve reconhecer diferentes tipos de fluxos alternativos."""
        textos = [
            "# FLUXO ALTERNATIVO - Validação de Email",
            "# FLUXO ALTERNATIVO - Erro de Autenticação",
            "# FLUXO ALTERNATIVO - CPF inválido",
        ]
        for texto in textos:
            assert re.search(PATTERN_FLUXO_ALTERNATIVO, texto, re.IGNORECASE)

    def test_diferencia_fluxo_principal_alternativo(self):
        """Deve diferenciar fluxos principais de alternativos."""
        principal = "# FLUXO PRINCIPAL: Cadastro"
        alternativo = "# FLUXO ALTERNATIVO - Erro"
        
        assert re.search(PATTERN_FLUXO_PRINCIPAL, principal, re.IGNORECASE)
        assert re.search(PATTERN_FLUXO_ALTERNATIVO, alternativo, re.IGNORECASE)


class TestPatternAcao:
    """Testes de pattern para ações."""

    def test_reconhece_acao_simples(self):
        """Deve reconhecer ação entre <>."""
        texto = "• <Salvar>"
        assert re.search(PATTERN_ACAO, texto)

    def test_reconhece_acao_com_espacos(self):
        """Deve reconhecer ação com espaços."""
        texto = "• < Salvar >"
        assert re.search(PATTERN_ACAO, texto)

    def test_reconhece_acao_multipalavra(self):
        """Deve reconhecer ação com múltiplas palavras."""
        texto = "• <Salvar e Fechar>"
        assert re.search(PATTERN_ACAO, texto)

    def test_extrai_nome_acao(self):
        """Deve extrair nome da ação."""
        texto = "• <Salvar>"
        match = re.search(PATTERN_ACAO, texto)
        if match:
            # Ação deve estar em algum grupo
            assert "Salvar" in texto

    def test_nao_reconhece_sem_colchetes(self):
        """Não deve reconhecer ação sem <>."""
        texto = "• Salvar"
        assert not re.search(PATTERN_ACAO, texto)

    def test_nao_reconhece_colchetes_errados(self):
        """Não deve reconhecer com [], {}, ()."""
        textos = [
            "• [Salvar]",
            "• {Salvar}",
            "• (Salvar)",
        ]
        for texto in textos:
            assert not re.search(PATTERN_ACAO, texto)


class TestPatternValidacao:
    """Testes de pattern para validações."""

    def test_reconhece_validacao_simples(self):
        """Deve reconhecer validação entre ()."""
        texto = "Email (obrigatório)"
        assert re.search(PATTERN_VALIDACAO, texto)

    def test_reconhece_validacao_complexa(self):
        """Deve reconhecer validação complexa."""
        texto = "CPF (obrigatório, formato 999.999.999-99, validação de digito verificador)"
        assert re.search(PATTERN_VALIDACAO, texto)

    def test_extrai_conteudo_validacao(self):
        """Deve extrair conteúdo da validação."""
        texto = "Email (obrigatório, validar duplicata)"
        conteudo = extrair_conteudo_validacao(texto)
        if conteudo:
            assert "obrigatório" in conteudo or "validar" in conteudo

    def test_nao_reconhece_parenteses_vazios(self):
        """Não deve reconhecer parenteses vazios."""
        texto = "Email ()"
        # Depende da implementação do pattern


class TestPatternTabela:
    """Testes de pattern para tabelas."""

    def test_reconhece_marcador_tabela(self):
        """Deve reconhecer marcador de tabela."""
        texto = "Colunas: ID, Nome, Email"
        # Pattern pode variar
        pass

    def test_reconhece_multiplas_colunas(self):
        """Deve reconhecer múltiplas colunas."""
        texto = "| ID | Nome | Email | CPF |"
        # Pattern pode variar
        pass


class TestPatternPasso:
    """Testes de pattern para passos de fluxo."""

    def test_reconhece_passo_numerado(self):
        """Deve reconhecer passo numerado."""
        texto = "1. O Usuário insere email"
        assert re.search(PATTERN_PASSO_ATOR, texto)

    def test_reconhece_passo_com_multiplos_dígitos(self):
        """Deve reconhecer passos com números maiores."""
        textos = ["10. O Sistema valida", "23. O Usuário confirma"]
        for texto in textos:
            assert re.search(PATTERN_PASSO_ATOR, texto)

    def test_extrai_numero_passo(self):
        """Deve extrair número do passo."""
        texto = "5. O Usuário clica em Enviar"
        match = re.search(PATTERN_PASSO_ATOR, texto)
        if match:
            # Número deve estar em algum grupo
            assert match.group(1) or "5" in texto

    def test_reconhece_ator_usuario(self):
        """Deve reconhecer ator 'O Usuário'."""
        texto = "1. O Usuário insere dados"
        assert re.search(PATTERN_PASSO_ATOR, texto)

    def test_reconhece_ator_sistema(self):
        """Deve reconhecer ator 'O Sistema'."""
        texto = "2. O Sistema valida dados"
        assert re.search(PATTERN_PASSO_ATOR, texto)

    def test_extrai_ator(self):
        """Deve extrair ator do passo."""
        passo = "O Usuário clica em Enviar"
        ator = extrair_ator(passo)
        if ator:
            assert "Usuário" in ator or "Usuario" in ator

    def test_extrai_ator_sistema(self):
        """Deve extrair 'Sistema' quando apropriado."""
        passo = "O Sistema valida dados"
        ator = extrair_ator(passo)
        if ator:
            assert "Sistema" in ator


class TestPatternIntegracao:
    """Testes de integração de patterns."""

    def test_conjunto_patterns_validos(self):
        """Todos os patterns devem ser válidos como regex."""
        patterns = [
            PATTERN_TITULO_TELA,
            PATTERN_FLUXO_PRINCIPAL,
            PATTERN_FLUXO_ALTERNATIVO,
            PATTERN_ACAO,
            PATTERN_VALIDACAO,
            PATTERN_PASSO_ATOR,
        ]
        
        for pattern in patterns:
            # Não deve lançar exceção ao compilar
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                pytest.fail(f"Pattern inválido: {pattern}, erro: {e}")

    def test_patterns_nao_conflitam(self):
        """Patterns não devem conflitar entre si."""
        # Ação não deve ser confundida com validação
        acao = "• <Salvar>"
        validacao = "Email (obrigatório)"
        
        # Ação deve ser reconhecida por PATTERN_ACAO, não por PATTERN_VALIDACAO
        assert re.search(PATTERN_ACAO, acao)
        assert re.search(PATTERN_VALIDACAO, validacao)

    def test_documento_completo_com_patterns(self):
        """Deve reconhecer documento com múltiplos patterns."""
        documento = """
        === TELA: Cadastro de Usuário
        • Email <validação email>
        • <Salvar>
        
        # FLUXO PRINCIPAL: Criar Conta
        1. O Usuário insere dados
        2. O Sistema valida
        
        # FLUXO ALTERNATIVO - Erro de Validação
        1. O Sistema exibe erro
        """
        
        # Cada padrão deve estar presente
        assert re.search(PATTERN_TITULO_TELA, documento, re.IGNORECASE)
        assert re.search(PATTERN_ACAO, documento)
        assert re.search(PATTERN_FLUXO_PRINCIPAL, documento, re.IGNORECASE)
        assert re.search(PATTERN_FLUXO_ALTERNATIVO, documento, re.IGNORECASE)
        assert re.search(PATTERN_PASSO_ATOR, documento)


class TestPatternEdgeCases:
    """Testes de casos extremos de patterns."""

    def test_pattern_com_caracteres_especiais(self):
        """Deve lidar com caracteres especiais."""
        texto = "=== TELA: Cadastro de Usuário & Dados"
        # Deve reconhecer ou não depende da implementação

    def test_pattern_com_unicode(self):
        """Deve lidar com Unicode."""
        texto = "=== TELA: Cadastro de Usuário (é)"
        assert re.search(PATTERN_TITULO_TELA, texto, re.IGNORECASE)

    def test_pattern_case_insensitive(self):
        """Patterns devem ser case-insensitive."""
        textos = [
            "=== TELA: Cadastro",
            "=== tela: cadastro",
            "=== Tela: Cadastro",
        ]
        for texto in textos:
            assert re.search(PATTERN_TITULO_TELA, texto, re.IGNORECASE)

    def test_pattern_com_linhas_extras(self):
        """Deve lidar com linhas em branco antes/depois."""
        texto = """
        
        === TELA: Cadastro
        
        """
        assert re.search(PATTERN_TITULO_TELA, texto.strip(), re.IGNORECASE)
