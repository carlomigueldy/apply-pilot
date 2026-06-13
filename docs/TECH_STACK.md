# ApplyPilot TECH_STACK

**Project:** ApplyPilot — Agentic Job Application Copilot  
**Document type:** Technical Stack and Implementation Plan  
**Version:** 1.0  
**Date:** 2026-06-13  
**Deployment target:** Local production-like Docker Compose stack  
**Testing target:** Unit, integration, and Playwright E2E tests with seeded data

---

## 1. Technical Direction

ApplyPilot should be built as a local-first, production-style monorepo.

Recommended architecture:

- **Frontend:** Next.js + TypeScript
- **Backend/API:** FastAPI + Python
- **Agent workflow:** LangChain + LangGraph
- **Database:** Postgres + pgvector
- **Cache/queue:** Redis
- **File/object storage:** Local volume or MinIO
- **Testing:** pytest, Vitest, Playwright
- **Deployment:** Docker Compose
- **Observability:** Local logs + persisted graph runs, optional LangSmith tracing

This split works well because LangChain and LangGraph are strongest in Python, while the frontend remains in a modern TypeScript/Next.js stack.

---

## 2. Architecture Overview

```txt
┌──────────────────────────┐
│        Next.js Web        │
│  Dashboard / Review UI    │
└─────────────┬────────────┘
              │ HTTP / JSON
┌─────────────▼────────────┐
│       FastAPI API         │
│ Auth-lite / CRUD / Jobs   │
└─────────────┬────────────┘
              │ invokes
┌─────────────▼────────────┐
│ LangGraph Agent Service   │
│ Stateful job workflow     │
└───────┬─────────┬────────┘
        │         │
        │         └────────────┐
        │                      │
┌───────▼────────┐     ┌───────▼────────┐
│ Postgres       │     │ Redis           │
│ pgvector       │     │ Queue/cache     │
└───────┬────────┘     └────────────────┘
        │
┌───────▼────────┐
│ Local storage   │
│ MinIO/volume    │
└────────────────┘

Optional:
- External LLM provider
- Local Ollama model runtime
- LangSmith tracing
```

---

## 3. Stack Decisions

| Layer | Choice | Reason |
|---|---|---|
| Web app | Next.js App Router + TypeScript | Strong portfolio value, excellent UI/dev experience |
| UI components | Tailwind CSS + shadcn/ui | Fast, clean, customizable dashboard UI |
| API | FastAPI | Native Python ecosystem for LangChain/LangGraph |
| API schemas | Pydantic v2 | Strong validation for structured LLM outputs |
| Agent orchestration | LangGraph | Stateful, resumable, human-in-the-loop workflows |
| LLM app framework | LangChain | Tools, structured output, model abstractions, retrievers |
| Database | Postgres | Reliable local relational store |
| Vector search | pgvector | Keeps relational and vector data in one DB |
| ORM | SQLAlchemy 2.0 or SQLModel | Mature Python DB layer |
| Migrations | Alembic | Standard migration workflow |
| Queue/cache | Redis | Job status, graph execution coordination, cache |
| Background worker | Celery, Dramatiq, or RQ | Optional for long-running graph runs |
| Object storage | MinIO or local volume | Local file uploads and resume/profile docs |
| E2E tests | Playwright | Browser-level validation of full workflow |
| API tests | pytest + httpx | Fast integration tests against API |
| Frontend tests | Vitest + Testing Library | Component and utility tests |
| Linting | Ruff, mypy, ESLint, Prettier | Quality gates |
| Package manager | pnpm for JS, uv for Python | Fast local development |
| Containers | Docker Compose | Local production-like deployment |
| Observability | DB run logs + optional LangSmith | Useful locally, expandable later |

---

## 4. Repository Structure

