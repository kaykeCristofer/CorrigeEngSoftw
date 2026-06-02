from __future__ import annotations

import re


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
