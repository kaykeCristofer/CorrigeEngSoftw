from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .artifacts import carregar_artefato
from .comparator import comparar


DEFAULT_MODEL = "models/gemini-flash-latest"


def _json_compacto(dados: dict[str, Any]) -> str:
    return json.dumps(dados, ensure_ascii=False, separators=(",", ":"))


def montar_prompt_avaliacao(
    gabarito: dict[str, Any],
    aluno: dict[str, Any],
    comparacao_deterministica: dict[str, Any],
) -> str:
    return f"""
Atue como professor de Engenharia de Software corrigindo protótipos e descrições de fluxos.

Você receberá:
1. Um GABARITO extraído do protótipo original.
2. Um TRABALHO_ALUNO extraído do protótipo do aluno.
3. Uma COMPARACAO_DETERMINISTICA inicial, baseada em similaridade textual.

Sua tarefa é fazer uma comparação semântica rigorosa, considerando:
- nomes sinônimos ou equivalentes em campos, ações, tabelas e fluxos;
- elementos ausentes, parcialmente previstos ou inventados;
- campos obrigatórios, validações e opções quando forem relevantes;
- presença ou ausência das telas esperadas;
- explicação dos fluxos, pré-condições, passos, regras de negócio e alternativas;
- diferenças que parecem apenas renomeação aceitável;
- diferenças que alteram o comportamento esperado.

Não trate como erro uma renomeação semanticamente equivalente, por exemplo:
- "Buscar" pode equivaler a "Pesquisar";
- "Preço Unitário" pode equivaler a "Valor Unitário";
- "ID" pode equivaler a "Código" se representar o mesmo identificador do item.

Retorne SOMENTE um objeto JSON válido com este formato:
{{
  "nota": 0,
  "percentual_cobertura_semantica": 0,
  "veredito": "string curta",
  "equivalencias_aceitas": [
    {{
      "esperado": "string",
      "encontrado": "string",
      "justificativa": "string"
    }}
  ],
  "itens_cobertos": ["string"],
  "itens_parciais": [
    {{
      "item": "string",
      "motivo": "string"
    }}
  ],
  "itens_faltantes": [
    {{
      "item": "string",
      "impacto": "baixo|medio|alto"
    }}
  ],
  "itens_extras_ou_inventados": [
    {{
      "item": "string",
      "impacto": "baixo|medio|alto"
    }}
  ],
  "problemas_de_fluxo": [
    {{
      "fluxo": "string",
      "problema": "string",
      "impacto": "baixo|medio|alto"
    }}
  ],
  "feedback": "texto curto e objetivo para o aluno"
}}

Use nota de 0 a 10. Seja criterioso: omitir tela, ação importante, fluxo alternativo,
confirmação administrativa ou regra de negócio relevante deve reduzir a nota.

GABARITO:
{_json_compacto(gabarito)}

TRABALHO_ALUNO:
{_json_compacto(aluno)}

COMPARACAO_DETERMINISTICA:
{_json_compacto(comparacao_deterministica)}
""".strip()


def _extrair_json(texto: str) -> dict[str, Any]:
  texto = texto.strip()
  if texto.startswith("```"):
    texto = re.sub(r"^```(?:json)?", "", texto, flags=re.I).strip()
    texto = re.sub(r"```$", "", texto).strip()
  try:
    return json.loads(texto)
  except json.JSONDecodeError:
    pass

  inicio = None
  profundidade = 0
  em_string = False
  escape = False

  for idx, ch in enumerate(texto):
    if em_string:
      if escape:
        escape = False
      elif ch == "\\":
        escape = True
      elif ch == '"':
        em_string = False
      continue

    if ch == '"':
      em_string = True
      continue

    if ch == "{":
      if profundidade == 0:
        inicio = idx
      profundidade += 1
    elif ch == "}":
      if profundidade == 0:
        continue
      profundidade -= 1
      if profundidade == 0 and inicio is not None:
        candidato = texto[inicio : idx + 1]
        try:
          return json.loads(candidato)
        except json.JSONDecodeError:
          inicio = None
          continue

  raise json.JSONDecodeError("Resposta não contém JSON válido", texto, 0)