```txt
applypilot/
  apps/
    web/
      app/
      components/
      lib/
      tests/
      package.json
      playwright.config.ts
  services/
    api/
      applypilot/
        api/
          routes/
          dependencies.py
        core/
          config.py
          logging.py
        db/
          models.py
          session.py
          repositories/
          migrations/
        schemas/
          application.py
          drafts.py
          evidence.py
          graph.py
          jobs.py
          profile.py
        agents/
          graphs/
            application_graph.py
          nodes/
            validate_input.py
            extract_job_details.py
            extract_requirements.py
            retrieve_evidence.py
            rank_evidence.py
            generate_fit_analysis.py
            generate_draft_bundle.py
            human_review.py
            persist_outputs.py
          prompts/
            extract_job_details.md
            fit_analysis.md
            draft_bundle.md
          tools/
            evidence_search.py
            profile_lookup.py
            salary_strategy.py
          llm/
            provider.py
            fake_model.py
            openai_provider.py
            anthropic_provider.py
            ollama_provider.py
        services/
          embedding_service.py
          application_service.py
          profile_service.py
          graph_run_service.py
        seeds/
          seed.py
          data/
            profile.seed.json
            jobs.seed.json
            drafts.seed.json
        tests/
          unit/
          integration/
      pyproject.toml
      Dockerfile
  packages/
    shared-types/
      src/
      package.json
  infra/
    docker/
      docker-compose.yml
      docker-compose.test.yml
      postgres/
        init.sql
      minio/
  tests/
    e2e/
      specs/
        application-flow.spec.ts
      fixtures/
        sample-job-posts.ts
  docs/
    PRD.md
    TECH_STACK.md
    ARCHITECTURE.md
  .env.example
  Makefile
  README.md
```

---

## 5. Docker Compose Services

### 5.1 Required Services

```yaml
services:
  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
    ports:
      - "3000:3000"
    env_file:
      - .env.local
    depends_on:
      - api

  api:
    build:
      context: .
      dockerfile: services/api/Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env.local
    depends_on:
      - postgres
      - redis
      - minio

  worker:
    build:
      context: .
      dockerfile: services/api/Dockerfile
    command: ["python", "-m", "applypilot.worker"]
    env_file:
      - .env.local
    depends_on:
      - postgres
      - redis
      - api

  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: applypilot
      POSTGRES_USER: applypilot
      POSTGRES_PASSWORD: applypilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: applypilot
      MINIO_ROOT_PASSWORD: applypilot-local-secret
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

### 5.2 Optional Services

```yaml
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "4318:4318"
```

Use Ollama only if you want a fully local LLM mode. For faster iteration, support external OpenAI-compatible or Anthropic-compatible providers through environment variables.

---

## 6. Environment Variables

Create `.env.example`:

```bash
# App
APP_ENV=local
APP_NAME=ApplyPilot
WEB_URL=http://localhost:3000
API_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql+psycopg://applypilot:applypilot@postgres:5432/applypilot

# Redis
REDIS_URL=redis://redis:6379/0

# Object storage
STORAGE_DRIVER=minio
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=applypilot
MINIO_SECRET_KEY=applypilot-local-secret
MINIO_BUCKET=applypilot

# LLM provider
LLM_PROVIDER=fake
LLM_MODEL=fake-applypilot-v1

# External provider examples
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Local Ollama example
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1

# Embeddings
EMBEDDING_PROVIDER=fake
EMBEDDING_MODEL=fake-embedding-v1

# Optional tracing
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=applypilot-local

# Testing
TEST_MODE=false
SEED_DEMO_DATA=true
```

For tests, use:

```bash
LLM_PROVIDER=fake
EMBEDDING_PROVIDER=fake
TEST_MODE=true
```

---

## 7. Backend Design

### 7.1 FastAPI Modules

```txt
api/routes/
  health.py
  profile.py
  applications.py
  analyses.py
  drafts.py
  graph_runs.py
  settings.py
```

### 7.2 Key API Endpoints

```txt
GET    /health
GET    /profile/items
POST   /profile/items
PATCH  /profile/items/{id}
POST   /profile/search

GET    /applications
POST   /applications
GET    /applications/{id}
PATCH  /applications/{id}
POST   /applications/{id}/analyze
POST   /applications/{id}/generate-drafts
POST   /applications/{id}/approve-draft
POST   /applications/{id}/regenerate-section

