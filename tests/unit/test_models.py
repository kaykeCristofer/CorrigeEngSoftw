"""
Testes unitários para módulo models (dataclasses).
"""

import pytest
from dataclasses import asdict

from src.corrige_engsoftw.models import (
    Campo,
    Acao,
    Tabela,
    Tela,
    Passo,
    Fluxo
)


class TestCampo:
    """Testes para dataclass Campo."""

    def test_criar_campo_minimo(self):
        """Deve criar campo com apenas nome."""
        campo = Campo(nome="Email")
        assert campo.nome == "Email"
        assert campo.obrigatorio is False
        assert campo.validacao is None
        assert campo.exemplo is None
        assert campo.opcoes == []

    def test_criar_campo_completo(self, sample_campo):
        """Deve criar campo com todos os atributos."""
        assert sample_campo.nome == "Email"
        assert sample_campo.obrigatorio is True
        assert sample_campo.validacao == "email válido"
        assert sample_campo.exemplo == "user@example.com"

    def test_serializar_para_dict(self, sample_campo):
        """Deve serializar para dicionário."""
        d = asdict(sample_campo)
        assert d["nome"] == "Email"
        assert d["obrigatorio"] is True

    def test_campo_com_opcoes(self):
        """Deve criar campo com opções."""
        campo = Campo(
            nome="Status",
            opcoes=["Ativo", "Inativo"]
        )
        assert len(campo.opcoes) == 2
        assert "Ativo" in campo.opcoes


class TestAcao:
    """Testes para dataclass Acao."""

    def test_criar_acao(self, sample_acao):
        """Deve criar ação com nome."""
        assert sample_acao.nome == "Salvar"

    def test_serializar_para_dict(self, sample_acao):
        """Deve serializar para dicionário."""
        d = asdict(sample_acao)
        assert d["nome"] == "Salvar"


class TestTabela:
    """Testes para dataclass Tabela."""

    def test_criar_tabela_minima(self):
        """Deve criar tabela com apenas nome."""
        tabela = Tabela(nome="Produtos")
        assert tabela.nome == "Produtos"
        assert tabela.colunas == []

    def test_criar_tabela_completa(self, sample_tabela):
        """Deve criar tabela com colunas."""
        assert sample_tabela.nome == "Produtos"
        assert len(sample_tabela.colunas) == 3
        assert "ID" in sample_tabela.colunas

    def test_serializar_para_dict(self, sample_tabela):
        """Deve serializar para dicionário."""
        d = asdict(sample_tabela)
        assert d["nome"] == "Produtos"
        assert len(d["colunas"]) == 3


class TestTela:
    """Testes para dataclass Tela."""

    def test_criar_tela_minima(self):
        """Deve criar tela com apenas nome."""
        tela = Tela(nome="Cadastro")
        assert tela.nome == "Cadastro"
        assert tela.campos == []
        assert tela.acoes == []
        assert tela.tabelas == []

    def test_criar_tela_completa(self, sample_tela):
        """Deve criar tela com todos os componentes."""
        assert sample_tela.nome == "Tela de Cadastro"
        assert len(sample_tela.campos) == 1
        assert len(sample_tela.acoes) == 1
        assert len(sample_tela.tabelas) == 1

    def test_serializar_para_dict(self, sample_tela):
        """Deve serializar para dicionário com estrutura aninhada."""
        d = asdict(sample_tela)
        assert d["nome"] == "Tela de Cadastro"
        assert len(d["campos"]) == 1
        assert d["campos"][0]["nome"] == "Email"


class TestPasso:
    """Testes para dataclass Passo."""

    def test_criar_passo(self, sample_passo):
        """Deve criar passo com ordem e descrição."""
        assert sample_passo.ordem == 1
        assert sample_passo.descricao == "O Sistema valida os dados"

    def test_serializar_para_dict(self, sample_passo):
        """Deve serializar para dicionário."""
        d = asdict(sample_passo)
        assert d["ordem"] == 1
        assert d["descricao"] == "O Sistema valida os dados"


class TestFluxo:
    """Testes para dataclass Fluxo."""

    def test_criar_fluxo_minimo(self):
        """Deve criar fluxo com apenas nome."""
        fluxo = Fluxo(nome="Fluxo principal")
        assert fluxo.nome == "Fluxo principal"
        assert fluxo.precondicoes == []
        assert fluxo.passos == []
        assert fluxo.regrasNegocio == []

    def test_criar_fluxo_completo(self, sample_fluxo):
        """Deve criar fluxo com todos os componentes."""
        assert sample_fluxo.nome == "Fluxo principal"
        assert len(sample_fluxo.precondicoes) == 1
        assert len(sample_fluxo.passos) == 1
        assert len(sample_fluxo.regrasNegocio) == 1

    def test_serializar_para_dict(self, sample_fluxo):
        """Deve serializar para dicionário com estrutura aninhada."""
        d = asdict(sample_fluxo)
        assert d["nome"] == "Fluxo principal"
        assert len(d["precondicoes"]) == 1
        assert len(d["passos"]) == 1
        assert d["regrasNegocio"][0] == "CPF deve ser válido"

    def test_fluxo_alternativo(self):
        """Deve criar fluxo alternativo com mesma estrutura."""
        fluxo = Fluxo(
            nome="Fluxo alternativo - Erro de validação",
            precondicoes=["Dados inválidos"],
            passos=[Passo(1, "O Sistema exibe mensagem de erro")],
            regrasNegocio=["Mostrar erro específico"]
        )
        assert "Fluxo alternativo" in fluxo.nome
        assert len(fluxo.passos) == 1
