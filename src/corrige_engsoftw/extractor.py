from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from .docx_reader import iter_blocos
from .flow_parser import eh_regra, extrair_fluxo_de_tabela, quebrar_sentencas
from .models import Fluxo, Tela, Passo
from .patterns import RE_ATOR, RE_FLUXO_ALTERNATIVO, RE_FLUXO_PRINCIPAL, RE_PRECONDICOES
from .screen_parser import extrair_telas_de_tabela
from .text_utils import limpar_texto


def parse_docx(caminho: str | Path) -> dict[str, Any]:
    documento = Document(str(caminho))
    telas: list[Tela] = []
    fluxos: list[Fluxo] = []
    fluxo_pendente: str | None = None
    fluxo_principal: Fluxo | None = None
    fluxo_atual: Fluxo | None = None
    secao_fluxo: str | None = None

    for bloco in iter_blocos(documento):
        if isinstance(bloco, Paragraph):
            texto = limpar_texto(bloco.text)
            if not texto:
                continue

            if RE_PRECONDICOES.match(texto):
                secao_fluxo = "precondicoes"
                continue
            if RE_FLUXO_PRINCIPAL.match(texto):
                fluxo_principal = Fluxo(nome="Fluxo principal")
                fluxos.append(fluxo_principal)
                fluxo_atual = fluxo_principal
                fluxo_pendente = "Fluxo principal"
                secao_fluxo = "passos"
                continue
            match_alt = RE_FLUXO_ALTERNATIVO.match(texto)
            if match_alt:
                fluxo_atual = Fluxo(nome=f"Fluxo alternativo {limpar_texto(match_alt.group(1))}")
                fluxos.append(fluxo_atual)
                fluxo_pendente = fluxo_atual.nome
                secao_fluxo = None
                continue
            if chave_secao := texto.casefold():
                if chave_secao == "passos":
                    secao_fluxo = "passos"
                    continue

            if fluxo_pendente == "Fluxo principal" and fluxo_principal:
                if eh_regra(texto):
                    fluxo_principal.regrasNegocio.append(texto)
                elif RE_ATOR.search(texto):
                    fluxo_principal.passos.append(Passo(len(fluxo_principal.passos) + 1, texto))
            elif fluxo_atual and fluxo_pendente and fluxo_pendente != "Fluxo principal":
                sentencas = quebrar_sentencas(texto)
                if secao_fluxo == "precondicoes":
                    fluxo_atual.precondicoes.extend(sentencas)
                else:
                    secao_fluxo = "passos"
                    for sentenca in sentencas:
                        if eh_regra(sentenca):
                            fluxo_atual.regrasNegocio.append(sentenca)
                        elif RE_ATOR.search(sentenca):
                            fluxo_atual.passos.append(Passo(len(fluxo_atual.passos) + 1, sentenca))

        elif isinstance(bloco, Table):
            if fluxo_pendente and fluxo_pendente != "Fluxo principal":
                fluxo = extrair_fluxo_de_tabela(fluxo_pendente, bloco)
                if fluxo.precondicoes or fluxo.passos or fluxo.regrasNegocio:
                    if fluxo_atual and fluxo_atual.nome == fluxo.nome and not (
                        fluxo_atual.precondicoes or fluxo_atual.passos or fluxo_atual.regrasNegocio
                    ):
                        fluxos[-1] = fluxo
                    else:
                        fluxos.append(fluxo)
                    fluxo_atual = fluxo
                    fluxo_pendente = None
                    continue

            novas_telas = extrair_telas_de_tabela(bloco)
            if novas_telas:
                telas.extend(novas_telas)
                fluxo_pendente = None
                secao_fluxo = None

    return {
        "telas": [asdict(t) for t in telas],
        "fluxos": [asdict(f) for f in fluxos],
    }