GET    /applications/{id}/analysis
GET    /applications/{id}/evidence
GET    /applications/{id}/drafts

GET    /graph-runs
GET    /graph-runs/{id}
```

### 7.3 Structured Schemas

Use Pydantic models for every LLM output.

Example:

```python
from pydantic import BaseModel, Field
from typing import Literal

class JobRequirement(BaseModel):
    id: str
    text: str
    category: Literal["frontend", "backend", "ai", "web3", "devops", "soft_skill", "domain", "other"]
    priority: Literal["must_have", "nice_to_have", "unknown"]

class EvidenceMatch(BaseModel):
    requirement_id: str
    profile_item_id: str
    evidence_chunk_id: str
    summary: str
    confidence: float = Field(ge=0, le=1)

class FitAnalysisItem(BaseModel):
    requirement_id: str
    match_level: Literal["strong", "partial", "weak", "missing", "unknown"]
    explanation: str
    evidence_chunk_ids: list[str]
    confidence: float = Field(ge=0, le=1)

class FitAnalysis(BaseModel):
    fit_score: int = Field(ge=0, le=100)
    summary: str
    items: list[FitAnalysisItem]
    red_flags: list[str]
    positioning_strategy: str
```

Validation rule:

```txt
If match_level is "strong" or "partial", evidence_chunk_ids must not be empty.
```

---

## 8. LangGraph Workflow

### 8.1 Main Graph

```txt
START
  ↓
validate_input
  ↓
extract_job_details
  ↓
extract_requirements
  ↓
retrieve_evidence
  ↓
rank_evidence
  ↓
generate_fit_analysis
  ↓
generate_draft_bundle
  ↓
human_review_interrupt
  ↓
persist_approved_outputs
  ↓
END
```

### 8.2 Graph State

```python
from typing import TypedDict, NotRequired

class ApplicationGraphState(TypedDict):
    application_id: str
    raw_job_post: str
    extracted_job: NotRequired[dict]
    requirements: NotRequired[list[dict]]
    evidence_matches: NotRequired[list[dict]]
    fit_analysis: NotRequired[dict]
    draft_bundle: NotRequired[dict]
    review_decision: NotRequired[dict]
    errors: NotRequired[list[dict]]
```

### 8.3 Human Review

The review node should interrupt the workflow before finalizing outputs.

Review actions:

```txt
approve
edit
reject
regenerate
```

The interrupted graph state should include:

- Draft bundle
- Fit analysis
- Evidence matches
- Suggested next action
- Review instructions

### 8.4 Persistence

Persist:

- Graph run ID
- Application ID
- Current node
- Status
- Input payload
- Output payload
- Error payload
- Started at
- Completed at
- Duration
- Model metadata

---

## 9. LangChain Usage

Use LangChain for:

1. Chat model abstraction.
2. Tool definitions.
3. Structured output.
4. Prompt templates.
5. Retriever interfaces.
6. Optional tracing integration.

Recommended internal tools:

```txt
profile_search_tool
job_requirement_parser_tool
salary_strategy_tool
evidence_lookup_tool
draft_style_tool
```

Important rule:

```txt
Agent tools should read and analyze local data.
No tool should send an email, submit an application, or mutate external systems in the MVP.
```

---

## 10. Database Schema

### 10.1 Tables

```sql
users
  id uuid primary key
  name text
  email text
  timezone text
  target_salary_min_usd integer
  target_salary_max_usd integer
  remote_preference text
  created_at timestamptz
  updated_at timestamptz

profile_items
  id uuid primary key
  user_id uuid references users(id)
  type text
  title text
  body text
  metadata jsonb
  created_at timestamptz
  updated_at timestamptz

evidence_chunks
  id uuid primary key
  profile_item_id uuid references profile_items(id)
  chunk_text text
  chunk_index integer
  embedding vector(1536)
  metadata jsonb
  created_at timestamptz

