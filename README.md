# CorrigeEngSoftw

Sistema para apoiar a correção de trabalhos de Engenharia de Software a partir de protótipos em arquivos `.docx`.

A ideia é comparar um protótipo original, usado como **gabarito**, com um ou mais protótipos entregues por alunos. O sistema extrai telas, campos, ações, tabelas e fluxos dos documentos, gera uma comparação determinística e, opcionalmente, usa o Gemini para uma avaliação semântica.

## Onde Colocar Os Arquivos

Use esta organização:

```text
prototypes/
  gestao-contas/
    Prototipo.docx                  # gabarito do cenário gestão de contas
  sistema-mercado/
    Prototipo.docx                  # gabarito do cenário sistema de mercado

inputs/
  fixtures/
    prototypes/
      gestao-contas/
        Prototipo_gestao_teste1.docx
        Prototipo_gestao_teste2.docx
      sistema-mercado/
        Prototipo_mercado_teste1.docx
        Prototipo_mercado_teste2.docx

outputs/
  resultado_Prototipo_gestao_teste1.json
  resultado_Prototipo_mercado_teste1.json
```

Convenção recomendada:

- Coloque os gabaritos em `prototypes/<nome-do-cenario>/Prototipo.docx`.
- Coloque os protótipos dos alunos em `inputs/fixtures/prototypes/<nome-do-cenario>/`.
- Os relatórios gerados devem ficar em `outputs/`.

## Caminhos Padrão Da CLI

Quando você executa os comandos sem informar caminhos, o sistema usa:

```text
Gabarito padrão:
prototypes/gestao-contas/Prototipo.docx

Pasta padrão dos protótipos dos alunos:
inputs/fixtures/prototypes/gestao-contas

Pasta padrão de saída:
outputs
```

O sistema gera um arquivo por aluno em `outputs/`, com o formato:

```text
outputs/resultado_<nome_do_arquivo_do_aluno>.json
```

Exemplo:

```text
inputs/fixtures/prototypes/gestao-contas/Prototipo_gestao_teste1.docx
```

gera:

```text
outputs/resultado_Prototipo_gestao_teste1.json
```

## Configuração

Crie um arquivo `.env` na raiz do projeto para usar a comparação com Gemini:

```env
GENAI_API_KEY=sua_chave_do_gemini
GEMINI_MODEL=models/gemini-flash-latest
```

Também é aceito:

```env
GEMINI_API_KEY=sua_chave_do_gemini
```

A comparação determinística não usa internet nem chave de API.

Para modicar o caminho para o gabarito, entradas e saídas sem utilizar o terminal, vá em src/corrige_engsoftw/cli.py e atualize os caminhos padrões:

```bash
DEFAULT_GABARITO = Path("prototypes/gestao-contas/Prototipo.docx")
DEFAULT_DIRETORIO_ALUNOS = Path("inputs/fixtures/prototypes/gestao-contas")
DEFAULT_DIRETORIO_SAIDA = Path("outputs")
```

## Comandos Principais

Use a virtualenv do projeto:

```bash
python src/parser.py --help
```
### 1. Comparar Com Gemini

Executa a comparação semântica usando Gemini:

```bash
python src/parser.py comparar
```

### 2. Extrair Um Protótipo

Extrai telas e fluxos de um `.docx` e imprime o JSON no terminal:

```bash
python src/parser.py extrair prototypes/gestao-contas/Prototipo.docx
```

Salvar a extração em `outputs/`:

```bash
python src/parser.py extrair prototypes/gestao-contas/Prototipo.docx -o outputs/gabarito_gestao_contas.json
```

Sem informar arquivo, usa o gabarito padrão:

```bash
python src/parser.py extrair
```

### 3. Comparar Sem Gemini

Executa a comparação determinística, sem usar API:

```bash
.venv/bin/python src/parser.py comparar-deterministico
```

Esse comando compara:

```text
prototypes/gestao-contas/Prototipo.docx
```

com todos os `.docx` em:

