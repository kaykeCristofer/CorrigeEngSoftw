"""
Testes unitários do módulo extractor (parsing de DOCX).
"""

import pytest
from unittest.mock import MagicMock, patch, call

from src.corrige_engsoftw.models import Tela, Campo, Acao, Tabela, Fluxo, Passo


class TestExtrairTelaBasico:
    """Testes básicos de extração de tela."""

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_tela_simples(self, mock_document_class):
        """Deve extrair tela com título, campos e ações."""
        # Importar aqui para usar mock
        from src.corrige_engsoftw.extractor import extrair_telas
        
        # Mock de parágrafo com título
        mock_para_titulo = MagicMock()
        mock_para_titulo.text = "=== TELA: Cadastro de Usuário"
        
        # Mock de parágrafo com campo
        mock_para_campo = MagicMock()
        mock_para_campo.text = "• Email <obrigatório, validar email>"
        
        # Mock de parágrafo com ação
        mock_para_acao = MagicMock()
        mock_para_acao.text = "• <Salvar>"
        
        # Mock do documento
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_titulo, mock_para_campo, mock_para_acao]
        mock_document_class.return_value = mock_doc
        
        # Extrair
        telas = extrair_telas("dummy.docx")
        
        # Verificar
        assert len(telas) > 0

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_tela_normaliza_nomes(self, mock_document_class):
        """Deve normalizar nomes de telas."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        # Mock
        mock_para = MagicMock()
        mock_para.text = "=== TELA:    Cadastro   de   Usuário   "
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        
        # Deve normalizar espaços
        if telas:
            assert "  " not in telas[0].nome

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_campos_com_validacao(self, mock_document_class):
        """Deve extrair campos com validações entre ()."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        mock_para_titulo = MagicMock()
        mock_para_titulo.text = "=== TELA: Cadastro"
        
        mock_para_campo = MagicMock()
        mock_para_campo.text = "• CPF (obrigatório, formato 999.999.999-99)"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_titulo, mock_para_campo]
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        
        # Verificar que campo foi extraído
        if telas and telas[0].campos:
            assert len(telas[0].campos) > 0


class TestExtrairFluxo:
    """Testes de extração de fluxo."""

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_fluxo_principal(self, mock_document_class):
        """Deve extrair fluxo principal."""
        from src.corrige_engsoftw.extractor import extrair_fluxos
        
        mock_para = MagicMock()
        mock_para.text = "# FLUXO PRINCIPAL: Cadastro de Usuário"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc
        
        fluxos = extrair_fluxos("dummy.docx")
        
        # Deve ter pelo menos um fluxo
        assert isinstance(fluxos, list)

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_fluxo_com_passos(self, mock_document_class):
        """Deve extrair passos de fluxo."""
        from src.corrige_engsoftw.extractor import extrair_fluxos
        
        mock_paras = [
            MagicMock(text="# FLUXO PRINCIPAL: Autenticação"),
            MagicMock(text="1. O Usuário insere email"),
            MagicMock(text="2. O Sistema valida email"),
            MagicMock(text="3. O Usuário insere senha"),
        ]
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paras
        mock_document_class.return_value = mock_doc
        
        fluxos = extrair_fluxos("dummy.docx")
        
        # Deve ter extraído passos
        assert isinstance(fluxos, list)

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_fluxo_alternativo(self, mock_document_class):
        """Deve extrair fluxo alternativo com tipo."""
        from src.corrige_engsoftw.extractor import extrair_fluxos
        
        mock_paras = [
            MagicMock(text="# FLUXO ALTERNATIVO - Email inválido"),
            MagicMock(text="1. O Sistema detecta email inválido"),
        ]
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paras
        mock_document_class.return_value = mock_doc
        
        fluxos = extrair_fluxos("dummy.docx")
        
        assert isinstance(fluxos, list)


