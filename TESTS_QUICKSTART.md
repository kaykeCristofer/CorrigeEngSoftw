# ⚡ Quick Start - Testes

## 30 segundos para começar

### 1. Instalar
```bash
pip install -r requirements-test.txt
```

### 2. Executar
```bash
pytest
```

### 3. Pronto! ✅

Você verá algo assim:
```
======================== 146 passed in 12.34s ========================
```

## 5 minutos para entender

### Estrutura
```
tests/
├── conftest.py           # Fixtures compartilhadas
├── unit/                 # Testes de unidades
│   ├── test_*.py        # Um arquivo por módulo
└── integration/          # Testes end-to-end
    └── test_*.py
```

### Comandos Principais
```bash
pytest                              # Todos os testes
pytest tests/unit/                 # Apenas unitários
pytest tests/integration/          # Apenas integração
pytest --cov=src/corrige_engsoftw # Com cobertura
pytest -v                          # Verbose
pytest -k "nome_do_teste"          # Filtrar por nome
pytest -x                          # Parar no primeiro erro
```

### Usando Makefile
```bash
make test               # Todos
make test-unit         # Unitários
make test-coverage     # Com cobertura
make test-fast         # Rápido (< 30s)
make lint              # Verificar código
make format            # Formatar código
```

## Adicionar Novo Teste

### Template Básico
```python
# tests/unit/test_novo_modulo.py
import pytest
from src.corrige_engsoftw.novo_modulo import funcao

class TestNovModulo:
    def test_caso_basico(self):
        resultado = funcao("input")
        assert resultado == "esperado"
    
    def test_com_fixture(self, sample_tela):
        assert sample_tela.nome == "Cadastro"
```

### Rodar Novo Teste
```bash
pytest tests/unit/test_novo_modulo.py -v
```

## Fixtures Disponíveis

### Modelos
```python
def test_usando_fixtures(sample_campo, sample_tela, sample_fluxo):
    assert sample_campo.nome is not None
    assert sample_tela.nome == "Cadastro"
    assert sample_fluxo.nome is not None
```

### JSONs
```python
def test_com_jsons(gabarito_json, aluno_json_completo):
    assert "telas" in gabarito_json
    assert "fluxos" in aluno_json_completo
```

### Diretório Temporário
```python
def test_com_temp_dir(temp_dir):
    arquivo = temp_dir / "teste.json"
    arquivo.write_text('{"teste": true}')
    assert arquivo.exists()
```

### Mock do Gemini
```python
def test_sem_chamar_api_real(mock_gemini_api):
    # mock_gemini_api é autoapplicado
    # Gemini não será chamado
    pass
```

## Debug

### Verbose Mode
```bash
pytest tests/unit/test_text_utils.py -v
```

### Mostrar Output
```bash
pytest tests/unit/test_text_utils.py -s
```

### Parar no Erro
```bash
pytest tests/unit/test_text_utils.py -x
```

### Debugger
```bash
pytest tests/unit/test_text_utils.py --pdb
```

Ou adicione no código:
```python
import pdb; pdb.set_trace()  # Breakpoint
```

## Coverage

### Gerar Relatório
```bash
pytest --cov=src/corrige_engsoftw --cov-report=html
```

### Ver Cobertura
```bash
open htmlcov/index.html  # macOS
# ou
xdg-open htmlcov/index.html  # Linux
```

### Terminal
```bash
pytest --cov=src/corrige_engsoftw --cov-report=term-missing
```

## Problemas Comuns

### "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install -r requirements-test.txt
```

### "Fixture 'sample_tela' not found"
- Verificar se conftest.py está em `tests/conftest.py`
- Reiniciar pytest

### "Timeout"
- Adicionar `--timeout=300` antes de relatar bug
- Ou desabilitar: `pytest --timeout=0`

### "Test is hanging"
- Usar `pytest -x` para ver onde trava
- Adicionar prints para debug
- Usar `pytest --timeout=10`

## Performance

### Rápido
```bash
make test-fast      # ~5 segundos
```

### Normal
```bash
make test           # ~12 segundos
```

### Completo
```bash
make test-coverage  # ~30 segundos
```

## CI/CD

Commits automaticamente testam com:
```bash
# Python 3.9, 3.10, 3.11
# Lint (flake8, isort, black)
# Type checking (mypy)
# Coverage report
```

Ver em: `.github/workflows/tests.yml`

## Próximos Passos

1. **Ler** [TESTING.md](TESTING.md) para guia completo
2. **Explorar** arquivos de teste para entender padrões
3. **Adicionar** seus próprios testes
4. **Rodar** `make test-coverage` regularmente
5. **Manter** > 80% de cobertura

## Links Úteis

- 📖 [TESTING.md](TESTING.md) - Guia completo
- 📊 [COVERAGE.md](COVERAGE.md) - Relatório de cobertura
- 📋 [TESTS_IMPLEMENTATION.md](TESTS_IMPLEMENTATION.md) - O que foi criado
- 🎯 [TESTS_README.md](TESTS_README.md) - Resumo executivo

## Cheat Sheet

```bash
# Básico
pytest                                  # Tudo
pytest -k "nome"                       # Filtrar
pytest -x                              # Parar no erro

# Coverage
pytest --cov                           # Terminal
pytest --cov=src --cov-report=html    # HTML

# Make
make test                              # Tudo
make test-fast                         # Rápido
make test-coverage                     # Com cobertura
make lint                              # Verificar
make format                            # Formatar

# Debug
pytest -v                              # Verbose
pytest -s                              # Show output
pytest -vvs                            # Super verbose
pytest --pdb                           # Debugger
```

## ✅ Você está pronto!

Sua suite de testes está pronta para uso. Comece a:
1. Rodar testes regularmente
2. Adicionar testes para novos recursos
3. Manter cobertura > 80%
4. Usar CI/CD para validar automáticamente

Sucesso! 🚀
