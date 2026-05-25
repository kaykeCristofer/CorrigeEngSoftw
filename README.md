# CorrigeEngSoftw

Projeto para apoiar a correção de trabalhos de Engenharia de Software a partir de protótipos de funcionalidades em arquivos DOCX.

A ideia central é usar um protótipo original como **gabarito** e comparar os protótipos dos alunos contra ele. O sistema extrai telas, campos, ações, tabelas e fluxos dos documentos, gera uma comparação inicial e, opcionalmente, usa o Gemini para avaliar equivalências semânticas como sinônimos e descrições semelhantes.

## Objetivo

O projeto busca responder perguntas como:

- O aluno previu as mesmas telas do gabarito?
- Os campos esperados aparecem no protótipo do aluno?
- Campos com nomes diferentes representam a mesma informação?
- As ações importantes foram previstas?
- As tabelas e colunas principais foram modeladas?
- Os fluxos principais e alternativos foram explicados?
- Regras de negócio e validações importantes foram omitidas?
- O aluno inventou elementos que não estavam no gabarito?

## Fluxo De Execução

O fluxo de comparação é dividido em três etapas.

```text
DOCX do gabarito
  -> extração determinística
  -> JSON estruturado do gabarito

DOCX do aluno
  -> extração determinística
  -> JSON estruturado do aluno

JSON gabarito + JSON aluno
  -> comparação determinística inicial
  -> comparação semântica opcional com Gemini
  -> relatório final
```

Importante: o Gemini **não faz a extração do DOCX**. A extração é feita pelo código do projeto. O Gemini atua depois, como avaliador semântico.

## O Que É Extraído

Da parte de protótipos de tela:

- telas;
- campos;
- obrigatoriedade;
- validações;
- exemplos;
- opções de seleção;
- ações/comandos;
- tabelas e colunas.

Da parte de caso de uso/fluxo:

- fluxo principal;
- fluxos alternativos;
- pré-condições;
- passos;
- regras de negócio.

## Comparação Determinística

A comparação determinística é feita sem LLM. Ela usa normalização textual e similaridade para comparar:

- tela esperada vs tela encontrada;
- campo esperado vs campo encontrado;
- ação esperada vs ação encontrada;
- tabela esperada vs tabela encontrada;
- passo esperado vs passo encontrado;
- regra esperada vs regra encontrada.

Ela gera uma primeira visão de:

- itens cobertos;
- itens faltantes;
- itens extras;
- percentual de cobertura.

Essa etapa é rápida, reprodutível e não depende de internet ou API.

## Comparação Com Gemini

A comparação com Gemini recebe:

1. JSON extraído do gabarito;
2. JSON extraído do protótipo do aluno;
3. comparação determinística inicial.

Com isso, o Gemini avalia aspectos semânticos que uma comparação textual simples pode errar, por exemplo:

- `Buscar` pode equivaler a `Pesquisar`;
- `Preço Unitário` pode equivaler a `Valor Unitário`;
- `ID` pode equivaler a `Código`, dependendo do contexto;
- um fluxo pode estar parcialmente descrito mesmo com texto diferente;
- uma regra de negócio pode ter sido omitida mesmo que a tela exista.

O retorno esperado da avaliação semântica inclui:

- nota;
- percentual de cobertura semântica;
- equivalências aceitas;
- itens cobertos;
- itens parciais;
- itens faltantes;
- itens extras ou inventados;
- problemas de fluxo;
- feedback textual para o aluno.

## Estrutura Do Projeto

```text
.
├── prototypes/
│   └── gestao-contas/
│       └── Prototipo.docx
├── tests/
│   └── fixtures/
│       └── prototypes/
│           ├── Prototipo_teste1.docx
│           └── Prototipo_teste2.docx
├── outputs/
│   ├── resultado.json
│   ├── comparacoes_deterministicas.json
│   ├── comparacao_gemini_teste1.json
│   └── comparacao_gemini_teste2.json
├── notebooks/
│   └── CorrigeTrabalhos.ipynb
└── src/
    └── parser.py
```

## Organização Do Código

Nesta branch, a implementação está concentrada em `src/parser.py`.

O arquivo único reúne:

