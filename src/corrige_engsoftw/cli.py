from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .artifacts import carregar_artefato
from .comparator import comparar, comparar_lote
from .extractor import parse_docx
from .gemini_comparator import comparar_arquivo_com_gemini, comparar_lote_com_gemini


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
    comparar_gemini.add_argument("--timeout", type=int, default=60)

    lote_gemini = sub.add_parser("comparar-lote-gemini", help="compara um gabarito com todos os DOCX de uma pasta usando Gemini")
    lote_gemini.add_argument("gabarito")
    lote_gemini.add_argument("diretorio_alunos")
    lote_gemini.add_argument("-o", "--output")
    lote_gemini.add_argument("--modelo")
    lote_gemini.add_argument("--limite", type=float, default=0.72)
    lote_gemini.add_argument("--timeout", type=int, default=60)

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
            )
        except Exception as exc:
            raise SystemExit(f"Erro na comparação Gemini: {exc}") from exc
        salvar_ou_imprimir(resultado, args.output)
        return

    if args.arquivo_compat:
        salvar_ou_imprimir(parse_docx(args.arquivo_compat), None)
        return

    parser.print_help()