job_applications
  id uuid primary key
  user_id uuid references users(id)
  company_name text
  role_title text
  job_url text
  raw_job_post text
  status text
  work_arrangement text
  salary_text text
  timezone_text text
  created_at timestamptz
  updated_at timestamptz

job_requirements
  id uuid primary key
  application_id uuid references job_applications(id)
  text text
  category text
  priority text
  metadata jsonb

evidence_matches
  id uuid primary key
  application_id uuid references job_applications(id)
  requirement_id uuid references job_requirements(id)
  evidence_chunk_id uuid references evidence_chunks(id)
  summary text
  confidence numeric
  created_at timestamptz

fit_analyses
  id uuid primary key
  application_id uuid references job_applications(id)
  fit_score integer
  summary text
  red_flags jsonb
  positioning_strategy text
  raw_output jsonb
  created_at timestamptz

drafts
  id uuid primary key
  application_id uuid references job_applications(id)
  type text
  title text
  body text
  status text
  version integer
  review_notes text
  created_at timestamptz
  updated_at timestamptz

graph_runs
  id uuid primary key
  application_id uuid references job_applications(id)
  graph_name text
  status text
  current_node text
  input_payload jsonb
  output_payload jsonb
  error_payload jsonb
  model_metadata jsonb
  started_at timestamptz
  completed_at timestamptz

review_decisions
  id uuid primary key
  application_id uuid references job_applications(id)
  draft_id uuid references drafts(id)
  decision text
  notes text
  created_at timestamptz
```

### 10.2 pgvector Index

Use an approximate index once there is enough data:

```sql
CREATE INDEX evidence_chunks_embedding_idx
ON evidence_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

For a small local seed database, exact vector search is also acceptable.

---

## 11. Seed Data Plan

### 11.1 Seed Command

```bash
make seed
```

Implementation:

```bash
cd services/api
uv run python -m applypilot.seeds.seed --reset
```

### 11.2 Seeded Profile

Include realistic records:

```json
{
  "name": "Demo Senior Software Engineer",
  "timezone": "Asia/Manila",
  "target_salary_min_usd": 5500,
  "target_salary_max_usd": 7500,
  "remote_preference": "remote_only"
}
```

### 11.3 Seeded Work Experiences

1. Senior Software Engineer — Rollup/infra/Web3 company
2. Senior Blockchain Engineer — Prediction markets startup
3. Lead Blockchain Engineer — Metaverse/Web3 game startup

### 11.4 Seeded Projects

1. RAG document assistant
2. Agentic coding workflow
3. Web3 prediction market MVP
4. NFT sale/minting platform
5. Full-stack analytics dashboard

### 11.5 Seeded Job Posts

1. Senior Full-Stack Engineer
2. Senior AI Engineer
3. Web3 Product Engineer

### 11.6 Deterministic Test Fixtures

For tests, seed:

- Fixed profile item IDs.
- Fixed evidence chunk IDs.
- Fixed sample job post IDs.
- Fake embeddings.
- Fake LLM outputs.

---

## 12. Testing Strategy

### 12.1 Unit Tests

Backend:

```bash
make test-api-unit
```

Covers:

- Pydantic schema validation.
- Evidence match validation.
- Draft status transitions.
- Fit score helper logic.
- Prompt input builders.
- Repository functions with mocked DB session.

Frontend:

```bash
make test-web-unit
```

Covers:

- Application table rendering.
- Draft approval button states.
- Fit score component.
- Evidence list component.
- Form validation.

### 12.2 Integration Tests

```bash
make test-integration
```

Covers:

- API with real Postgres test DB.
- Migrations.
- Seed command.
- Profile search.
- Application creation.
- LangGraph run using fake LLM.
- Draft approval persistence.
- Graph run failure persistence.

Recommended approach:

- Use `docker-compose.test.yml`.
- Use separate `applypilot_test` database.
- Use fake LLM and fake embeddings.
- Reset DB before each test module or test session.

### 12.3 E2E Tests

```bash
make test-e2e
```

Use Playwright.

Core spec:

```txt
application-flow.spec.ts
```

Flow:

