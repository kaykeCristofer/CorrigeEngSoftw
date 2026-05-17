from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from .docx_reader import iter_blocos
from .flow_parser import eh_regra, extrair_fluxo_de_tabela
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

    for bloco in iter_blocos(documento):
        if isinstance(bloco, Paragraph):
            texto = limpar_texto(bloco.text)
            if not texto:
                continue

            if RE_PRECONDICOES.match(texto):
                continue
            if RE_FLUXO_PRINCIPAL.match(texto):
                fluxo_principal = Fluxo(nome="Fluxo principal")
                fluxos.append(fluxo_principal)
                fluxo_pendente = "Fluxo principal"
                continue
            match_alt = RE_FLUXO_ALTERNATIVO.match(texto)
            if match_alt:
                fluxo_pendente = f"Fluxo alternativo {limpar_texto(match_alt.group(1))}"
                continue

            if fluxo_pendente == "Fluxo principal" and fluxo_principal:
                if eh_regra(texto):
                    fluxo_principal.regrasNegocio.append(texto)
                elif RE_ATOR.search(texto):
                    fluxo_principal.passos.append(Passo(len(fluxo_principal.passos) + 1, texto))

        elif isinstance(bloco, Table):
            if fluxo_pendente and fluxo_pendente != "Fluxo principal":
                fluxo = extrair_fluxo_de_tabela(fluxo_pendente, bloco)
                if fluxo.precondicoes or fluxo.passos or fluxo.regrasNegocio:
                    fluxos.append(fluxo)
                    fluxo_pendente = None
                    continue

            novas_telas = extrair_telas_de_tabela(bloco)
            if novas_telas:
                telas.extend(novas_telas)
                fluxo_pendente = None

    return {
        "telas": [asdict(t) for t in telas],
        "fluxos": [asdict(f) for f in fluxos],
    }