```text
inputs/fixtures/prototypes/gestao-contas
```

Como `-o` não foi informado, será gerado um arquivo por aluno em `outputs/`.

Para salvar todos os resultados em um único JSON:

```bash
  python src/parser.py comparar-deterministico \
  prototypes/gestao-contas/Prototipo.docx \
  inputs/fixtures/prototypes/gestao-contas \
  -o outputs/comparacoes_gestao_deterministicas.json
```

Exemplo com outro cenário:

```bash
  python src/parser.py comparar-deterministico \
  prototypes/sistema-mercado/Prototipo.docx \
  inputs/fixtures/prototypes/sistema-mercado \
  -o outputs/comparacoes_mercado_deterministicas.json
```


Por padrão, esse comando usa o gabarito e a pasta de alunos de `gestao-contas`, e grava um arquivo por aluno em `outputs/`.

Para informar cenário e saída única:

```bash
  python src/parser.py comparar \
  prototypes/sistema-mercado/Prototipo.docx \
  inputs/fixtures/prototypes/sistema-mercado \
  -o outputs/comparacoes_mercado_gemini.json
```

Ajustar timeout e retentativas:

```bash
  python src/parser.py comparar \
  prototypes/sistema-mercado/Prototipo.docx \
  inputs/fixtures/prototypes/sistema-mercado \
  --timeout 180 \
  --tentativas 4 \
  --retry-delay 8
```

## Fluxo De Execução

```text
DOCX do gabarito
  -> extração determinística
  -> JSON estruturado do gabarito

DOCX do aluno
  -> extração determinística
  -> JSON estruturado do aluno

JSON gabarito + JSON aluno
  -> comparação determinística
  -> avaliação semântica opcional com Gemini
  -> relatório em outputs/
```

Importante: o Gemini não lê o `.docx` diretamente. A extração do documento é feita pelo código do projeto. O Gemini recebe os JSONs extraídos e a comparação determinística inicial.

## O Que É Extraído

Dos protótipos de tela:

- telas;
- campos;
- obrigatoriedade;
- validações;
- exemplos;
- opções de seleção;
- ações/comandos;
- tabelas e colunas.

Dos fluxos:

- fluxo principal;
- fluxos alternativos;
- pré-condições;
- passos;
- regras de negócio.

## Como Ler O Resultado

Na comparação determinística, observe:

```json
"resumo": {
  "itensEsperados": 113,
  "itensCobertos": 106,
  "percentualCobertura": 93.81
}
```

Na comparação com Gemini, observe:

```json
"avaliacaoGemini": {
  "nota": 8.5,
  "percentual_cobertura_semantica": 85,
  "veredito": "...",
  "equivalencias_aceitas": [],
  "itens_faltantes": [],
  "problemas_de_fluxo": [],
  "feedback": "..."
}
```

## Estrutura Do Código

```text
src/
  parser.py                         # ponto de entrada da CLI
  corrige_engsoftw/
    artifacts.py                    # carrega .docx ou .json
    cli.py                          # comandos e caminhos padrão
    comparator.py                   # comparação determinística
    docx_reader.py                  # leitura de blocos e células do DOCX
    extractor.py                    # coordena a extração completa
    flow_parser.py                  # extrai fluxos e passos
    gemini_comparator.py            # avaliação semântica com Gemini
    models.py                       # estruturas de dados
    patterns.py                     # expressões regulares
    screen_parser.py                # extrai telas, campos, ações e tabelas
    text_utils.py                   # normalização e similaridade textual
```

## Fluxo Recomendado De Correção

1. Coloque o gabarito em `prototypes/<cenario>/Prototipo.docx`.
2. Coloque os protótipos dos alunos em `inputs/fixtures/prototypes/<cenario>/`.
3. Rode `extrair` no gabarito e confira se o JSON extraído está correto.
4. Rode `comparar-deterministico` para obter uma visão rápida.
5. Rode `comparar` para obter a avaliação semântica com Gemini.
6. Revise os arquivos gerados em `outputs/`.