1. Open dashboard.
2. Verify seeded profile exists.
3. Create new application.
4. Paste sample job post.
5. Start analysis.
6. Wait for analysis complete.
7. Verify fit score appears.
8. Verify evidence appears.
9. Verify recruiter reply draft appears.
10. Edit recruiter reply.
11. Approve recruiter reply.
12. Verify application status is ready_to_apply.

### 12.4 LLM Testing Rules

Do not rely on external LLMs in automated tests.

Use three provider modes:

```txt
fake       deterministic tests
external   manual local development
ollama     optional fully local experimentation
```

Fake provider behavior:

- Match known fixture job post by hash.
- Return fixed structured outputs.
- Fail intentionally for specific test inputs.
- Produce stable draft text.

---

## 13. Makefile Commands

```makefile
bootstrap:
	pnpm install
	cd services/api && uv sync

up:
	docker compose -f infra/docker/docker-compose.yml up --build

down:
	docker compose -f infra/docker/docker-compose.yml down

reset:
	docker compose -f infra/docker/docker-compose.yml down -v
	docker compose -f infra/docker/docker-compose.yml up --build

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m applypilot.seeds.seed --reset

test:
	make test-api-unit
	make test-web-unit
	make test-integration
	make test-e2e

test-api-unit:
	docker compose exec api pytest tests/unit

test-integration:
	docker compose -f infra/docker/docker-compose.test.yml up --build --abort-on-container-exit

test-web-unit:
	pnpm --filter web test

test-e2e:
	pnpm --filter web playwright test

lint:
	pnpm lint
	docker compose exec api ruff check .
	docker compose exec api mypy applypilot

format:
	pnpm format
	docker compose exec api ruff format .
```

---

## 14. Frontend Implementation

### 14.1 App Routes

```txt
/
  Dashboard

/applications
  Application list

/applications/new
  Create application

/applications/[id]
  Application detail

/profile
  Knowledge base

/settings
  Local settings
```

### 14.2 Components

```txt
ApplicationTable
ApplicationStatusBadge
JobPostForm
FitScoreCard
RequirementMatchList
EvidencePanel
DraftBundleTabs
DraftEditor
ApprovalPanel
GraphRunTimeline
ProfileItemEditor
```

### 14.3 Data Fetching

Use TanStack Query.

Recommended hooks:

```ts
useApplications()
useApplication(id)
useCreateApplication()
useAnalyzeApplication()
useDrafts(applicationId)
useApproveDraft()
useProfileSearch()
useGraphRuns(applicationId)
```

### 14.4 UI States

Every async view should handle:

- Loading
- Empty
- Error
- Success
- Regenerating
- Needs review
- Approved

---

## 15. Backend Implementation Details

### 15.1 LLM Provider Interface

```python
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMProvider(Protocol):
    async def structured(self, prompt: str, schema: type[T]) -> T:
        ...

    async def text(self, prompt: str) -> str:
        ...
```

Implementations:

```txt
FakeLLMProvider
OpenAIProvider
AnthropicProvider
OllamaProvider
```

### 15.2 Embedding Provider Interface

```python
class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> list[float]:
        ...

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        ...
```

Implementations:

```txt
FakeEmbeddingProvider
OpenAIEmbeddingProvider
OllamaEmbeddingProvider
```

### 15.3 Evidence Search

Retrieval strategy:

1. Convert requirement to embedding.
2. Query pgvector top 8.
3. Keyword fallback for exact tech terms.
4. Merge and deduplicate.
5. Rerank by:
   - semantic similarity
   - exact keyword match
   - profile item recency
   - category relevance

Return:

```python
class RetrievedEvidence(BaseModel):
    evidence_chunk_id: str
    profile_item_id: str
    title: str
    snippet: str
    score: float
    source_type: str
```

---

## 16. Prompt Files

Store prompts as versioned Markdown files.

```txt
agents/prompts/
  extract_job_details.md
  extract_requirements.md
  fit_analysis.md
  draft_bundle.md
  salary_strategy.md
  rewrite_draft_section.md
```

Each prompt should include:

