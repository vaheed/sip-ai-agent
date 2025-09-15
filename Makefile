.PHONY: help install test test-cov clean docker-build docker-run docker-test web-ui web-demo

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install production dependencies
	pip install -r requirements.txt


# Testing targets
test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	pytest tests/ -v -m integration

# Security checks (for production)
security: ## Run security checks
	bandit -r app/
	safety check

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
	@python scripts/version.py current

version-bump-patch: ## Bump patch version
	@python scripts/version.py bump --type patch

version-bump-minor: ## Bump minor version
	@python scripts/version.py bump --type minor

version-bump-major: ## Bump major version
	@python scripts/version.py bump --type major

version-tag: ## Create git tag for current version
	@python scripts/version.py tag --push

version-info: ## Show Docker image version info
	@python scripts/version.py info

release: ## Create a new release (bump version, tag, and push)
	@echo "Creating new release..."
	@read -p "Enter release type (patch/minor/major): " type; \
	python scripts/version.py bump --type $$type; \
	python scripts/version.py tag --push; \
	echo "Release created successfully!"

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
check-all: security test ## Run all quality checks

# Comprehensive testing
test-all: ## Run comprehensive test suite (backend + frontend + docker)
	@echo "Running comprehensive test suite..."
	@if [ -f "scripts/test-all.sh" ]; then \
		chmod +x scripts/test-all.sh && ./scripts/test-all.sh; \
	elif [ -f "scripts/test-all.ps1" ]; then \
		powershell -ExecutionPolicy Bypass -File scripts/test-all.ps1; \
	else \
		echo "Test script not found. Please run individual tests."; \
	fi

test-all-backend: ## Run comprehensive backend tests only
	@echo "Running backend tests..."
	@if [ -f "scripts/test-all.sh" ]; then \
		chmod +x scripts/test-all.sh && ./scripts/test-all.sh; \
	elif [ -f "scripts/test-all.ps1" ]; then \
		powershell -ExecutionPolicy Bypass -File scripts/test-all.ps1 -SkipFrontend; \
	fi

test-all-frontend: ## Run comprehensive frontend tests only
	@echo "Running frontend tests..."
	@if [ -f "scripts/test-all.sh" ]; then \
		chmod +x scripts/test-all.sh && ./scripts/test-all.sh; \
	elif [ -f "scripts/test-all.ps1" ]; then \
		powershell -ExecutionPolicy Bypass -File scripts/test-all.ps1 -SkipDocker; \
	fi

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

# Web UI targets
web-ui: ## Start the web UI (development)
	python -m app.start_web_ui

web-demo: ## Start the web UI with demo calls
	python -m app.start_web_ui --demo

web-build: ## Build the web UI Docker container
	docker-compose build web

web-run: ## Run the web UI in Docker
	docker-compose up web

# Deployment targets
deploy: ## Deploy to production
	./scripts/deploy.sh

deploy-staging: ## Deploy to staging
	ENVIRONMENT=staging ./scripts/deploy.sh

deploy-version: ## Deploy specific version (usage: make deploy-version VERSION=v1.2.3)
	VERSION=$(VERSION) ./scripts/deploy.sh

deploy-status: ## Show deployment status
	./scripts/deploy.sh status

deploy-logs: ## Show deployment logs
	./scripts/deploy.sh logs

deploy-stop: ## Stop all services
	./scripts/deploy.sh stop

deploy-rollback: ## Rollback to previous version
	./scripts/deploy.sh rollback

# UI/UX Quality targets
ui-test: ## Run UI/UX tests (E2E only)
	cd web && npm run test:e2e

ui-accessibility: ## Run accessibility tests
	cd web && npm run a11y

ui-lighthouse: ## Run Lighthouse performance tests
	cd web && npm run lighthouse
