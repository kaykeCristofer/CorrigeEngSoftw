from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import carregar_artefato
from .text_utils import similaridade


def nomes_de(colecao: list[dict[str, Any]], campo: str = "nome") -> list[str]:
    return [str(item.get(campo, "")) for item in colecao if item.get(campo)]


def similaridade_conjuntos(esperados: list[str], encontrados: list[str]) -> float:
    if not esperados and not encontrados:
        return 1.0
    if not esperados or not encontrados:
        return 0.0

    total = 0.0
    for esperado in esperados:
        total += max(similaridade(esperado, encontrado) for encontrado in encontrados)
    return total / len(esperados)


def score_tela(esperada: dict[str, Any], encontrada: dict[str, Any]) -> float:
    nome = similaridade(esperada.get("nome", ""), encontrada.get("nome", ""))
    campos = similaridade_conjuntos(nomes_de(esperada.get("campos", [])), nomes_de(encontrada.get("campos", [])))
    acoes = similaridade_conjuntos(nomes_de(esperada.get("acoes", [])), nomes_de(encontrada.get("acoes", [])))
    tabelas = similaridade_conjuntos(nomes_de(esperada.get("tabelas", [])), nomes_de(encontrada.get("tabelas", [])))
    return (nome * 0.35) + (campos * 0.35) + (acoes * 0.15) + (tabelas * 0.15)


def score_fluxo(esperado: dict[str, Any], encontrado: dict[str, Any]) -> float:
    nome = similaridade(esperado.get("nome", ""), encontrado.get("nome", ""))
    passos = similaridade_conjuntos(
        nomes_de(esperado.get("passos", []), "descricao"),
        nomes_de(encontrado.get("passos", []), "descricao"),
    )
    regras = similaridade_conjuntos(
        [str(r) for r in esperado.get("regrasNegocio", [])],
        [str(r) for r in encontrado.get("regrasNegocio", [])],
    )
    return (nome * 0.45) + (passos * 0.4) + (regras * 0.15)


def melhor_match(nome: str, candidatos: list[dict[str, Any]], limite: float) -> tuple[dict[str, Any] | None, float]:
    melhor = None
    nota = 0.0
    for candidato in candidatos:
        atual = similaridade(nome, candidato.get("nome", ""))
        if atual > nota:
            melhor = candidato
            nota = atual
    return (melhor, nota) if nota >= limite else (None, nota)


def parear_por_score(
    esperados: list[dict[str, Any]],
    encontrados: list[dict[str, Any]],
    score_fn,
    limite: float,
) -> list[tuple[dict[str, Any], dict[str, Any] | None, float]]:
    candidatos = []
    for indice_esperado, esperado in enumerate(esperados):
        for indice_encontrado, encontrado in enumerate(encontrados):
            candidatos.append((score_fn(esperado, encontrado), indice_esperado, indice_encontrado))

    candidatos.sort(reverse=True, key=lambda item: item[0])
    pares_por_esperado: dict[int, tuple[dict[str, Any], dict[str, Any], float]] = {}
    esperados_usados: set[int] = set()
    encontrados_usados: set[int] = set()

    for score, indice_esperado, indice_encontrado in candidatos:
        if score < limite:
            break
        if indice_esperado in esperados_usados or indice_encontrado in encontrados_usados:
            continue
        esperados_usados.add(indice_esperado)
        encontrados_usados.add(indice_encontrado)
        pares_por_esperado[indice_esperado] = (esperados[indice_esperado], encontrados[indice_encontrado], score)

    pares = []
    for indice_esperado, esperado in enumerate(esperados):
        if indice_esperado in pares_por_esperado:
            pares.append(pares_por_esperado[indice_esperado])
        else:
            melhor_score = max((score_fn(esperado, encontrado) for encontrado in encontrados), default=0.0)
            pares.append((esperado, None, melhor_score))

    return pares


def comparar_lista(
    esperados: list[dict[str, Any]],
    encontrados: list[dict[str, Any]],
    tipo: str,
    limite: float,
) -> dict[str, Any]:
    cobertos = []
    faltantes = []
    usados: set[int] = set()

    for esperado in esperados:
        candidatos = [e for i, e in enumerate(encontrados) if i not in usados]
        achado, score = melhor_match(esperado.get("nome", ""), candidatos, limite)
        if achado:
            indice_real = encontrados.index(achado)
            usados.add(indice_real)
            cobertos.append(
                {
                    "esperado": esperado.get("nome"),
                    "encontrado": achado.get("nome"),
                    "similaridade": round(score, 3),
                }
            )
        else:
            faltantes.append({"tipo": tipo, "nome": esperado.get("nome"), "similaridade_maxima": round(score, 3)})

    extras = [
        {"tipo": tipo, "nome": item.get("nome")}
        for i, item in enumerate(encontrados)
        if i not in usados
    ]
    return {"cobertos": cobertos, "faltantes": faltantes, "extras": extras}