def avaliar_com_gemini(
    gabarito: dict[str, Any],
    aluno: dict[str, Any],
    *,
    modelo: str | None = None,
    api_key: str | None = None,
    limite_deterministico: float = 0.72,
    timeout: int = 120,
    tentativas: int = 3,
    retry_delay: float = 5.0,
) -> dict[str, Any]:
    load_dotenv()
    api_key = api_key or os.getenv("GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Defina GENAI_API_KEY ou GEMINI_API_KEY no .env/ambiente para usar o Gemini.")

    # Import local para manter extração/comparação utilizáveis sem dependência da API.
    import google.generativeai as genai

    modelo = modelo or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
    comparacao_deterministica = comparar(gabarito, aluno, limite_deterministico)
    prompt = montar_prompt_avaliacao(gabarito, aluno, comparacao_deterministica)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=modelo,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
        },
    )
    response = gerar_conteudo_com_retentativas(
        model,
        prompt,
        timeout=timeout,
        tentativas=tentativas,
        retry_delay=retry_delay,
    )
    avaliacao = _extrair_json(response.text)
    return {
        "modelo": modelo,
        "comparacaoDeterministica": comparacao_deterministica,
        "avaliacaoGemini": avaliacao,
    }


def comparar_arquivo_com_gemini(
    gabarito_path: str | Path,
    aluno_path: str | Path,
    *,
    modelo: str | None = None,
    limite_deterministico: float = 0.72,
    timeout: int = 120,
    tentativas: int = 3,
    retry_delay: float = 5.0,
) -> dict[str, Any]:
    gabarito = carregar_artefato(gabarito_path)
    aluno = carregar_artefato(aluno_path)
    resultado = avaliar_com_gemini(
        gabarito,
        aluno,
        modelo=modelo,
        limite_deterministico=limite_deterministico,
        timeout=timeout,
        tentativas=tentativas,
        retry_delay=retry_delay,
    )
    return {
        "gabarito": str(gabarito_path),
        "aluno": str(aluno_path),
        **resultado,
    }


def comparar_lote_com_gemini(
    gabarito_path: str | Path,
    diretorio_alunos: str | Path,
    *,
    modelo: str | None = None,
    limite_deterministico: float = 0.72,
    timeout: int = 120,
    tentativas: int = 3,
    retry_delay: float = 5.0,
) -> dict[str, Any]:
    diretorio_alunos = Path(diretorio_alunos)
    gabarito = carregar_artefato(gabarito_path)
    resultados = []

    for aluno_path in sorted(diretorio_alunos.glob("*.docx")):
        aluno = carregar_artefato(aluno_path)
        resultado = avaliar_com_gemini(
            gabarito,
            aluno,
            modelo=modelo,
            limite_deterministico=limite_deterministico,
            timeout=timeout,
            tentativas=tentativas,
            retry_delay=retry_delay,
        )
        resultados.append({"arquivo": str(aluno_path), **resultado})

    return {
        "gabarito": str(gabarito_path),
        "diretorioAlunos": str(diretorio_alunos),
        "quantidade": len(resultados),
        "resultados": resultados,
    }


def gerar_conteudo_com_retentativas(
    model,
    prompt: str,
    *,
    timeout: int,
    tentativas: int,
    retry_delay: float,
):
    ultimo_erro: Exception | None = None

    for tentativa in range(1, max(tentativas, 1) + 1):
        try:
            return model.generate_content(prompt, request_options={"timeout": timeout})
        except Exception as exc:
            ultimo_erro = exc
            if tentativa >= max(tentativas, 1) or not erro_transitorio(exc):
                raise
            espera = retry_delay * tentativa
            time.sleep(espera)

    if ultimo_erro:
        raise ultimo_erro
    raise RuntimeError("Falha inesperada ao chamar o Gemini.")


def erro_transitorio(exc: Exception) -> bool:
    texto = str(exc).lower()
    return any(
        marcador in texto
        for marcador in (
            "504",
            "deadline",
            "timeout",
            "temporarily unavailable",
            "service unavailable",
            "rate limit",
            "resource exhausted",
        )
    )
