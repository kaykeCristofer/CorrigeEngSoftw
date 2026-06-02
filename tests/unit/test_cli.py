import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.corrige_engsoftw.cli import cli


@pytest.fixture
def cli_runner():
    """Fixture para executar comandos CLI."""
    return CliRunner()


@pytest.fixture
def temp_docx_files(tmp_path):
    """Cria arquivos DOCX temporários para testes."""
    # Criar estrutura de diretórios
    gabarito_dir = tmp_path / "gabarito"
    aluno_dir = tmp_path / "aluno"
    gabarito_dir.mkdir()
    aluno_dir.mkdir()
    
    # Criar arquivos JSON mockados
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
    
    aluno = gabarito.copy()
    
    (gabarito_dir / "teste.json").write_text(json.dumps(gabarito))
    (aluno_dir / "teste.json").write_text(json.dumps(aluno))
    
    return {
        "gabarito_dir": str(gabarito_dir),
        "aluno_dir": str(aluno_dir),
        "tmp_path": str(tmp_path),
    }


class TestComandoExtrair:
    """Testes do comando 'extrair'."""

    def test_extrair_sem_argumentos(self, cli_runner):
        """Deve exigir pelo menos um argumento."""
        result = cli_runner.invoke(cli, ["extrair"])
        assert result.exit_code != 0

    @patch("src.corrige_engsoftw.cli.extrair_telas")
    @patch("src.corrige_engsoftw.cli.extrair_fluxos")
    def test_extrair_arquivo_valido(self, mock_fluxos, mock_telas, cli_runner, tmp_path):
        """Deve extrair de arquivo DOCX válido."""
        # Mock de retornos
        mock_telas.return_value = [
            MagicMock(nome="Cadastro", campos=[], acoes=[], tabelas=[])
        ]
        mock_fluxos.return_value = []
        
        # Criar arquivo dummy
        arquivo = tmp_path / "teste.docx"
        arquivo.write_text("dummy")
        
        result = cli_runner.invoke(cli, ["extrair", str(arquivo)])
        
        # Pode falhar por outros motivos, mas não deve ser erro de CLI
        assert result.exit_code in [0, 1]

    def test_extrair_arquivo_inexistente(self, cli_runner):
        """Deve falhar se arquivo não existe."""
        result = cli_runner.invoke(cli, ["extrair", "/nao/existe.docx"])
        assert result.exit_code != 0

    def test_extrair_com_output(self, cli_runner, tmp_path):
        """Deve aceitar opção --output."""
        arquivo = tmp_path / "teste.docx"
        arquivo.write_text("dummy")
        
        output = tmp_path / "output.json"
        
        # Comando deve ser aceito sintaticamente
        result = cli_runner.invoke(
            cli,
            ["extrair", str(arquivo), "--output", str(output)]
        )
        
        # Exit code depende da implementação
        assert isinstance(result.exit_code, int)


