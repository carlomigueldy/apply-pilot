# ApplyPilot

> Agentic Job Application Copilot — paste a job post, get a structured fit analysis, evidence-backed drafts, and a ready-to-send application package. Human approval required at every step.

ApplyPilot is a production-quality portfolio app that demonstrates retrieval-augmented generation, LangGraph stateful workflows, structured output, human-in-the-loop approval, local Docker deployment, seeded demo data, backend integration tests, and Playwright E2E tests — all running entirely offline with `LLM_PROVIDER=fake`.

---

## What it does

1. **Paste a job post** — raw text or URL goes into `POST /api/applications`.
2. **Run analysis** — `POST /api/applications/{id}/analyze` triggers the LangGraph workflow:
   - Extracts job requirements from the post.
   - Searches the profile knowledge base (pgvector cosine similarity + keyword re-ranking).
   - Scores each requirement as `strong` / `partial` / `weak` / `missing`.
   - Generates a fit summary, red flags, and positioning strategy.
   - Produces application drafts (cover email, recruiter reply, resume bullets, talking points) with status `needs_review`.
3. **Review** — `GET /api/applications/{id}/analysis` shows the fit score and evidence. `GET /api/applications/{id}/drafts` shows draft bodies.
4. **Approve** — `POST /api/applications/{id}/approve-draft` accepts an optional edited body and notes; application status advances to `ready_to_apply`.

See [docs/PRD.md](docs/PRD.md) for the full product requirements and [docs/TECH_STACK.md](docs/TECH_STACK.md) for the architecture and stack decisions.

---

## Architecture

```
┌──────────────────────────┐
│        Next.js Web        │  http://localhost:3000
│  Dashboard / Review UI    │
└─────────────┬────────────┘
              │ HTTP / JSON
┌─────────────▼────────────┐
│       FastAPI API         │  http://localhost:8000
│ CRUD / Job / Profile      │
└─────────────┬────────────┘
              │ invokes
┌─────────────▼────────────┐
│ LangGraph Agent Graph     │
│ Stateful, human-in-loop   │
└───────┬─────────┬────────┘
        │         │
┌───────▼──────┐  ┌────────▼───────┐
│  Postgres    │  │   Redis         │
│  pgvector    │  │   Queue/cache   │
└──────────────┘  └────────────────┘
```

| Layer | Choice |
|---|---|
| Web | Next.js 16 App Router + TypeScript + Tailwind + shadcn/ui |
| API | FastAPI + Pydantic v2 (synchronous, no async DB) |
| Agent workflow | LangGraph + LangChain |
| Database | Postgres 16 + pgvector |
| ORM / migrations | SQLAlchemy 2.0 + Alembic |
| Cache / queue | Redis |
| Object storage | MinIO (or local volume) |
| JS package manager | pnpm |
| Python package manager | uv |
| Testing | pytest (backend), Vitest (web), Playwright (E2E) |
| Linting | Ruff + mypy (Python), ESLint + Prettier (JS/TS) |

---

## Quick start — Docker (recommended)

Requires Docker with the Compose plugin.

```bash
# 1. Install JS deps and sync the Python venv
make bootstrap

# 2. Start the full stack (Postgres, Redis, MinIO, API, Web)
make up

# 3. Apply database migrations
make migrate

# 4. Seed demo data (profile, job applications, drafts)
make seed

# 5. Open the app
open http://localhost:3000
```

Other useful targets:

```bash
make down          # stop the stack
make reset         # tear down volumes and restart clean
make logs          # tail logs from all containers
```

---

## Quick start — no Docker (local dev, Postgres already running)

Requires: Python 3.12+, Node.js 20+, pnpm, uv, and a running pgvector-enabled Postgres instance.

```bash
# 1. Start Postgres with pgvector (if not already running)
docker run -d --name pgvector \
  -e POSTGRES_USER=applypilot \
  -e POSTGRES_PASSWORD=applypilot \
  -e POSTGRES_DB=applypilot \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 2. Install JS dependencies
pnpm install

# 3. Sync the Python venv
cd services/api && uv sync --extra dev && cd ../..

# 4. Apply database migrations
cd services/api
DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
  .venv/bin/alembic upgrade head
cd ../..

# 5. Seed demo data
cd services/api
DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
  EMBEDDING_PROVIDER=fake \
  .venv/bin/python -m applypilot.seeds.seed --reset
cd ../..

# 6. Start the API (terminal 1)
cd services/api
DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
  LLM_PROVIDER=fake \
  EMBEDDING_PROVIDER=fake \
  .venv/bin/uvicorn applypilot.main:app --host 127.0.0.1 --port 8000

# 7. Start the web dev server (terminal 2)
pnpm --filter web dev
# => http://localhost:3000
```

Health check: `curl http://127.0.0.1:8000/api/health` should return `{"status":"ok","db":"ok"}`.

---

## Offline / deterministic mode

Setting `LLM_PROVIDER=fake` and `EMBEDDING_PROVIDER=fake` replaces all LLM and embedding calls with deterministic local stubs — no API keys, no network required. The fit analysis produces a realistic mix of `strong` / `partial` / `weak` / `missing` items; drafts are generated with status `needs_review`. This is the default for local dev and all CI tests.