def comparar_passos(esperados: list[dict[str, Any]], encontrados: list[dict[str, Any]], limite: float) -> dict[str, Any]:
    exp = [{"nome": p.get("descricao", "")} for p in esperados]
    enc = [{"nome": p.get("descricao", "")} for p in encontrados]
    return comparar_lista(exp, enc, "passo", limite)


def comparar(gabarito: dict[str, Any], aluno: dict[str, Any], limite: float = 0.72) -> dict[str, Any]:
    relatorio: dict[str, Any] = {
        "limiteSimilaridade": limite,
        "telas": [],
        "fluxos": [],
        "resumo": {},
    }

    total = 0
    cobertos = 0

    telas_aluno = aluno.get("telas", [])
    for tela_ref, tela_aluno, score in parear_por_score(gabarito.get("telas", []), telas_aluno, score_tela, min(limite, 0.35)):
        item = {
            "telaEsperada": tela_ref.get("nome"),
            "telaEncontrada": tela_aluno.get("nome") if tela_aluno else None,
            "similaridade": round(score, 3),
            "campos": {"cobertos": [], "faltantes": [], "extras": []},
            "acoes": {"cobertos": [], "faltantes": [], "extras": []},
            "tabelas": {"cobertos": [], "faltantes": [], "extras": []},
        }
        total += 1
        if tela_aluno:
            cobertos += 1
            for chave_item, tipo in (("campos", "campo"), ("acoes", "ação"), ("tabelas", "tabela")):
                comparacao = comparar_lista(tela_ref.get(chave_item, []), tela_aluno.get(chave_item, []), tipo, limite)
                item[chave_item] = comparacao
                total += len(tela_ref.get(chave_item, []))
                cobertos += len(comparacao["cobertos"])
        else:
            item["faltante"] = True
            total += len(tela_ref.get("campos", [])) + len(tela_ref.get("acoes", [])) + len(tela_ref.get("tabelas", []))
        relatorio["telas"].append(item)

    fluxos_aluno = aluno.get("fluxos", [])
    for fluxo_ref, fluxo_aluno, score in parear_por_score(gabarito.get("fluxos", []), fluxos_aluno, score_fluxo, min(limite, 0.35)):
        item = {
            "fluxoEsperado": fluxo_ref.get("nome"),
            "fluxoEncontrado": fluxo_aluno.get("nome") if fluxo_aluno else None,
            "similaridade": round(score, 3),
            "passos": {"cobertos": [], "faltantes": [], "extras": []},
            "regrasNegocio": {"cobertos": [], "faltantes": [], "extras": []},
        }
        total += 1
        if fluxo_aluno:
            cobertos += 1
            passos = comparar_passos(fluxo_ref.get("passos", []), fluxo_aluno.get("passos", []), limite)
            regras = comparar_lista(
                [{"nome": r} for r in fluxo_ref.get("regrasNegocio", [])],
                [{"nome": r} for r in fluxo_aluno.get("regrasNegocio", [])],
                "regra de negócio",
                limite,
            )
            item["passos"] = passos
            item["regrasNegocio"] = regras
            total += len(fluxo_ref.get("passos", [])) + len(fluxo_ref.get("regrasNegocio", []))
            cobertos += len(passos["cobertos"]) + len(regras["cobertos"])
        else:
            item["faltante"] = True
            total += len(fluxo_ref.get("passos", [])) + len(fluxo_ref.get("regrasNegocio", []))
        relatorio["fluxos"].append(item)

    relatorio["resumo"] = {
        "itensEsperados": total,
        "itensCobertos": cobertos,
        "percentualCobertura": round((cobertos / total) * 100, 2) if total else 0,
    }
    return relatorio


def comparar_lote(gabarito_path: str | Path, diretorio_alunos: str | Path, limite: float = 0.72) -> dict[str, Any]:
    diretorio_alunos = Path(diretorio_alunos)
    gabarito = carregar_artefato(gabarito_path)
    resultados = []

    for aluno_path in sorted(diretorio_alunos.glob("*.docx")):
        aluno = carregar_artefato(aluno_path)
        resultados.append(
            {
                "arquivo": str(aluno_path),
                "comparacao": comparar(gabarito, aluno, limite),
            }
        )

    return {
        "gabarito": str(gabarito_path),
        "diretorioAlunos": str(diretorio_alunos),
        "quantidade": len(resultados),
        "resultados": resultados,
    }
