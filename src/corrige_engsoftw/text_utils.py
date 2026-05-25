from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


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
    "solicitada": "solicitada",
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
