# Documentação de Testes

## Visão Geral

A suite de testes do projeto CorrigeEngSoftw cobre:
- **82 testes unitários** em 5 módulos principais
- **Testes de integração** do pipeline completo
- **Testes de performance** para escalabilidade
- **Testes da CLI** para interface de comando

## Estrutura de Testes

```
tests/
├── conftest.py                 # Fixtures compartilhadas
├── unit/                       # Testes unitários
│   ├── test_text_utils.py     # (24 testes)
│   ├── test_models.py         # (21 testes)
│   ├── test_comparator.py     # (31 testes)
│   ├── test_artifacts.py      # (6 testes)
│   ├── test_extractor.py      # Parsing DOCX
│   ├── test_patterns.py       # Regex patterns
│   ├── test_cli.py            # Interface CLI
│   └── test_gemini_comparator.py  # API Gemini
└── integration/
    ├── test_pipeline.py       # Pipeline end-to-end
    └── test_performance.py    # Testes de performance
```

## Instalação de Dependências

```bash
# Instalar dependências de teste
pip install -r requirements-test.txt

# Ou com conda
conda create -n test-env python=3.11
conda activate test-env
pip install -r requirements-test.txt
```

## Executando Testes

### Todos os testes
```bash
pytest
# ou
make test
```

### Apenas testes unitários
```bash
pytest tests/unit/
# ou
make test-unit
```

### Apenas testes de integração
```bash
pytest tests/integration/
# ou
make test-integration
```

### Com coverage
```bash
pytest --cov=src/corrige_engsoftw --cov-report=html
# ou
make test-coverage
```

### Testes rápidos (excluindo lentos)
```bash
pytest -m "not slow"
# ou
make test-fast
```

### Teste específico
```bash
pytest tests/unit/test_text_utils.py::TestLimparTexto::test_remove_espacos_multiplos
```

## Cobertura de Código

Gerar relatório de cobertura:
```bash
make test-coverage
```

Visualizar em navegador:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Estrutura de Fixtures

### Fixtures Compartilhadas (conftest.py)

#### Models
- `sample_campo`: Campo exemplo
- `sample_acao`: Ação exemplo
- `sample_tabela`: Tabela exemplo
- `sample_tela`: Tela completa
- `sample_passo`: Passo de fluxo
- `sample_fluxo`: Fluxo exemplo

#### JSONs de Teste
- `gabarito_json`: JSON de gabarito completo
- `aluno_json_completo`: JSON de aluno com tudo
- `aluno_json_parcial`: JSON de aluno incompleto
- `aluno_json_vazio`: JSON de aluno vazio

#### Mocks
- `mock_gemini_api`: Mock da API Gemini (autoapplicado a todos)
- `temp_dir`: Diretório temporário

### Uso de Fixtures

```python
def test_exemplo(sample_tela):
    """Usar fixture de tela."""
    assert sample_tela.nome == "Cadastro"
```

## Categorias de Testes

### Testes Unitários (82 testes)

#### test_text_utils.py (24 testes)
- Limpeza de texto
- Normalização de acentos
- Cálculo de similaridade
- Deduplicação

#### test_models.py (21 testes)
- Validação de dataclasses
- Serialização JSON
- Propriedades e métodos

#### test_comparator.py (31 testes)
- Extração de nomes
- Similaridade de conjuntos
- Scoring de telas/fluxos
- Matching e pareamento

#### test_artifacts.py (6 testes)
- Carregamento de JSON
- Carregamento de DOCX
- Validação de estrutura

#### test_extractor.py
- Extração de telas
- Extração de fluxos
- Tratamento de erros
- Normalização

#### test_patterns.py
- Validação de regex patterns
- Reconhecimento de padrões
- Casos extremos

#### test_cli.py
- Comandos da CLI
- Opções e flags
- Validação de entrada

#### test_gemini_comparator.py
- Integração com Gemini
- Parsing de resposta
- Qualidade de resposta

### Testes de Integração

#### test_pipeline.py
- Pipeline de extração
- Pipeline de comparação
- Casos de uso práticos
- Integração completa

#### test_performance.py
- Performance de normalização
- Performance de similaridade
- Escalabilidade
- Uso de memória

## Markers (Etiquetas)

Use para categorizar testes:

```bash
# Apenas unitários
pytest -m unit

# Apenas lentos (não executar)
pytest -m "not slow"

# Apenas que usam mock
pytest -m mock

# Apenas performance
pytest -m performance
```

## Boas Práticas

### 1. Nomenclatura
```python
# ✓ Bom
def test_normaliza_acentos():
    pass

# ✗ Ruim
def test_1():
    pass
```

### 2. Fixtures
```python
# ✓ Usar fixtures
def test_com_fixture(sample_tela):
    assert sample_tela is not None

# ✗ Evitar repetir setup
def test_sem_fixture():
    tela = Tela(...)
    assert tela is not None
```

### 3. Asserções
```python
# ✓ Específico
assert len(resultado) == 5

# ✗ Genérico
assert resultado is not None
```

### 4. Mocks
```python
# ✓ Mock apropriado
@patch("src.corrige_engsoftw.gemini_comparator.genai.GenerativeModel")
def test_com_mock(mock_genai):
    mock_genai.return_value.generate_content.return_value = "resposta"
```

## Testes com Múltiplos Ambientes

Usar tox para testar em Python 3.9, 3.10, 3.11:

```bash
# Testar em todos os ambientes
tox

# Testar em ambiente específico
tox -e py310

# Executar lint
tox -e lint

# Gerar coverage
tox -e coverage
```

## Debugging de Testes

### Modo verbose
```bash
pytest -v -s
```

### Parar no primeiro erro
```bash
pytest -x
```

### Mostrar locals no traceback
```bash
pytest -l
```

### Debugger (pdb)
```python
def test_debug():
    import pdb; pdb.set_trace()
    # ou
    assert False  # pytest --pdb
```

## Relatórios

### Relatório HTML de testes
```bash
pytest --html=report.html --self-contained-html
```

### Relatório JUnit XML
```bash
pytest --junit-xml=report.xml
```

### Combinado
```bash
pytest --html=report.html --junit-xml=report.xml --cov=src
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=src
```

## Troubleshooting

### Fixture não encontrada
```
Error: fixture 'sample_tela' not found
```
✓ Verificar se conftest.py está no mesmo diretório

### Mock não funciona
```
AssertionError: Expected 'function' to have been called
```
✓ Verificar path completo do mock
✓ Verificar se mock foi retornado corretamente

### Teste timeout
```
FAILED - Timeout
```
✓ Aumentar timeout em pytest.ini
✓ Verificar loops infinitos
✓ Usar `pytest -x` para parar rápido

## Performance

Benchmarks executados com:
```bash
make test-performance
```

Tempos esperados:
- Normalização: < 100ms para 10k strings
- Similaridade: < 50ms por par
- Comparação pequena: < 500ms
- Comparação média: < 2s

## Cobertura Esperada

Depois de todos os testes:
- **text_utils.py**: ~95% cobertura
- **models.py**: ~90% cobertura
- **comparator.py**: ~85% cobertura
- **Total esperado**: ~70% cobertura global

## Próximos Passos

1. Aumentar cobertura para 80%+
2. Adicionar testes de mutação
3. Implementar property-based testing
4. Setup de CI/CD completo
5. Testes de carga em produção
