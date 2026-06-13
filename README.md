# ApplyPilot

> Agentic Job Application Copilot — a local-first AI copilot that turns a job post into a structured fit analysis, evidence-backed positioning, tailored application drafts, and a saved application record.

ApplyPilot is a production-quality portfolio app (not a chatbot) that demonstrates retrieval-augmented generation, LangGraph stateful workflows, structured output, human-in-the-loop approval, local Docker deployment, seeded data, integration tests, and browser-based E2E tests.

## Status

🚧 **Planning** — this repo currently holds the product and technical specifications. Implementation has not started.

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product Requirements Document — problem, users, goals, feature requirements, user journeys, milestones |
| [TECH_STACK](docs/TECH_STACK.md) | Technical stack and implementation plan — architecture, services, schema, testing, deployment |

## Architecture at a glance

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind + shadcn/ui
- **Backend/API:** FastAPI + Python + Pydantic v2
- **Agent workflow:** LangChain + LangGraph (stateful, resumable, human-in-the-loop)
- **Database:** Postgres + pgvector (relational + vector in one store)
- **Cache/queue:** Redis
- **Object storage:** MinIO / local volume
- **Testing:** pytest, Vitest, Playwright
- **Deployment:** Docker Compose (local production-like)

## Principles

1. **Evidence first** — every claim maps back to a known role, project, skill, or profile item.
2. **Human approval required** — the app drafts; the user decides what is final.
3. **Structured outputs over vague prose** — the backend produces predictable objects the UI can render.
4. **Local-first by default** — services, database, vector search, storage, and tests run locally through Docker.
5. **Testable agent behavior** — tests validate schemas, state transitions, tool calls, and user-visible outcomes.

## Getting started

Implementation is pending. The planned local workflow (see [TECH_STACK](docs/TECH_STACK.md)) is:

```bash
cp .env.example .env.local
make bootstrap
make up
make migrate
make seed
# open http://localhost:3000
```
