# ApplyPilot — developer task runner
# Docker Compose lives at infra/docker/docker-compose.yml.

COMPOSE := docker compose -f infra/docker/docker-compose.yml

.DEFAULT_GOAL := help

.PHONY: help bootstrap up down reset logs migrate seed \
	test test-api-unit test-integration test-web-unit test-e2e test-e2e-local \
	lint format \
	dev-api dev-web api-unit-local api-test-local

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ----------------------------------------------------------------------------
## Setup
## ----------------------------------------------------------------------------

bootstrap: ## Install JS deps and sync the Python (api) environment
	pnpm install
	cd services/api && uv sync --extra dev

## ----------------------------------------------------------------------------
## Docker stack
## ----------------------------------------------------------------------------

up: ## Start the docker stack (detached)
	$(COMPOSE) up -d

down: ## Stop the docker stack
	$(COMPOSE) down

reset: ## Tear down the stack including volumes, then start fresh
	$(COMPOSE) down -v
	$(COMPOSE) up -d

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

migrate: ## Apply database migrations (alembic) inside the api container
	$(COMPOSE) exec api alembic upgrade head

seed: ## Reset and seed demo data inside the api container
	$(COMPOSE) exec api python -m applypilot.seeds.seed --reset

## ----------------------------------------------------------------------------
## Tests
## ----------------------------------------------------------------------------

test: test-api-unit test-integration test-web-unit ## Run api unit, integration, and web unit tests

test-api-unit: ## Run backend unit tests inside the api container
	$(COMPOSE) exec api python -m pytest tests/unit -q

test-integration: ## Run backend integration tests inside the api container
	$(COMPOSE) exec api python -m pytest tests/integration -q

test-web-unit: ## Run web unit tests (vitest)
	pnpm --filter web test

test-e2e: ## Run end-to-end tests (playwright, inside Docker)
	pnpm --filter web exec playwright test

test-e2e-local: ## Seed + start API locally, then run Playwright E2E tests (no Docker)
	@echo "Seeding local database..."
	DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
	  EMBEDDING_PROVIDER=fake \
	  services/api/.venv/bin/python -m applypilot.seeds.seed --reset
	@echo "Starting API on :8000 (background)..."
	DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
	  LLM_PROVIDER=fake \
	  EMBEDDING_PROVIDER=fake \
	  services/api/.venv/bin/uvicorn applypilot.main:app --host 127.0.0.1 --port 8000 &
	@echo "Waiting for API to be ready..."
	until curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; do sleep 1; done
	@echo "Running Playwright E2E tests..."
	pnpm --filter web exec playwright test; \
	  EXIT=$$?; \
	  kill $$(lsof -ti:8000) 2>/dev/null || true; \
	  exit $$EXIT

## ----------------------------------------------------------------------------
## Lint & format
## ----------------------------------------------------------------------------

lint: ## Lint Python (ruff) and web (eslint)
	cd services/api && .venv/bin/ruff check .
	pnpm --filter web lint

format: ## Format Python (ruff) and the repo (prettier)
	cd services/api && .venv/bin/ruff format .
	pnpm format

## ----------------------------------------------------------------------------
## Local helpers (no docker — run against your host .venv / pnpm)
## ----------------------------------------------------------------------------

dev-api: ## Run the FastAPI dev server locally with reload on :8000
	cd services/api && .venv/bin/uvicorn applypilot.main:app --reload --port 8000

dev-web: ## Run the Next.js dev server locally
	pnpm --filter web dev

api-unit-local: ## Run backend unit tests locally against the host .venv
	cd services/api && .venv/bin/python -m pytest tests/unit -q

api-test-local: ## Run the full backend test suite locally against the host .venv
	cd services/api && .venv/bin/python -m pytest -q
