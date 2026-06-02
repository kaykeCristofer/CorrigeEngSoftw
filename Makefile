.PHONY: test test-unit test-integration test-coverage test-fast clean help

# Cores para output
YELLOW := \033[1;33m
GREEN := \033[1;32m
RED := \033[1;31m
NC := \033[0m # No Color

help:
	@echo "$(YELLOW)Comandos disponíveis:$(NC)"
	@echo "  $(GREEN)make test$(NC)                 - Executar todos os testes"
	@echo "  $(GREEN)make test-unit$(NC)            - Executar apenas testes unitários"
	@echo "  $(GREEN)make test-integration$(NC)     - Executar apenas testes de integração"
	@echo "  $(GREEN)make test-coverage$(NC)        - Executar testes com coverage"
	@echo "  $(GREEN)make test-fast$(NC)            - Executar testes rápidos (sem slow)"
	@echo "  $(GREEN)make test-performance$(NC)     - Executar testes de performance"
	@echo "  $(GREEN)make lint$(NC)                 - Executar linters"
	@echo "  $(GREEN)make format$(NC)               - Formatar código"
	@echo "  $(GREEN)make clean$(NC)                - Limpar arquivos gerados"

# Executar todos os testes
test:
	@echo "$(YELLOW)Executando todos os testes...$(NC)"
	pytest tests/ -v

# Executar apenas testes unitários
test-unit:
	@echo "$(YELLOW)Executando testes unitários...$(NC)"
	pytest tests/unit/ -v -m "not slow"

# Executar apenas testes de integração
test-integration:
	@echo "$(YELLOW)Executando testes de integração...$(NC)"
	pytest tests/integration/ -v

# Executar testes com coverage
test-coverage:
	@echo "$(YELLOW)Executando testes com coverage...$(NC)"
	pytest tests/ --cov=src/corrige_engsoftw --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Relatório HTML gerado em htmlcov/index.html$(NC)"

# Executar testes rápidos
test-fast:
	@echo "$(YELLOW)Executando testes rápidos...$(NC)"
	pytest tests/ -v -m "not slow" --timeout=10

# Executar testes de performance
test-performance:
	@echo "$(YELLOW)Executando testes de performance...$(NC)"
	pytest tests/integration/test_performance.py -v

# Executar linters
lint:
	@echo "$(YELLOW)Executando linters...$(NC)"
	flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503
	isort --check-only src/ tests/
	mypy src/ --ignore-missing-imports

# Formatar código
format:
	@echo "$(YELLOW)Formatando código...$(NC)"
	black src/ tests/ --line-length=100
	isort src/ tests/

# Limpar arquivos gerados
clean:
	@echo "$(YELLOW)Limpando arquivos gerados...$(NC)"
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Limpeza concluída$(NC)"

# Executar teste específico
test-one:
	@echo "$(RED)Uso: make test-one FILE=tests/unit/test_text_utils.py$(NC)"
	pytest $(FILE) -v
