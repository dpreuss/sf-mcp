# Starfish MCP Server - Development Makefile

.PHONY: help install test test-unit test-integration lint format type-check clean dev-setup

help:  ## Show this help message
	@echo "Starfish MCP Server - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package and dependencies
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e ".[dev]"

dev-setup: install-dev  ## Set up development environment
	@echo "Development environment ready!"
	@echo "Copy env.example to .env and configure your Starfish settings."

test: test-unit  ## Run all tests (unit tests only by default)

test-unit:  ## Run unit tests with mock Starfish API
	pytest tests/ -v --tb=short -m "not integration"

test-integration:  ## Run integration tests against real Starfish API
	@echo "Running integration tests..."
	@echo "Ensure STARFISH_INTEGRATION_* environment variables are set!"
	pytest tests/test_integration.py -v --tb=short -m integration

test-all:  ## Run both unit and integration tests
	pytest tests/ -v --tb=short

test-watch:  ## Run tests in watch mode
	pytest-watch tests/ -- -v --tb=short -m "not integration"

lint:  ## Lint code with ruff
	ruff check starfish_mcp/ tests/

lint-fix:  ## Lint and fix code with ruff
	ruff check --fix starfish_mcp/ tests/

format:  ## Format code with black
	black starfish_mcp/ tests/

format-check:  ## Check code formatting
	black --check starfish_mcp/ tests/

type-check:  ## Run type checking with mypy
	mypy starfish_mcp/

quality: lint format-check type-check  ## Run all code quality checks

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:  ## Run the MCP server
	python -m starfish_mcp.server

run-dev:  ## Run the MCP server with debug logging
	LOG_LEVEL=DEBUG python -m starfish_mcp.server

# Example commands for testing specific scenarios
test-mock-demo:  ## Run a quick demo with mock data
	@echo "Testing with mock Starfish data..."
	pytest tests/test_tools.py::test_find_file_tool -v -s

# Build and distribution
build:  ## Build distribution packages
	python -m build

dist: clean build  ## Create distribution packages
	@echo "Distribution packages created in dist/"

# Environment checks
check-env:  ## Check if .env file exists and has required variables
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Copy env.example to .env and configure it."; \
		exit 1; \
	fi
	@if ! grep -q "STARFISH_API_ENDPOINT=" .env; then \
		echo "❌ STARFISH_API_ENDPOINT not set in .env"; \
		exit 1; \
	fi
	@if ! grep -q "STARFISH_USERNAME=" .env; then \
		echo "❌ STARFISH_USERNAME not set in .env"; \
		exit 1; \
	fi
	@if ! grep -q "STARFISH_PASSWORD=" .env; then \
		echo "❌ STARFISH_PASSWORD not set in .env"; \
		exit 1; \
	fi
	@echo "✅ .env file looks good!"

check-integration-env:  ## Check integration test environment
	@if [ -z "$$STARFISH_INTEGRATION_API_ENDPOINT" ]; then \
		echo "❌ STARFISH_INTEGRATION_API_ENDPOINT not set"; \
		echo "Set integration test environment variables:"; \
		echo "  export STARFISH_INTEGRATION_API_ENDPOINT='https://sf-redashdev.sfish.dev/api'"; \
		echo "  export STARFISH_INTEGRATION_USERNAME='demo'"; \
		echo "  export STARFISH_INTEGRATION_PASSWORD='demo'"; \
		exit 1; \
	fi
	@echo "✅ Integration test environment looks good!"

# Documentation
docs:  ## Generate documentation (placeholder)
	@echo "Documentation generation not implemented yet"

# TESTING COMMANDS - MANDATORY FOR ALL DEVELOPMENT

# Core testing commands
test:  ## Run all unit tests (MANDATORY before committing)
	@echo "🧪 Running all unit tests..."
	pytest tests/ -v --tb=short -x --ignore=tests/test_integration*.py

test-unit:  ## Run unit tests only (alias for test)
	@$(MAKE) test

test-integration:  ## Run integration tests against real Starfish API
	@echo "🌐 Running integration tests..."
	@$(MAKE) check-integration-env
	pytest tests/test_integration*.py -v -m integration --tb=short

test-modular:  ## Test new modular architecture specifically
	@echo "🏗️  Testing modular tools architecture..."
	pytest tests/test_tools_modular.py tests/test_query_builder.py -v

test-watch:  ## Auto-run tests on file changes (development)
	@echo "👁️  Watching for changes... (Ctrl+C to stop)"
	pytest-watch tests/ --verbose --tb=short --ignore=tests/test_integration*.py

test-specific:  ## Run specific test file (usage: make test-specific FILE=test_tools_modular.py)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Usage: make test-specific FILE=test_tools_modular.py"; \
		exit 1; \
	fi
	pytest tests/$(FILE) -v

test-failed:  ## Re-run only failed tests from last run
	pytest --lf -v

# Coverage and quality
coverage:  ## Generate test coverage report
	@echo "📊 Generating coverage report..."
	pytest tests/ --cov=starfish_mcp --cov-report=html --cov-report=term --ignore=tests/test_integration*.py
	@echo "📄 Coverage report: htmlcov/index.html"

coverage-integration:  ## Coverage including integration tests
	@echo "📊 Generating coverage with integration tests..."
	@$(MAKE) check-integration-env
	pytest tests/ --cov=starfish_mcp --cov-report=html --cov-report=term

# Development workflow shortcuts
quick-test:  ## Quick test - run fastest tests only
	pytest tests/test_models.py tests/test_config.py -v --tb=short

test-query-builder:  ## Test query builder specifically (for parameter development)
	pytest tests/test_query_builder.py -v

# MANDATORY: Full check before committing
check: quality test coverage  ## 🚨 MANDATORY: Run full checks before committing
	@echo "✅ All checks passed! Safe to commit."

full-check: check test-integration  ## Complete check including integration tests

ci: quality test coverage  ## Run CI pipeline (quality + unit tests + coverage)

# Debugging helpers
debug-config:  ## Debug configuration loading
	python -c "from starfish_mcp.config import load_config; print(load_config())"

debug-mock:  ## Debug mock client
	python -c "import asyncio; from tests.conftest import MockStarfishClient; client = MockStarfishClient([], [], [], {}); print('Mock client created successfully')"
