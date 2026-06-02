from __future__ import annotations

from dataclasses import dataclass, field


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
