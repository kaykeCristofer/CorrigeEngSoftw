from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from dotenv import load_dotenv


DEFAULT_MODEL = "models/gemini-flash-latest"

SINONIMOS_DOMINIO = {
    "comandas": "contas",
    "comanda": "conta",
    "documento do cliente": "cpf",
    "documento": "cpf",
    "cliente": "nome",
    "contato": "celular",
    "codigo interno": "numero",
    "codigo da conta": "numero",
    "codigo da comanda": "numero",
    "codigo": "numero",
    "situacao": "aberta",
    "ativa": "sim",
    "finalizada": "nao",
    "abertura": "data",
    "horario": "hora",
    "qtde": "quantidade",
    "preco unitario": "valor unitario",
    "preco": "valor",
    "produto": "item",
    "produtos": "itens",
    "vinculados": "na conta",
    "localizacao": "registro",
    "painel": "tela",
    "manutencao": "edicao",
    "gerenciamento": "registro",
    "inclusao": "lancamento",
    "insercao": "lancamento",
    "finalizacao": "fechamento",
    "encerramento": "fechamento",
    "encerrar": "fechar",
    "finalizar atendimento": "concluir fechamento",
    "gravar": "salvar",
    "buscar": "pesquisar",
    "detalhar": "visualizar",
    "editar": "alterar",
    "cancelar": "excluir",
    "adicionar": "inserir",
    "remover": "excluir",
    "autorizar": "confirmar",
    "login admin": "usuario",
    "login": "usuario",
    "senha admin": "senha",
    "operador": "atendente",
    "sku": "codigo",
    "mercadorias": "itens",
    "mercadoria": "item",
    "aquisicoes": "compras",
    "aquisicao": "compra",
    "pedido": "compra",
    "pedidos": "compras",
    "solicitacao": "compra",
    "distribuidor": "fornecedor",
    "distribuidores": "fornecedores",
    "empresa fornecedora": "nome fornecedor",
    "unidade comercial": "unidade",
    "ultimo valor": "preco de compra",
    "valor negociado": "preco unitario",
    "valor atualizado": "preco unitario",
    "volume solicitado": "quantidade comprada",
    "quantidade atual": "quantidade",
    "estoque atual": "quantidade",
    "limite minimo": "minimo",
    "estoque critico": "minimo",
    "comentarios": "observacao",
    "retornar": "voltar",
    "consultar": "pesquisar",
    "ver historico": "ultimas compras",
    "refazer": "repetir",
    "registrar pedido": "salvar",
    "confirmar pedido": "confirmar compra",
    "registrar transporte": "registrar envio",
    "finalizar recebimento": "receber compra",
}

RE_ACAO = re.compile(r"<\s*([^<>]+?)\s*>")
RE_OPCOES = re.compile(r"\[([^\]]+)\]")
RE_VALIDACAO = re.compile(r"\(([^)]+)\)")
RE_OBRIGATORIO = re.compile(r"\*\s*$")
RE_FLUXO_PRINCIPAL = re.compile(r"^fluxo\s+principal(?:\s+.+)?$", re.I)
RE_FLUXO_ALTERNATIVO = re.compile(r"^fluxo\s+alternativo\s+(.+)$", re.I)
RE_PRECONDICOES = re.compile(r"^pr[eé]-?condi[cç](?:[aã]o|[oõ]es|ões)$", re.I)
RE_TELA = re.compile(
    r"^(tela\s+(de\s+)?|registro\s+de\s+|edi[cç][aã]o\s+(de\s+)?|"
    r"fechamento\s+(de\s+)?|confirma[cç][aã]o\s+)",
    re.I,
)
RE_SECAO = re.compile(
    r"^(pesquisa\s+por|tabela\s+de|itens\s+na\s+conta|pagamentos|confirma[cç][aã]o\s+)",
    re.I,
)
RE_EXEMPLO = re.compile(
    r"^(\d{3}\.\d{3}\.\d{3}-\d{2}|R\$|[\d]+[,\.]\d+|\d{2}/\d{2}/\d{4}|\d{2}:\d{2})"
)
RE_ATOR = re.compile(r"\b(O|A)\s+(Sistema|Atendente|Administrador|Usu[aá]rio|Cliente|Operador|Estoquista)\b", re.I)

