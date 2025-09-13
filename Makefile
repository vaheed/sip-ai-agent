.PHONY: help install install-dev test test-cov lint format typecheck security clean docker-build docker-run docker-test pre-commit setup-dev

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pre-commit

# Testing targets
test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	pytest tests/ -v -m integration

# Code quality targets
lint: ## Run linting
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format: ## Format code
	black app/ tests/
	isort app/ tests/

typecheck: ## Run type checking
	mypy app/ --ignore-missing-imports --no-strict-optional

security: ## Run security checks
	bandit -r app/
	safety check

# Development setup
setup-dev: install-dev ## Setup development environment
	pre-commit install
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Docker targets
docker-build: ## Build Docker image
	docker build -t sip-ai-agent:latest .

docker-run: ## Run Docker container (requires .env file)
	docker run --rm -p 8080:8080 -p 5060:5060/udp -p 16000-16100:16000-16100/udp --env-file .env sip-ai-agent:latest

docker-test: ## Test Docker image
	docker build -t sip-ai-agent:test .
	docker run --rm sip-ai-agent:test python -c "print('Docker test passed')"

# Configuration validation
validate-config: ## Validate configuration
	python -c "import sys; sys.path.append('app'); from config import Settings; s = Settings(); print('Configuration validation passed')"

# Development server
dev: ## Run development server (requires .env file)
	python app/agent.py

# Monitoring
monitor: ## Open monitoring dashboard
	@echo "Opening monitoring dashboard..."
	@echo "Dashboard: http://localhost:8080"
	@echo "Health check: http://localhost:8080/healthz"
	@echo "Metrics: http://localhost:9090/metrics"

# Cleanup targets
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	rm -f bandit-report.json safety-report.json

clean-docker: ## Clean up Docker images and containers
	docker system prune -f
	docker image prune -f

# Documentation
docs: ## Generate documentation (if using sphinx)
	@echo "Documentation generation not yet implemented"

# Release helpers
version: ## Show current version
	@python -c "
import sys
sys.path.append('app')
try:
    from config import Settings
    settings = Settings()
    print('Version: 2.1.0')
    print('OpenAI Mode:', settings.openai_mode.value)
except Exception as e:
    print('Error getting version info:', e)
"

# Health check
health: ## Check system health
	@echo "Checking system health..."
	@python -c "
import sys
sys.path.append('app')
try:
    from health import get_health_monitor
    import asyncio
    
    async def check_health():
        monitor = get_health_monitor()
        report = await monitor.run_health_checks()
        print(f'Overall Status: {report.overall_status.value}')
        for check in report.checks:
            status_icon = '✅' if check.status.value == 'healthy' else '❌'
            print(f'{status_icon} {check.name}: {check.message}')
    
    asyncio.run(check_health())
except Exception as e:
    print(f'Health check failed: {e}')
"

# All quality checks
check-all: lint typecheck security test ## Run all quality checks

# CI/CD helpers
ci-test: ## Run tests for CI environment
	pytest tests/ -v --tb=short --maxfail=5

ci-build: ## Build for CI environment
	docker build -t sip-ai-agent:ci .

# Environment helpers
env-example: ## Show example environment configuration
	@echo "Copy env.example to .env and configure:"
	@echo "cp env.example .env"
	@echo "Edit .env with your configuration"

env-check: ## Check environment variables
	@echo "Checking environment configuration..."
	@python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['SIP_DOMAIN', 'SIP_USER', 'SIP_PASS', 'OPENAI_API_KEY', 'AGENT_ID']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print('❌ Missing required environment variables:')
    for var in missing_vars:
        print(f'   {var}')
    print('\\nPlease configure these in your .env file')
else:
    print('✅ All required environment variables are set')
"
