from __future__ import annotations

import re

from docx.table import Table

from .docx_reader import celulas_linha
from .models import Acao, Campo, Tabela, Tela
from .patterns import (
    COLUNAS_PROVAVEIS,
    RE_ACAO,
    RE_EXEMPLO,
    RE_OBRIGATORIO,
    RE_OPCOES,
    RE_SECAO,
    RE_TELA,
    RE_VALIDACAO,
)
from .text_utils import chave, deduplicar, limpar_texto


def parece_titulo_tela(texto: str) -> bool:
    return bool(RE_TELA.match(texto))


def parece_cabecalho_tabela(celulas: list[str]) -> bool:
    if len(celulas) < 2:
        return False
    colunas = {chave(x) for x in COLUNAS_PROVAVEIS}
    conhecidas = sum(1 for c in celulas if chave(c) in colunas)
    return conhecidas >= 2


def extrair_opcoes(texto: str) -> list[str]:
    match = RE_OPCOES.search(texto)
    if not match:
        return []
    return [limpar_texto(p) for p in re.split(r";|,", match.group(1)) if limpar_texto(p)]


def montar_campo(nome_bruto: str, valor: str) -> Campo | None:
    nome = limpar_texto(RE_OBRIGATORIO.sub("", nome_bruto).replace("*", ""))
    if not nome or RE_SECAO.match(nome) or RE_EXEMPLO.match(nome) or RE_ACAO.search(nome):
        return None

    validacao = None
    match_validacao = RE_VALIDACAO.search(valor)
    if match_validacao:
        validacao = limpar_texto(match_validacao.group(1))

    exemplo = RE_VALIDACAO.sub("", RE_OPCOES.sub("", RE_ACAO.sub("", valor)))
    exemplo = limpar_texto(exemplo) or None

    return Campo(
        nome=nome,
        obrigatorio=bool(RE_OBRIGATORIO.search(nome_bruto) or "*" in nome_bruto),
        validacao=validacao,
        exemplo=exemplo,
        opcoes=extrair_opcoes(valor),
    )


def extrair_telas_de_tabela(tabela: Table) -> list[Tela]:
    telas: list[Tela] = []
    tela_atual: Tela | None = None
    tabela_atual: Tabela | None = None
    lendo_dados = False

    for linha in tabela.rows:
        celulas = [c for c in celulas_linha(linha) if c]
        if not celulas:
            continue

        primeira = celulas[0]
        texto_linha = " ".join(celulas)

        if len(celulas) == 1 and parece_titulo_tela(primeira):
            tela_atual = Tela(nome=primeira)
            telas.append(tela_atual)
            tabela_atual = None
            lendo_dados = False
            continue

        if tela_atual is None:
            continue

        if len(celulas) == 1:
            for acao in RE_ACAO.findall(primeira):
                tela_atual.acoes.append(Acao(limpar_texto(acao)))

            if chave(primeira).startswith(("tabela de", "itens na conta", "pagamentos")):
                tabela_atual = Tabela(nome=primeira)
                tela_atual.tabelas.append(tabela_atual)
                lendo_dados = True
            elif RE_SECAO.match(primeira) or RE_ACAO.search(primeira):
                lendo_dados = False
                tabela_atual = None
            continue

        if parece_cabecalho_tabela(celulas):
            if tabela_atual is not None:
                tabela_atual.colunas = [limpar_texto(c) for c in celulas if c]
            lendo_dados = True
            continue

        for acao in RE_ACAO.findall(texto_linha):
            tela_atual.acoes.append(Acao(limpar_texto(acao)))

        if lendo_dados:
            continue

        campo = montar_campo(primeira, celulas[1] if len(celulas) > 1 else "")
        if campo:
            tela_atual.campos.append(campo)

    for tela in telas:
        tela.campos = deduplicar(tela.campos, "nome")
        tela.acoes = deduplicar(tela.acoes, "nome")
        tela.tabelas = deduplicar(tela.tabelas, "nome")
    return telas