COLUNAS_PROVAVEIS = {
    "cpf",
    "nome",
    "celular",
    "numero",
    "número",
    "aberta?",
    "comandos",
    "código",
    "codigo",
    "descrição",
    "descricao",
    "quantidade",
    "valor",
    "forma",
    "documento",
    "cliente",
    "situação",
    "situacao",
    "opções",
    "opcoes",
    "produto",
    "id",
    "contato",
    "tipo",
}
PALAVRAS_REGRA = (
    "verifica",
    "valida",
    "confere",
    "impede",
    "não existe",
    "nao existe",
    "não há",
    "nao ha",
    "emite mensagem",
    "qualquer outro caso",
    "caso exista",
    "caso contrário",
    "caso contrario",
    "bloqueia",
)


@dataclass
class Campo:
    nome: str
    obrigatorio: bool = False
    validacao: str | None = None
    exemplo: str | None = None
    opcoes: list[str] = field(default_factory=list)


@dataclass
class Acao:
    nome: str


@dataclass
class Tabela:
    nome: str
    colunas: list[str] = field(default_factory=list)


@dataclass
class Tela:
    nome: str
    campos: list[Campo] = field(default_factory=list)
    acoes: list[Acao] = field(default_factory=list)
    tabelas: list[Tabela] = field(default_factory=list)


@dataclass
class Passo:
    ordem: int
    descricao: str


@dataclass
class Fluxo:
    nome: str
    precondicoes: list[str] = field(default_factory=list)
    passos: list[Passo] = field(default_factory=list)
    regrasNegocio: list[str] = field(default_factory=list)


def limpar_texto(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto.replace("\xa0", " ")).strip()
    texto = re.sub(r"\s+([,.?;:])", r"\1", texto)
    return texto


def chave(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    texto = limpar_texto(texto)
    for origem, destino in sorted(SINONIMOS_DOMINIO.items(), key=lambda item: len(item[0]), reverse=True):
        texto = re.sub(rf"\b{re.escape(origem)}\b", destino, texto)
    return limpar_texto(texto)


def similaridade(a: str, b: str) -> float:
    ca, cb = chave(a), chave(b)
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0
    if ca in cb or cb in ca:
        return 0.9
    return SequenceMatcher(None, ca, cb).ratio()


def deduplicar(items: list[Any], attr: str) -> list[Any]:
    vistos: set[str] = set()
    saida = []
    for item in items:
        valor = chave(getattr(item, attr))
        if valor not in vistos:
            vistos.add(valor)
            saida.append(item)
    return saida


def texto_celula(celula) -> str:
    return limpar_texto(" ".join(p.text for p in celula.paragraphs if p.text.strip()))


def celulas_linha(linha) -> list[str]:
    celulas: list[str] = []
    anterior = None
    for celula in linha.cells:
        texto = texto_celula(celula)
        if texto != anterior:
            celulas.append(texto)
        anterior = texto
    return celulas


def iter_blocos(documento: Document) -> Iterable[Paragraph | Table]:
    for child in documento.element.body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, documento)
        elif tag == "tbl":
            yield Table(child, documento)


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
    nome_bruto = nome_bruto.strip().lstrip("|").strip()
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