- estruturas de dados do domínio;
- expressões regulares e palavras-chave;
- leitura do DOCX;
- extração de telas, campos, ações, tabelas e fluxos;
- comparação determinística;
- comparação semântica com Gemini;
- interface de linha de comando.

## Configuração

Crie ou ajuste o arquivo `.env` na raiz do projeto:

```env
GENAI_API_KEY=sua_chave_do_gemini
GEMINI_MODEL=models/gemini-flash-latest
```

Também é aceito:

```env
GEMINI_API_KEY=sua_chave_do_gemini
```

Se o Gemini retornar erro de chave inválida, gere uma nova chave válida no Google AI Studio e atualize o `.env`.

## Comandos Principais

### Extrair Um Protótipo

```bash
.venv/bin/python src/parser.py extrair prototypes/gestao-contas/Prototipo.docx
```

Salvar em JSON:

```bash
.venv/bin/python src/parser.py extrair prototypes/gestao-contas/Prototipo.docx -o outputs/gabarito_extraido.json
```

### Comparar Um Aluno Sem Gemini

```bash
.venv/bin/python src/parser.py comparar prototypes/gestao-contas/Prototipo.docx tests/fixtures/prototypes/Prototipo_teste1.docx
```

Salvar em JSON:

```bash
.venv/bin/python src/parser.py comparar prototypes/gestao-contas/Prototipo.docx tests/fixtures/prototypes/Prototipo_teste1.docx -o outputs/comparacao_deterministica_teste1.json
```

### Comparar Todos Os Protótipos De Teste Sem Gemini

```bash
.venv/bin/python src/parser.py comparar-lote prototypes/gestao-contas/Prototipo.docx tests/fixtures/prototypes -o outputs/comparacoes_deterministicas.json
```

### Comparar Um Aluno Com Gemini

```bash
.venv/bin/python src/parser.py comparar-gemini prototypes/gestao-contas/Prototipo.docx tests/fixtures/prototypes/Prototipo_teste1.docx -o outputs/comparacao_gemini_teste1.json
```

### Comparar Todos Os Protótipos De Teste Com Gemini

```bash
.venv/bin/python src/parser.py comparar-lote-gemini prototypes/gestao-contas/Prototipo.docx tests/fixtures/prototypes -o outputs/comparacoes_gemini.json
```

### Ajustar Timeout Da API

```bash
.venv/bin/python src/parser.py comparar-gemini prototypes/gestao-contas/Prototipo.docx tests/fixtures/prototypes/Prototipo_teste1.docx --timeout 180 -o outputs/comparacao_gemini_teste1.json
```

### Ajustar Retentativas Da API

Erros como `504 Deadline expired` costumam ser transitórios. O comando com Gemini já tenta novamente por padrão, mas você pode aumentar as tentativas:

```bash
.venv/bin/python src/parser.py comparar-gemini prototypes/sistema-mercado/Prototipo.docx tests/fixtures/prototypes/Prototipo_mercado_teste.docx --timeout 180 --tentativas 4 --retry-delay 8 -o outputs/comparacao_gemini_teste_mercado.json
```

## Como Ler O Resultado

Na comparação determinística, procure:

```json
"resumo": {
  "itensEsperados": 113,
  "itensCobertos": 106,
  "percentualCobertura": 93.81
}
```

Na comparação com Gemini, procure:

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

## Limitações Atuais

- A extração é determinística e depende de padrões no DOCX, como tabelas, títulos de telas e seções de fluxo.
- Protótipos desenhados apenas como imagem não são interpretados.
- A comparação determinística não entende todos os sinônimos; por isso existe a etapa com Gemini.
- A etapa com Gemini depende de chave válida, internet e disponibilidade da API.
- A resposta da LLM deve ser revisada quando usada para nota final, especialmente em avaliações oficiais.

## Fluxo Recomendado De Correção

1. Use o protótipo original como gabarito.
2. Rode a extração e verifique se o JSON do gabarito está correto.
3. Rode a comparação determinística em lote para obter uma visão rápida.
4. Rode a comparação com Gemini para obter avaliação semântica.
5. Revise os casos com nota baixa ou divergências importantes.
6. Use o feedback gerado como apoio, não como substituto completo do julgamento do professor.
