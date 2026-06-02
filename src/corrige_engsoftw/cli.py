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


DEFAULT_GABARITO = Path("prototypes/gestao-contas/Prototipo.docx")
DEFAULT_DIRETORIO_TESTES = Path("tests/fixtures/prototypes/gestao-contas")
DEFAULT_DIRETORIO_SAIDA = Path("outputs")

def _saida_padrao(nome_arquivo: str) -> str:
    return str(DEFAULT_DIRETORIO_SAIDA / nome_arquivo)


def _saida_por_aluno(aluno: str, prefix: str = "resultado") -> str:
    return str(DEFAULT_DIRETORIO_SAIDA / f"{prefix}_{Path(aluno).stem}.json")


def salvar_ou_imprimir(dados: dict[str, Any], saida: str | None) -> None:
    texto = json.dumps(dados, ensure_ascii=False, indent=2)
    if saida:
        caminho_saida = Path(saida)
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        caminho_saida.write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)


def criar_parser_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extrai e compara protótipos DOCX de engenharia de software.")
    sub = parser.add_subparsers(dest="comando")

    extrair = sub.add_parser("extrair", help="extrai telas e fluxos de um DOCX")
    extrair.add_argument("arquivo", nargs="?", default=str(DEFAULT_GABARITO))
    extrair.add_argument("-o", "--output", default=None)

    comparar_cmd = sub.add_parser("comparar", help="compara gabarito com todos os DOCX de uma pasta usando Gemini")
    comparar_cmd.add_argument("gabarito", nargs="?", default=str(DEFAULT_GABARITO))
    comparar_cmd.add_argument("diretorio_alunos", nargs="?", default=str(DEFAULT_DIRETORIO_TESTES))
    comparar_cmd.add_argument("-o", "--output", default=None)
    comparar_cmd.add_argument("--modelo")
    comparar_cmd.add_argument("--limite", type=float, default=0.72)
    comparar_cmd.add_argument("--timeout", type=int, default=120)
    comparar_cmd.add_argument("--tentativas", type=int, default=3)
    comparar_cmd.add_argument("--retry-delay", type=float, default=5.0)

    comparar_det = sub.add_parser("comparar-deterministico", help="compara gabarito com todos os DOCX de uma pasta sem Gemini")
    comparar_det.add_argument("gabarito", nargs="?", default=str(DEFAULT_GABARITO))
    comparar_det.add_argument("diretorio_alunos", nargs="?", default=str(DEFAULT_DIRETORIO_TESTES))
    comparar_det.add_argument("-o", "--output", default=None)
    comparar_det.add_argument("--limite", type=float, default=0.72)

    parser.add_argument("arquivo_compat", nargs="?", help="atalho legado: extrai um DOCX sem informar subcomando")
    return parser


def main() -> None:
    comandos = {"extrair", "comparar", "comparar-deterministico", "-h", "--help"}
    if len(sys.argv) > 1 and sys.argv[1] not in comandos:
        salvar_ou_imprimir(parse_docx(sys.argv[1]), None)
        return

    parser = criar_parser_cli()
    args = parser.parse_args()

    if args.comando == "extrair":
        salvar_ou_imprimir(parse_docx(args.arquivo), args.output)
        return

    if args.comando == "comparar":
        # comparação em lote via Gemini
        diretorio = Path(args.diretorio_alunos)
        if args.output is None:
            # escreve um arquivo por aluno em outputs/
            for aluno_path in sorted(diretorio.glob("*.docx")):
                aluno_str = str(aluno_path)
                output = _saida_por_aluno(aluno_str)
                try:
                    resultado = comparar_arquivo_com_gemini(
                        args.gabarito,
                        aluno_str,
                        modelo=args.modelo,
                        limite_deterministico=args.limite,
                        timeout=args.timeout,
                        tentativas=args.tentativas,
                        retry_delay=args.retry_delay,
                    )
                    salvar_ou_imprimir(resultado, output)
                except Exception as exc:
                    salvar_ou_imprimir({"error": str(exc)}, output)
        else:
            # escreve um único arquivo de saída
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

    if args.comando == "comparar-deterministico":
        # comparação em lote determinística (sem Gemini)
        diretorio = Path(args.diretorio_alunos)
        if args.output is None:
            # escreve um arquivo por aluno em outputs/
            for aluno_path in sorted(diretorio.glob("*.docx")):
                aluno_str = str(aluno_path)
                output = _saida_por_aluno(aluno_str)
                gabarito = carregar_artefato(args.gabarito)
                aluno = carregar_artefato(aluno_str)
                try:
                    salvar_ou_imprimir(comparar(gabarito, aluno, args.limite), output)
                except Exception as exc:
                    salvar_ou_imprimir({"error": str(exc)}, output)
        else:
            # escreve um único arquivo de saída
            salvar_ou_imprimir(comparar_lote(args.gabarito, args.diretorio_alunos, args.limite), args.output)
        return

    if args.arquivo_compat:
        salvar_ou_imprimir(parse_docx(args.arquivo_compat), None)
        return

    parser.print_help()
