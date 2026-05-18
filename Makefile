.PHONY: help install dev dev-stop dev-backend dev-frontend build start docker-up docker-down docker-build clean test lint coverage db-init db-seed fmt

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd src/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install pytest pytest-asyncio pytest-cov httpx aiosqlite
	cd src/frontend && npm install

dev: ## Start dev servers (kills old 3001/5173, then backend + frontend)
	@bash ops/scripts/dev-start.sh

dev-stop: ## Stop processes on ports 3001 and 5173
	@bash ops/scripts/dev-stop.sh

dev-backend: ## Start backend only (frees port 3001 first)
	@bash ops/scripts/dev-stop.sh 2>/dev/null || true
	@lsof -ti:3001 | xargs kill -9 2>/dev/null || true
	cd src/backend && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3001

dev-frontend: ## Start frontend dev server only
	cd src/frontend && npm run dev

build: ## Build frontend for production
	cd src/frontend && npm run build

docker-up: ## Start all services via Docker Compose
	docker compose -f ops/docker/docker-compose.yml up -d

docker-up-lite: ## Start minimal services (MySQL + Backend + Frontend, no Milvus)
	docker compose -f ops/docker/docker-compose.lite.yml up -d

db-mysql-dev: ## Start local dev MySQL only (port 3306)
	docker compose -f ops/docker/docker-compose.dev.yml up -d

docker-down: ## Stop all Docker services
	docker compose -f ops/docker/docker-compose.yml down

docker-build: ## Build Docker images
	docker compose -f ops/docker/docker-compose.yml build

docker-logs: ## View Docker logs
	docker compose -f ops/docker/docker-compose.yml logs -f

clean: ## Clean build artifacts
	rm -rf src/backend/__pycache__ src/backend/app/**/__pycache__
	rm -rf src/frontend/dist src/frontend/node_modules
	rm -rf *.log logs/*.log
	find . -name "*.pyc" -delete
	find . -name "*.tsbuildinfo" -delete
	find . -name "__pycache__" -type d -delete

test: ## Run backend tests
	cd src/backend && python -m pytest ../../tests/ -v

test-cov: ## Run tests with coverage report
	cd src/backend && python -m pytest ../../tests/ -v --cov=app --cov-report=term-missing

lint: ## Run linters
	cd src/backend && ruff check app/ 2>/dev/null || echo "ruff not installed"
	cd src/frontend && npm run lint 2>/dev/null || echo "ESLint not configured"

fmt: ## Format code
	cd src/backend && ruff format app/ 2>/dev/null || echo "ruff not installed"
	cd src/frontend && npx prettier --write "src/**/*.{ts,tsx,css}" 2>/dev/null || echo "prettier not installed"

db-init: ## Initialize database tables
	cd src/backend && python -c "from app.cli import _cmd_db; import asyncio, argparse; asyncio.run(_cmd_db(argparse.Namespace(db_action='init')))"

db-migrate: ## Apply schema patches (new columns, etc.)
	cd src/backend && source venv/bin/activate && python -m app.cli db migrate

db-seed: ## Seed database with default data
	cd src/backend && python -c "from app.cli import _cmd_db; import asyncio, argparse; asyncio.run(_cmd_db(argparse.Namespace(db_action='seed')))"
