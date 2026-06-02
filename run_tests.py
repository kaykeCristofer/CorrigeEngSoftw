#!/usr/bin/env python3
"""
Script para executar testes com várias opções.
Uso: python run_tests.py [options]
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Executa um comando e exibe o resultado."""
    print(f"\n{'='*70}")
    print(f"🧪 {description}")
    print(f"{'='*70}")
    print(f"Comando: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Script para executar testes do projeto CorrigeEngSoftw"
    )
    
    parser.add_argument(
        "action",
        nargs="?",
        default="all",
        choices=[
            "all",
            "unit",
            "integration",
            "performance",
            "coverage",
            "fast",
            "cli",
            "lint",
            "format",
            "clean",
        ],
        help="Tipo de teste ou ação a executar"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verbose"
    )
    
    parser.add_argument(
        "-s", "--show-output",
        action="store_true",
        help="Mostrar output completo"
    )
    
    parser.add_argument(
        "-k", "--keyword",
        help="Filtrar testes por keyword"
    )
    
    parser.add_argument(
        "--markers",
        help="Filtrar por markers (ex: 'not slow')"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    pytest_cmd = ["pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.show_output:
        pytest_cmd.append("-s")
    
    if args.keyword:
        pytest_cmd.extend(["-k", args.keyword])
    
    if args.markers:
        pytest_cmd.extend(["-m", args.markers])
    
    success = True
    
    if args.action == "all":
        # Executar todos os testes
        success = run_command(
            pytest_cmd + ["tests/"],
            "Executando TODOS os testes"
        )
    
    elif args.action == "unit":
        # Testes unitários
        success = run_command(
            pytest_cmd + ["tests/unit/"],
            "Executando testes UNITÁRIOS"
        )
    
    elif args.action == "integration":
        # Testes de integração
        success = run_command(
            pytest_cmd + ["tests/integration/"],
            "Executando testes de INTEGRAÇÃO"
        )
    
    elif args.action == "performance":
        # Testes de performance
        success = run_command(
            pytest_cmd + ["tests/integration/test_performance.py"],
            "Executando testes de PERFORMANCE"
        )
    
    elif args.action == "coverage":
        # Com coverage
        success = run_command(
            pytest_cmd + [
                "tests/",
                "--cov=src/corrige_engsoftw",
                "--cov-report=html",
                "--cov-report=term-missing"
            ],
            "Executando testes com COVERAGE"
        )
        
        if success:
            print("\n✓ Relatório HTML gerado em: htmlcov/index.html")
    
    elif args.action == "fast":
        # Testes rápidos (sem slow)
        success = run_command(
            pytest_cmd + ["tests/", "-m", "not slow", "--timeout=10"],
            "Executando testes RÁPIDOS"
        )
    
    elif args.action == "cli":
        # Testes da CLI
        success = run_command(
            pytest_cmd + ["tests/unit/test_cli.py"],
            "Executando testes da CLI"
        )
    
    elif args.action == "lint":
        # Lint
        print("\n" + "="*70)
        print("🔍 Executando LINT")
        print("="*70)
        
        lint_cmd = [
            "flake8",
            "src/",
            "tests/",
            "--max-line-length=100",
            "--ignore=E501,W503"
        ]
        
        success = run_command(lint_cmd, "flake8")
        
        if success:
            isort_cmd = ["isort", "--check-only", "src/", "tests/"]
            success = run_command(isort_cmd, "isort check")
            
            if success:
                mypy_cmd = ["mypy", "src/", "--ignore-missing-imports"]
                success = run_command(mypy_cmd, "mypy")
    
    elif args.action == "format":
        # Format
        print("\n" + "="*70)
        print("📝 Formatando código")
        print("="*70)
        
        black_cmd = ["black", "src/", "tests/", "--line-length=100"]
        success = run_command(black_cmd, "black")
        
        if success:
            isort_cmd = ["isort", "src/", "tests/"]
            success = run_command(isort_cmd, "isort")
    
    elif args.action == "clean":
        # Clean
        print("\n" + "="*70)
        print("🧹 Limpando arquivos gerados")
        print("="*70)
        
        to_remove = [
            "htmlcov/",
            ".coverage",
            ".pytest_cache/",
            "__pycache__/",
            ".mypy_cache/",
            "*.pyc"
        ]
        
        for pattern in to_remove:
            subprocess.run(["rm", "-rf", pattern], capture_output=True)
        
        print("✓ Limpeza concluída")
        success = True
    
    # Resultado final
    print("\n" + "="*70)
    if success:
        print("✓ Sucesso!")
        sys.exit(0)
    else:
        print("✗ Falhou!")
        sys.exit(1)


if __name__ == "__main__":
    main()