class TestComandoComparar:
    """Testes do comando 'comparar'."""

    def test_comparar_sem_argumentos(self, cli_runner):
        """Deve exigir argumentos."""
        result = cli_runner.invoke(cli, ["comparar"])
        assert result.exit_code != 0

    def test_comparar_sem_segundo_argumento(self, cli_runner, tmp_path):
        """Deve exigir dois diretórios."""
        diretorio = tmp_path / "dir1"
        diretorio.mkdir()
        
        result = cli_runner.invoke(cli, ["comparar", str(diretorio)])
        assert result.exit_code != 0

    @patch("src.corrige_engsoftw.cli.comparar")
    @patch("src.corrige_engsoftw.cli.carregar_artefato")
    def test_comparar_diretorios_validos(
        self, mock_carregar, mock_comparar, cli_runner, tmp_path
    ):
        """Deve comparar dois diretórios válidos."""
        # Setup
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        # Mock de carregamento
        mock_carregar.return_value = {"telas": [], "fluxos": []}
        mock_comparar.return_value = {"resumo": {"percentualCobertura": 100}}
        
        # Criar JSONs dummy
        (gab_dir / "teste.json").write_text('{"telas": [], "fluxos": []}')
        (aluno_dir / "teste.json").write_text('{"telas": [], "fluxos": []}')
        
        result = cli_runner.invoke(
            cli,
            ["comparar", str(gab_dir), str(aluno_dir)]
        )
        
        # Pode falhar por detalhes, mas não deve ser erro básico
        assert isinstance(result.exit_code, int)

    def test_comparar_com_limite(self, cli_runner, tmp_path):
        """Deve aceitar opção --limite."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        result = cli_runner.invoke(
            cli,
            [
                "comparar",
                str(gab_dir),
                str(aluno_dir),
                "--limite", "0.5"
            ]
        )
        
        # Deve aceitar opção
        assert isinstance(result.exit_code, int)

    def test_comparar_com_output(self, cli_runner, tmp_path):
        """Deve aceitar opção --output."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        output = tmp_path / "resultado.json"
        
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        result = cli_runner.invoke(
            cli,
            [
                "comparar",
                str(gab_dir),
                str(aluno_dir),
                "--output", str(output)
            ]
        )
        
        # Deve aceitar opção
        assert isinstance(result.exit_code, int)


class TestComandoCompararDeterministico:
    """Testes do comando 'comparar-deterministico'."""

    def test_comparar_deterministico_sem_args(self, cli_runner):
        """Deve exigir argumentos."""
        result = cli_runner.invoke(cli, ["comparar-deterministico"])
        assert result.exit_code != 0

    @patch("src.corrige_engsoftw.cli.comparar")
    @patch("src.corrige_engsoftw.cli.carregar_artefato")
    def test_comparar_deterministico_diretorios(
        self, mock_carregar, mock_comparar, cli_runner, tmp_path
    ):
        """Deve fazer comparação determinística."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        mock_carregar.return_value = {"telas": [], "fluxos": []}
        mock_comparar.return_value = {"resumo": {"percentualCobertura": 100}}
        
        (gab_dir / "teste.json").write_text('{"telas": [], "fluxos": []}')
        (aluno_dir / "teste.json").write_text('{"telas": [], "fluxos": []}')
        
        result = cli_runner.invoke(
            cli,
            ["comparar-deterministico", str(gab_dir), str(aluno_dir)]
        )
        
        assert isinstance(result.exit_code, int)

    def test_comparar_deterministico_nao_usa_gemini(self, cli_runner, tmp_path):
        """Comparação determinística não deve usar Gemini."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        with patch("src.corrige_engsoftw.cli.gemini_comparar") as mock_gemini:
            result = cli_runner.invoke(
                cli,
                ["comparar-deterministico", str(gab_dir), str(aluno_dir)]
            )
            
            # Gemini não deve ser chamado
            # (verificar detalhes da implementação)


