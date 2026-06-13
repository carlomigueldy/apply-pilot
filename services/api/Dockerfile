# syntax=docker/dockerfile:1
#
# ApplyPilot API / worker image.
# Build context is the REPO ROOT, so all source paths are prefixed services/api/.
#   docker build -f services/api/Dockerfile -t applypilot-api:local .
#
# The compose files override CMD:
#   api    -> uvicorn applypilot.main:app --host 0.0.0.0 --port 8000
#   worker -> python -m applypilot.worker

FROM python:3.12-slim AS base

# uv: fast, reproducible Python package manager (pinned binary).
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/services/api/.venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/services/api/.venv/bin:$PATH"

# Runtime OS deps: curl for container healthchecks, libpq for psycopg fallbacks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/services/api

# 1) Dependency layer — cached unless lockfile/manifest changes.
COPY services/api/pyproject.toml services/api/uv.lock services/api/.python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --extra dev

# 2) Application source.
COPY services/api/ ./

# 3) Install the project itself into the existing environment.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra dev

EXPOSE 8000

# Default command; overridden by compose for the worker.
CMD ["uvicorn", "applypilot.main:app", "--host", "0.0.0.0", "--port", "8000"]