def extrair_telas_de_tabela(tabela: Table, titulo_inicial: str | None = None) -> list[Tela]:
    telas: list[Tela] = []
    tela_atual: Tela | None = None
    tabela_atual: Tabela | None = None
    tabela_pendente: str | None = None
    lendo_dados = False

    for indice_linha, linha in enumerate(tabela.rows):
        celulas = [c for c in celulas_linha(linha) if c]
        if not celulas:
            continue

        primeira = celulas[0]
        texto_linha = " ".join(celulas)

        primeira_eh_titulo_generico = indice_linha == 0 and chave(primeira) in {"campo", "campos", "dados"}
        primeira_linha_parece_titulo = indice_linha == 0 and not RE_ACAO.search(primeira)

        if len(celulas) == 1 and (parece_titulo_tela(primeira) or primeira_linha_parece_titulo):
            nome_tela = titulo_inicial if primeira_eh_titulo_generico and titulo_inicial else primeira
            tela_atual = Tela(nome=nome_tela)
            telas.append(tela_atual)
            tabela_atual = None
            tabela_pendente = None
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
                tabela_pendente = None
                lendo_dados = True
            elif RE_SECAO.match(primeira) or RE_ACAO.search(primeira):
                lendo_dados = False
                tabela_atual = None
                tabela_pendente = None
            else:
                tabela_pendente = primeira
            continue

        if parece_cabecalho_tabela(celulas):
            if tabela_atual is None and tabela_pendente:
                tabela_atual = Tabela(nome=tabela_pendente)
                tela_atual.tabelas.append(tabela_atual)
                tabela_pendente = None
            if tabela_atual is not None:
                tabela_atual.colunas = [limpar_texto(c) for c in celulas if c]
            lendo_dados = True
            continue

        for acao in RE_ACAO.findall(texto_linha):
            tela_atual.acoes.append(Acao(limpar_texto(acao)))

        if lendo_dados:
            continue

        tabela_pendente = None
        campo = montar_campo(primeira, celulas[1] if len(celulas) > 1 else "")
        if campo:
            tela_atual.campos.append(campo)

    for tela in telas:
        tela.campos = deduplicar(tela.campos, "nome")
        tela.acoes = deduplicar(tela.acoes, "nome")
        tela.tabelas = deduplicar(tela.tabelas, "nome")
    return telas


def eh_regra(texto: str) -> bool:
    c = chave(texto)
    return any(chave(p) in c for p in PALAVRAS_REGRA)


def quebrar_sentencas(texto: str) -> list[str]:
    texto = limpar_texto(texto.replace("*", ""))
    partes = re.split(
        r"(?<=[.!?])\s+|(?=\bO\s+(?:Sistema|Atendente|Administrador|Operador|Estoquista|Usu[aá]rio)\b)",
        texto,
        flags=re.I,
    )
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


def parse_docx(caminho: str | Path) -> dict[str, Any]:
    documento = Document(str(caminho))
    telas: list[Tela] = []
    fluxos: list[Fluxo] = []
    fluxo_pendente: str | None = None
    fluxo_principal: Fluxo | None = None
    fluxo_atual: Fluxo | None = None
    secao_fluxo: str | None = None
    titulo_tela_pendente: str | None = None

    for bloco in iter_blocos(documento):
        if isinstance(bloco, Paragraph):
            texto = limpar_texto(bloco.text)
            if not texto:
                continue

            match_titulo_tela = re.match(r"^prot[oó]tipo\s+de\s+tela\s+de\s+(.+)$", texto, re.I)
            if match_titulo_tela:
                titulo_tela_pendente = f"Tela de {limpar_texto(match_titulo_tela.group(1))}"
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
            if texto.casefold() == "passos":
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

            novas_telas = extrair_telas_de_tabela(bloco, titulo_tela_pendente)
            if novas_telas:
                telas.extend(novas_telas)
                fluxo_pendente = None
                secao_fluxo = None
                titulo_tela_pendente = None

    return {
        "telas": [asdict(t) for t in telas],
        "fluxos": [asdict(f) for f in fluxos],
    }


def carregar_artefato(caminho: str | Path) -> dict[str, Any]:
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".json":
        return json.loads(caminho.read_text(encoding="utf-8"))
    if caminho.suffix.lower() == ".docx":
        return parse_docx(caminho)
    raise ValueError(f"Formato não suportado: {caminho.suffix}")


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

    extras = [{"tipo": tipo, "nome": item.get("nome")} for i, item in enumerate(encontrados) if i not in usados]
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
    for tela_ref, tela_aluno, score in parear_por_score(
        gabarito.get("telas", []), telas_aluno, score_tela, min(limite, 0.35)
    ):
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
    for fluxo_ref, fluxo_aluno, score in parear_por_score(
        gabarito.get("fluxos", []), fluxos_aluno, score_fluxo, min(limite, 0.35)
    ):
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


def salvar_ou_imprimir(dados: dict[str, Any], saida: str | None) -> None:
    texto = json.dumps(dados, ensure_ascii=False, indent=2)
    if saida:
        Path(saida).write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)