---

## Tests

### Backend (pytest)

```bash
# Docker — run inside the api container
make test-api-unit       # unit tests only
make test-integration    # integration tests only

# Local — run against the host .venv (requires test DB)
cd services/api
TEST_DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot_test' \
DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot_test' \
TEST_MODE=true LLM_PROVIDER=fake EMBEDDING_PROVIDER=fake \
  .venv/bin/python -m pytest tests -q
# => 245 passed
```

### Web unit tests (Vitest)

```bash
make test-web-unit
# or directly:
pnpm --filter web test
```

### E2E tests (Playwright, Chromium)

The API must be seeded and running before Playwright starts. The web dev server is auto-started by Playwright's `webServer` config.

```bash
# Using the Makefile helper (seeds + starts API + runs Playwright):
make test-e2e-local

# Or manually:
# Terminal 1 — seed and start API
cd services/api
DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
  EMBEDDING_PROVIDER=fake \
  .venv/bin/python -m applypilot.seeds.seed --reset
DATABASE_URL='postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot' \
  LLM_PROVIDER=fake EMBEDDING_PROVIDER=fake \
  .venv/bin/uvicorn applypilot.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — run Playwright
pnpm --filter web exec playwright test

# Docker (inside containers):
make test-e2e
```

---

## Demo script

Run the full workflow end-to-end from a shell (API must be running on :8000 with seeded data):

```bash
# 1. Create a new application
APP=$(curl -s -X POST http://localhost:8000/api/applications \
  -H 'Content-Type: application/json' \
  -d '{
    "raw_job_post": "Senior Blockchain Engineer at ChainCo.\n\nWe are looking for an experienced blockchain engineer to lead smart contract development on EVM chains.\n\nRequirements:\n- 4+ years Solidity development\n- Experience with DeFi protocols\n- TypeScript / Node.js for tooling\n- Familiarity with Hardhat or Foundry\n- Strong testing culture\n\nNice to have:\n- Layer-2 experience (Optimism, Arbitrum)\n- Cross-chain bridge experience\n\nRemote-first, competitive salary.",
    "company_name": "ChainCo",
    "role_title": "Senior Blockchain Engineer"
  }')
APP_ID=$(echo $APP | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Created application: $APP_ID"

# 2. Trigger the LangGraph analysis workflow
curl -s -X POST "http://localhost:8000/api/applications/$APP_ID/analyze" | python3 -m json.tool

# 3. Poll or fetch the fit analysis (may take a few seconds)
sleep 2
curl -s "http://localhost:8000/api/applications/$APP_ID/analysis" | python3 -m json.tool

# 4. List generated drafts
curl -s "http://localhost:8000/api/applications/$APP_ID/drafts" | python3 -m json.tool

# 5. Approve the first draft (replace DRAFT_ID with an id from step 4)
DRAFT_ID=$(curl -s "http://localhost:8000/api/applications/$APP_ID/drafts" \
  | python3 -c "import sys,json; ds=json.load(sys.stdin); print(ds[0]['id']) if ds else print('')")
curl -s -X POST "http://localhost:8000/api/applications/$APP_ID/approve-draft" \
  -H 'Content-Type: application/json' \
  -d "{\"draft_id\": \"$DRAFT_ID\", \"notes\": \"Looks good — approved via demo script\"}" \
  | python3 -m json.tool

# 6. Confirm the application is now ready_to_apply
curl -s "http://localhost:8000/api/applications/$APP_ID" | python3 -c \
  "import sys,json; a=json.load(sys.stdin); print('Status:', a['status'])"
```

Expected final status: `ready_to_apply`.

---

## Project structure

```
apply-pilot/
  apps/
    web/                 # Next.js 16 App Router (TypeScript)
  services/
    api/                 # FastAPI + LangGraph + SQLAlchemy (Python)
      applypilot/
        agents/          # LangGraph graph, nodes, LLM providers
        api/             # FastAPI routes and dependency injection
        db/              # ORM models, repositories, migrations
        schemas/         # Pydantic v2 request/response schemas
        services/        # Domain services (profile, application, graph run)
        seeds/           # Deterministic demo data seeder
      tests/
        unit/            # Fast, no-DB unit tests
        integration/     # Tests against a real test database
  tests/
    e2e/
      specs/             # Playwright test specs
  infra/
    docker/              # docker-compose.yml and service configs
  docs/
    PRD.md               # Product requirements document
    TECH_STACK.md        # Architecture and stack decisions
  Makefile               # Developer task runner
```

---

## Principles

1. **Evidence first** — every claim maps back to a known profile item (role, project, skill, award).
2. **Human approval required** — the app drafts; the user decides what is final.
3. **Structured outputs over vague prose** — the backend produces predictable JSON objects the UI renders directly.
4. **Local-first by default** — the whole stack runs locally; no cloud dependency for development or testing.
5. **Testable agent behavior** — tests validate schemas, state transitions, tool calls, and user-visible outcomes with deterministic fake providers.