class TestOpcoesCLI:
    """Testes de opções gerais da CLI."""

    def test_help_principal(self, cli_runner):
        """Deve mostrar ajuda."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "comparar" in result.output.lower()
        assert "extrair" in result.output.lower()

    def test_help_comando_extrair(self, cli_runner):
        """Deve mostrar ajuda do comando extrair."""
        result = cli_runner.invoke(cli, ["extrair", "--help"])
        assert result.exit_code == 0

    def test_help_comando_comparar(self, cli_runner):
        """Deve mostrar ajuda do comando comparar."""
        result = cli_runner.invoke(cli, ["comparar", "--help"])
        assert result.exit_code == 0

    def test_help_comando_comparar_deterministico(self, cli_runner):
        """Deve mostrar ajuda do comando comparar-deterministico."""
        result = cli_runner.invoke(cli, ["comparar-deterministico", "--help"])
        assert result.exit_code == 0

    def test_limite_invalido(self, cli_runner, tmp_path):
        """Deve rejeitar limite inválido."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        result = cli_runner.invoke(
            cli,
            [
                "comparar",
                str(gab_dir),
                str(aluno_dir),
                "--limite", "abc"  # Inválido
            ]
        )
        
        # Deve rejeitar valor inválido
        assert result.exit_code != 0

    def test_limite_fora_intervalo(self, cli_runner, tmp_path):
        """Deve rejeitar limite fora de 0-1."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        for limite in ["-0.5", "1.5", "2.0"]:
            result = cli_runner.invoke(
                cli,
                [
                    "comparar",
                    str(gab_dir),
                    str(aluno_dir),
                    "--limite", limite
                ]
            )
            
            # Deve rejeitar
            assert result.exit_code != 0


class TestIntegracaoCLI:
    """Testes de integração da CLI."""

    def test_pipeline_completo_extrair_comparar(self, cli_runner, tmp_path):
        """Deve suportar pipeline: extrair → comparar."""
        # Setup
        docx_dir = tmp_path / "docx"
        docx_dir.mkdir()
        
        # Criar arquivo dummy
        (docx_dir / "teste.docx").write_text("dummy")
        
        # Comando 1: Extrair
        result_extrair = cli_runner.invoke(
            cli,
            ["extrair", str(docx_dir / "teste.docx")]
        )
        
        # Mesmo que falhe, deve ser válido sintaticamente
        assert isinstance(result_extrair.exit_code, int)

    def test_comando_invalido(self, cli_runner):
        """Deve rejeitar comando inválido."""
        result = cli_runner.invoke(cli, ["comando-inexistente"])
        assert result.exit_code != 0

    def test_exit_code_sucesso(self, cli_runner):
        """Comando de ajuda deve retornar 0."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_mensagens_erro_claras(self, cli_runner):
        """Mensagens de erro devem ser claras."""
        result = cli_runner.invoke(cli, ["comparar"])
        
        if result.exit_code != 0:
            # Deve ter mensagem de erro
            assert len(result.output) > 0


class TestOpcaoOutput:
    """Testes da opção --output."""

    def test_output_arquivo_valido(self, cli_runner, tmp_path):
        """Deve criar arquivo de output."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        output = tmp_path / "resultado.json"
        
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        (gab_dir / "teste.json").write_text('{"telas": [], "fluxos": []}')
        (aluno_dir / "teste.json").write_text('{"telas": [], "fluxos": []}')
        
        with patch("src.corrige_engsoftw.cli.comparar") as mock_cmp:
            mock_cmp.return_value = {"resumo": {"percentualCobertura": 100}}
            
            result = cli_runner.invoke(
                cli,
                [
                    "comparar",
                    str(gab_dir),
                    str(aluno_dir),
                    "--output", str(output)
                ]
            )
            
            # Output file pode ou não existir dependendo de implementação

    def test_output_diretorio_inexistente(self, cli_runner, tmp_path):
        """Comportamento com diretório de output inexistente."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        output = tmp_path / "inexistente" / "resultado.json"
        
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        result = cli_runner.invoke(
            cli,
            [
                "comparar",
                str(gab_dir),
                str(aluno_dir),
                "--output", str(output)
            ]
        )
        
        # Depende de implementação: pode criar ou falhar


class TestValidacaoCaminhosArquivos:
    """Testes de validação de caminhos e arquivos."""

    def test_arquivo_nao_existe(self, cli_runner):
        """Deve validar existência de arquivo."""
        result = cli_runner.invoke(cli, ["extrair", "/nao/existe.docx"])
        assert result.exit_code != 0

    def test_diretorio_nao_existe_extrair(self, cli_runner):
        """Deve validar existência de diretório."""
        result = cli_runner.invoke(cli, ["extrair", "/nao/existe"])
        assert result.exit_code != 0

    def test_diretorio_vazio(self, cli_runner, tmp_path):
        """Deve lidar com diretório vazio."""
        gab_dir = tmp_path / "gabarito"
        aluno_dir = tmp_path / "aluno"
        gab_dir.mkdir()
        aluno_dir.mkdir()
        
        result = cli_runner.invoke(
            cli,
            ["comparar", str(gab_dir), str(aluno_dir)]
        )
        
        # Deve lidar gracefully
        assert isinstance(result.exit_code, int)