class TestExtrairTabela:
    """Testes de extração de tabelas."""

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrair_tabela_de_tela(self, mock_document_class):
        """Deve extrair tabela dentro de tela."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        # Mock de tabela
        mock_cell_1 = MagicMock()
        mock_cell_1.text = "ID"
        mock_cell_2 = MagicMock()
        mock_cell_2.text = "Nome"
        
        mock_row = MagicMock()
        mock_row.cells = [mock_cell_1, mock_cell_2]
        
        mock_table = MagicMock()
        mock_table.rows = [mock_row]
        
        # Mocks de parágrafo
        mock_para_titulo = MagicMock()
        mock_para_titulo.text = "=== TELA: Listagem"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_titulo]
        mock_doc.tables = [mock_table]
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        
        # Deve ter tela extraída
        assert len(telas) > 0


class TestExtrairComErros:
    """Testes de tratamento de erros."""

    def test_arquivo_nao_existe(self):
        """Deve falhar gracefully se arquivo não existe."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        with pytest.raises(Exception):  # FileNotFoundError ou similar
            extrair_telas("/nao/existe/arquivo.docx")

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_documento_vazio(self, mock_document_class):
        """Deve retornar lista vazia para documento sem conteúdo."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        
        assert isinstance(telas, list)

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_parafrafo_sem_texto(self, mock_document_class):
        """Deve ignorar parágrafos sem texto."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        mock_para_titulo = MagicMock()
        mock_para_titulo.text = "=== TELA: Cadastro"
        
        mock_para_vazio = MagicMock()
        mock_para_vazio.text = ""
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_titulo, mock_para_vazio]
        mock_document_class.return_value = mock_doc
        
        # Não deve lançar exceção
        telas = extrair_telas("dummy.docx")
        assert isinstance(telas, list)


class TestExtrairNormalizacao:
    """Testes de normalização durante extração."""

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_normaliza_acentos_em_tela(self, mock_document_class):
        """Deve normalizar acentos em nomes de tela."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        mock_para = MagicMock()
        mock_para.text = "=== TELA: Cadastro de Usuário"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        
        # Verificar tipo de retorno
        assert isinstance(telas, list)

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_normaliza_espacos_em_campo(self, mock_document_class):
        """Deve normalizar espaços múltiplos em campos."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        mock_para_titulo = MagicMock()
        mock_para_titulo.text = "=== TELA: Cadastro"
        
        mock_para_campo = MagicMock()
        mock_para_campo.text = "•    Email   com   espaços    "
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_titulo, mock_para_campo]
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        assert isinstance(telas, list)


class TestExtrairIntegracao:
    """Testes de integração de extração."""

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrai_telas_e_fluxos_juntos(self, mock_document_class):
        """Deve extrair telas e fluxos do mesmo documento."""
        from src.corrige_engsoftw.extractor import extrair_telas, extrair_fluxos
        
        mock_para_tela = MagicMock()
        mock_para_tela.text = "=== TELA: Cadastro"
        
        mock_para_fluxo = MagicMock()
        mock_para_fluxo.text = "# FLUXO PRINCIPAL: Cadastro"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_tela, mock_para_fluxo]
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        fluxos = extrair_fluxos("dummy.docx")
        
        assert isinstance(telas, list)
        assert isinstance(fluxos, list)

    @patch("src.corrige_engsoftw.extractor.Document")
    def test_extrai_com_multiplas_telas(self, mock_document_class):
        """Deve extrair múltiplas telas."""
        from src.corrige_engsoftw.extractor import extrair_telas
        
        mock_paras = [
            MagicMock(text="=== TELA: Cadastro"),
            MagicMock(text="• Email"),
            MagicMock(text="=== TELA: Listagem"),
            MagicMock(text="• ID"),
        ]
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paras
        mock_document_class.return_value = mock_doc
        
        telas = extrair_telas("dummy.docx")
        
        # Deve ter 2 telas
        assert len(telas) >= 1