def criar_parser_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extrai e compara protótipos DOCX de engenharia de software.")
    sub = parser.add_subparsers(dest="comando")

    extrair = sub.add_parser("extrair", help="extrai telas e fluxos de um DOCX")
    extrair.add_argument("arquivo")
    extrair.add_argument("-o", "--output")

    comparar_cmd = sub.add_parser("comparar", help="compara gabarito e trabalho de aluno")
    comparar_cmd.add_argument("gabarito")
    comparar_cmd.add_argument("aluno")
    comparar_cmd.add_argument("-o", "--output")
    comparar_cmd.add_argument("--limite", type=float, default=0.72)

    lote = sub.add_parser("comparar-lote", help="compara um gabarito com todos os DOCX de uma pasta")
    lote.add_argument("gabarito")
    lote.add_argument("diretorio_alunos")
    lote.add_argument("-o", "--output")
    lote.add_argument("--limite", type=float, default=0.72)

    comparar_gemini = sub.add_parser("comparar-gemini", help="compara gabarito e aluno usando avaliação semântica do Gemini")
    comparar_gemini.add_argument("gabarito")
    comparar_gemini.add_argument("aluno")
    comparar_gemini.add_argument("-o", "--output")
    comparar_gemini.add_argument("--modelo")
    comparar_gemini.add_argument("--limite", type=float, default=0.72)
    comparar_gemini.add_argument("--timeout", type=int, default=120)
    comparar_gemini.add_argument("--tentativas", type=int, default=3)
    comparar_gemini.add_argument("--retry-delay", type=float, default=5.0)

    lote_gemini = sub.add_parser("comparar-lote-gemini", help="compara um gabarito com todos os DOCX de uma pasta usando Gemini")
    lote_gemini.add_argument("gabarito")
    lote_gemini.add_argument("diretorio_alunos")
    lote_gemini.add_argument("-o", "--output")
    lote_gemini.add_argument("--modelo")
    lote_gemini.add_argument("--limite", type=float, default=0.72)
    lote_gemini.add_argument("--timeout", type=int, default=120)
    lote_gemini.add_argument("--tentativas", type=int, default=3)
    lote_gemini.add_argument("--retry-delay", type=float, default=5.0)

    parser.add_argument("arquivo_compat", nargs="?", help="atalho legado: extrai um DOCX sem informar subcomando")
    return parser


def main() -> None:
    comandos = {"extrair", "comparar", "comparar-lote", "comparar-gemini", "comparar-lote-gemini", "-h", "--help"}
    if len(sys.argv) > 1 and sys.argv[1] not in comandos:
        salvar_ou_imprimir(parse_docx(sys.argv[1]), None)
        return

    parser = criar_parser_cli()
    args = parser.parse_args()

    if args.comando == "extrair":
        salvar_ou_imprimir(parse_docx(args.arquivo), args.output)
        return

    if args.comando == "comparar":
        gabarito = carregar_artefato(args.gabarito)
        aluno = carregar_artefato(args.aluno)
        salvar_ou_imprimir(comparar(gabarito, aluno, args.limite), args.output)
        return

    if args.comando == "comparar-lote":
        salvar_ou_imprimir(comparar_lote(args.gabarito, args.diretorio_alunos, args.limite), args.output)
        return

    if args.comando == "comparar-gemini":
        try:
            resultado = comparar_arquivo_com_gemini(
                args.gabarito,
                args.aluno,
                modelo=args.modelo,
                limite_deterministico=args.limite,
                timeout=args.timeout,
                tentativas=args.tentativas,
                retry_delay=args.retry_delay,
            )
        except Exception as exc:
            raise SystemExit(f"Erro na comparação Gemini: {exc}") from exc
        salvar_ou_imprimir(resultado, args.output)
        return

    if args.comando == "comparar-lote-gemini":
        try:
            resultado = comparar_lote_com_gemini(
                args.gabarito,
                args.diretorio_alunos,
                modelo=args.modelo,
                limite_deterministico=args.limite,
                timeout=args.timeout,
                tentativas=args.tentativas,
                retry_delay=args.retry_delay,
            )
        except Exception as exc:
            raise SystemExit(f"Erro na comparação Gemini: {exc}") from exc
        salvar_ou_imprimir(resultado, args.output)
        return

    if args.arquivo_compat:
        salvar_ou_imprimir(parse_docx(args.arquivo_compat), None)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
