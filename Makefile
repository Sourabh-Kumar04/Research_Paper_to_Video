# RASO Platform Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "RASO Platform Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install     Install all dependencies"
	@echo "  dev         Set up development environment"
	@echo ""
	@echo "Development Commands:"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-prop   Run property-based tests only"
	@echo "  test-cov    Run tests with coverage report"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  type-check  Run mypy type checking"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build    Build Docker images"
	@echo "  docker-up       Start services with Docker Compose"
	@echo "  docker-down     Stop Docker Compose services"
	@echo "  docker-logs     View Docker Compose logs"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean       Clean temporary files and caches"
	@echo "  docs        Generate documentation"

# Setup Commands
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -e .
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installation complete!"

dev: install
	@echo "Setting up development environment..."
	cp .env.example .env
	mkdir -p data logs temp
	@echo "Development environment ready!"
	@echo "Edit .env file with your configuration"

# Testing Commands
test:
	@echo "Running all tests..."
	pytest

test-unit:
	@echo "Running unit tests..."
	pytest -m "not property and not integration"

test-prop:
	@echo "Running property-based tests..."
	pytest -m property

test-integration:
	@echo "Running integration tests..."
	pytest -m integration

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

# Code Quality Commands
lint:
	@echo "Running linting checks..."
	flake8 agents graph backend animation audio video infra
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	black agents graph backend animation audio video infra tests
	isort agents graph backend animation audio video infra tests
	@echo "Code formatting complete!"

type-check:
	@echo "Running type checks..."
	mypy agents graph backend animation audio video infra
	@echo "Type checking complete!"

# Docker Commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d
	@echo "Services started! Check status with: docker-compose ps"

docker-down:
	@echo "Stopping Docker Compose services..."
	docker-compose down

docker-logs:
	@echo "Viewing Docker Compose logs..."
	docker-compose logs -f

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

# Development Server Commands
run-backend:
	@echo "Starting backend development server..."
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm start

run-ollama:
	@echo "Starting Ollama server..."
	ollama serve

# Utility Commands
clean:
	@echo "Cleaning temporary files and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	rm -rf temp/* logs/*
	@echo "Cleanup complete!"

docs:
	@echo "Generating documentation..."
	# Add documentation generation commands here
	@echo "Documentation generated!"

# Database Commands
db-reset:
	@echo "Resetting Redis database..."
	redis-cli FLUSHDB

# Model Management Commands
download-models:
	@echo "Downloading default models..."
	ollama pull deepseek-coder:6.7b
	@echo "Models downloaded!"

# CI/CD Commands
ci-test:
	@echo "Running CI test suite..."
	HYPOTHESIS_PROFILE=ci pytest --cov-report=xml

ci-lint:
	@echo "Running CI linting..."
	flake8 agents graph backend animation audio video infra --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check agents graph backend animation audio video infra tests
	isort --check-only agents graph backend animation audio video infra tests

# Security Commands
security-check:
	@echo "Running security checks..."
	pip-audit
	bandit -r agents graph backend animation audio video infra

# Performance Commands
profile:
	@echo "Running performance profiling..."
	# Add profiling commands here

# Monitoring Commands
health-check:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "Backend not responding"
	curl -f http://localhost:3000 || echo "Frontend not responding"