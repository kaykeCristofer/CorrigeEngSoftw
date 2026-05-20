from __future__ import annotations

import re

from docx.table import Table

from .docx_reader import celulas_linha
from .models import Fluxo, Passo
from .patterns import PALAVRAS_REGRA, RE_ATOR
from .text_utils import chave, limpar_texto


def eh_regra(texto: str) -> bool:
    c = chave(texto)
    return any(chave(p) in c for p in PALAVRAS_REGRA)


def quebrar_sentencas(texto: str) -> list[str]:
    texto = limpar_texto(texto.replace("*", ""))
    partes = re.split(r"(?<=[.!?])\s+|(?=\bO\s+(?:Sistema|Atendente|Administrador|Operador)\b)", texto, flags=re.I)
    return [limpar_texto(p).rstrip(".") for p in partes if limpar_texto(p).rstrip(".")]


def extrair_fluxo_de_tabela(nome: str, tabela: Table) -> Fluxo:
    fluxo = Fluxo(nome=nome)

    for linha in tabela.rows:
        celulas = celulas_linha(linha)
        if len(celulas) < 2:
            continue

        rotulo = chave(celulas[0])
        valor = celulas[1]
        if "precondi" in rotulo:
            fluxo.precondicoes.extend(quebrar_sentencas(valor))
        elif "passo" in rotulo:
            for sentenca in quebrar_sentencas(valor):
                if eh_regra(sentenca):
                    fluxo.regrasNegocio.append(sentenca)
                elif RE_ATOR.search(sentenca):
                    fluxo.passos.append(Passo(len(fluxo.passos) + 1, sentenca))

    return fluxo