- Purpose
- Inputs
- Output schema
- Rules
- Failure behavior
- Evidence requirements

Example rule:

```txt
Do not claim the candidate has experience unless it appears in the provided evidence.
If evidence is weak, mark the match as partial or weak.
For strong and partial matches, include evidence source IDs.
```

---

## 17. Observability

### 17.1 Local Observability

Persist every graph run to `graph_runs`.

Store:

- Graph name
- Application ID
- Status
- Current node
- Node timings
- Error payload
- Model provider
- Model name
- Token count if available
- Retrieved evidence IDs
- Output schema validation errors

### 17.2 Optional LangSmith

Enable when:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=applypilot-local
```

Do not require LangSmith for local tests.

### 17.3 Debug UI

Add a `Run Logs` tab to application detail.

Show:

- Node timeline
- Inputs/outputs per node
- Error states
- Retrieved evidence
- Draft versions
- Approval decisions

---

## 18. Local Production Workflow

### 18.1 First Run

```bash
cp .env.example .env.local
make bootstrap
make up
make migrate
make seed
```

Open:

```txt
http://localhost:3000
```

### 18.2 Demo Flow

```txt
1. Open dashboard.
2. Go to Applications.
3. Create a new application.
4. Paste seeded sample job post.
5. Click Analyze.
6. Review fit analysis.
7. Open Evidence tab.
8. Open Drafts tab.
9. Edit recruiter reply.
10. Approve recruiter reply.
11. Confirm status changes to ready_to_apply.
```

### 18.3 Test Flow

```bash
make reset
make seed
make test-integration
make test-e2e
```

---

## 19. Quality Gates

Before considering MVP complete:

```txt
- API unit tests pass
- API integration tests pass
- Frontend unit tests pass
- Playwright E2E tests pass
- Docker Compose stack starts cleanly
- Seed command is idempotent
- Migrations run from scratch
- No external LLM calls during tests
- Generated analysis validates against schema
- Strong/partial claims include evidence IDs
- Draft approval status persists
```

---

## 20. Suggested Implementation Order

### Phase 1: Infrastructure

1. Create monorepo.
2. Add Docker Compose.
3. Add Postgres + pgvector.
4. Add FastAPI health endpoint.
5. Add Next.js dashboard shell.
6. Add Makefile.

### Phase 2: Data Layer

1. Add SQLAlchemy models.
2. Add Alembic migrations.
3. Add seed script.
4. Add profile CRUD.
5. Add evidence chunking.
6. Add fake embeddings.

### Phase 3: Agent Workflow

1. Add fake LLM provider.
2. Add job extraction schemas.
3. Add evidence search tool.
4. Add LangGraph application graph.
5. Persist graph runs.
6. Add analysis endpoint.

### Phase 4: Draft and Review

1. Add draft generation.
2. Add draft versioning.
3. Add review/approval API.
4. Add review UI.
5. Add status transitions.

### Phase 5: Tests and Polish

1. Add integration tests.
2. Add Playwright E2E flow.
3. Add run logs UI.
4. Add README.
5. Add sample demo script.
6. Add optional external model provider.

---

## 21. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| LLM output is inconsistent | Use structured output, schema validation, fake provider in tests |
| Agent workflow becomes too complex | Keep graph nodes explicit and small |
| Evidence mapping hallucinates | Require source IDs for strong/partial claims |
| E2E tests become flaky | Use deterministic fake model and seeded DB |
| Local setup becomes heavy | Keep optional services optional |
| pgvector setup issues | Use official pgvector Docker image |
| Drafts overstate experience | Add strict prompt rules and validation checks |
| External provider cost | Default tests to fake provider; support local Ollama |

---

## 22. Definition of Done

The technical implementation is done when:

- `make up` starts the app.
- `make seed` creates usable demo data.
- User can complete the job post to approved draft workflow.
- Graph runs are persisted.
- Evidence is attached to generated fit analysis.
- E2E test validates the main flow.
- Integration tests run without external APIs.
- README explains local deployment, seeding, and testing.
