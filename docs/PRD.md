# ApplyPilot PRD

**Product:** ApplyPilot — Agentic Job Application Copilot  
**Document type:** Product Requirements Document  
**Version:** 1.0  
**Date:** 2026-06-13  
**Primary deployment target:** Local production-like Docker environment  
**Primary user:** Senior software engineer actively applying to remote roles

---

## 1. Executive Summary

ApplyPilot is a local-first AI job application copilot that turns a job post into a structured fit analysis, evidence-backed positioning, tailored application drafts, interview talking points, and a saved job application record.

The project is designed as a production-quality portfolio app, not a simple chatbot. It demonstrates retrieval-augmented generation, LangGraph stateful workflows, structured output, human-in-the-loop approval, local Docker deployment, seeded data, integration tests, and browser-based E2E tests.

The product should be useful enough for a real job search while remaining scoped enough to build as an end-to-end portfolio project.

---

## 2. Problem Statement

Job applications are repetitive but require high-quality tailoring. A strong candidate often has relevant experience, but converting that experience into job-specific positioning takes time.

Common pain points:

- Copying and analyzing job descriptions manually.
- Rewriting the same recruiter replies and cover emails.
- Mapping role requirements to actual resume/project evidence.
- Forgetting which version of a draft was used for each application.
- Overstating experience because AI-generated drafts are not grounded in real evidence.
- Lacking a repeatable system for salary positioning and interview preparation.

ApplyPilot solves this by creating a reliable workflow where an agent analyzes a job post, retrieves relevant career evidence, produces structured outputs, and pauses for human review before anything is finalized.

---

## 3. Target Users

### 3.1 Primary User

A senior software engineer or product engineer applying to remote software roles.

Typical profile:

- Has multiple past roles and projects.
- Needs tailored applications quickly.
- Wants evidence-backed answers for recruiter screens and interviews.
- Wants to maintain a clean job tracker.
- Is comfortable running a local Docker-based app.

### 3.2 Secondary Users

- Freelancers applying to contract roles.
- Developers building a portfolio-worthy AI agent project.
- Career coaches who want to demonstrate structured candidate/job matching.

---

## 4. Product Goals

### 4.1 MVP Goals

1. Let the user paste a job post and receive a structured fit analysis.
2. Map job requirements to concrete evidence from the user profile, resume, projects, and prior answers.
3. Generate tailored recruiter replies, cover emails, resume bullets, and interview talking points.
4. Save every analysis and draft into a local database.
5. Require human approval before a final application draft is marked as ready.
6. Support local production-like deployment through Docker Compose.
7. Seed the database with realistic demo data.
8. Provide integration and E2E tests that validate the core workflow.

### 4.2 Portfolio Goals

The project should demonstrate:

- Agent workflow design with LangGraph.
- Tool calling and structured outputs with LangChain.
- RAG over a personal career knowledge base.
- Postgres + pgvector retrieval.
- State persistence and resumable workflows.
- Human-in-the-loop approval checkpoints.
- Local Docker deployment.
- Seed data and deterministic test fixtures.
- E2E testing with Playwright.
- Clean software architecture and API boundaries.

---

## 5. Non-Goals

The MVP will not include:

- Automatic email sending.
- Automatic LinkedIn or job board submissions.
- Multi-user SaaS billing.
- Browser extension.
- OAuth login.
- Complex resume PDF editing.
- Production cloud deployment.
- A marketplace of prompts.
- Fully autonomous job applications.

These can be future extensions, but the MVP should focus on a robust local workflow.

---

## 6. Product Principles

1. **Evidence first.** Every claim should map back to a known role, project, skill, or profile item.
2. **Human approval required.** The app may draft, but the user decides what is final.
3. **Structured outputs over vague prose.** The backend should produce predictable objects the UI can render.
4. **Local-first by default.** App services, database, vector search, storage, and tests should run locally through Docker.
5. **Testable agent behavior.** Tests should validate schemas, state transitions, tool calls, and user-visible outcomes.
6. **Useful for real applications.** The workflow should save time in an actual job search.

---

## 7. Core User Journey

### 7.1 Main Flow

1. User opens the local web app.
2. User reviews or edits seeded career profile data.
3. User creates a new job application record.
4. User pastes a job description or job URL text.
5. App extracts company, role title, location, salary, requirements, responsibilities, and constraints.
6. Agent retrieves relevant career evidence.
7. Agent generates:
   - Fit score
   - Strong matches
   - Weak matches
   - Red flags
   - Salary positioning
   - Tailored resume bullets
   - Recruiter reply
   - Cover email
   - Interview talking points
8. User reviews outputs in the UI.
9. User approves, edits, or regenerates specific sections.
10. App saves final approved draft and marks the application as ready.

### 7.2 Human-in-the-Loop Flow

The workflow must pause before marking a generated draft as final.

The user can:

- Approve the generated draft.
- Edit the draft manually.
- Ask for a rewrite with instructions.
- Reject the draft and keep the analysis only.

---

## 8. MVP Feature Requirements

### F1. Local User Profile Knowledge Base

**Description:** The user should have a structured local career profile that the agent can retrieve from.

**Requirements:**

- Seed sample profile data on first setup.
- Store roles, companies, dates, skills, projects, achievements, testimonials, salary preferences, and interview answers.
- Support manual editing from the UI.
- Store embeddings for searchable profile chunks.
- Allow a profile item to be tagged by category:
  - `role`
  - `project`
  - `skill`
  - `achievement`
  - `testimonial`
  - `salary`
  - `interview_answer`
  - `preference`

**Acceptance Criteria:**

- User can view seeded profile data.
- User can add a new project.
- User can edit a profile item.
- Vector search returns relevant evidence for a sample job post.
- E2E test confirms profile evidence appears in a generated fit analysis.

---

### F2. Job Post Ingestion

**Description:** The user can paste a job description and create an application record.

**Requirements:**

- Accept raw job post text.
- Optional fields:
  - Company name
  - Role title
  - Job URL
  - Salary range
  - Work arrangement
  - Time zone
  - Recruiter name
  - Recruiter email
- Extract structured job details using LLM structured output.
- Save raw input and extracted fields.

**Acceptance Criteria:**

- User can create a job application from pasted text.
- Extracted role title, company, work arrangement, and requirements appear in the UI.
- Invalid or very short job posts show a helpful validation message.
- Integration test validates parser output against a fixed sample job post.

---

### F3. Fit Analysis

**Description:** The agent analyzes the job against the user's profile.

**Requirements:**

- Generate a fit score from 0 to 100.
- Categorize requirements:
  - Strong match
  - Partial match
  - Weak match
  - Missing
  - Unknown
- For every match, include:
  - Requirement
  - Evidence summary
  - Evidence source IDs
  - Confidence score
- Flag concerns:
  - On-site requirement
  - Salary below target
  - Time zone mismatch
  - Required skill gap
  - Contract risk
  - Unclear compensation
- Recommend positioning strategy.

**Acceptance Criteria:**

- Analysis cannot include a strong match without evidence source IDs.
- Weak matches include a recommended mitigation.
- Red flags are shown separately from skill gaps.
- Fit score is deterministic enough in tests using mocked LLM responses.

---

### F4. Evidence Mapper

**Description:** The system maps requirements to the user's actual career evidence.

**Requirements:**

- Use semantic search over profile chunks.
- Use keyword search fallback for exact technologies.
- Return top evidence snippets with source IDs.
- Allow the user to open the source item in the UI.
- Store the evidence mapping used for each analysis.

**Acceptance Criteria:**

- Searching `Next.js production experience` returns seeded frontend/Next.js evidence.
- Searching `Web3 engineering` returns seeded blockchain/Web3 evidence.
- Searching `AI agents` returns seeded AI workflow/RAG evidence.
- Every generated claim in the fit analysis references evidence.

---

### F5. Application Draft Generator

**Description:** Generate job-specific application assets.

**Outputs:**

1. Recruiter reply
2. Cover email
3. Resume summary
4. Tailored resume bullets
5. Interview talking points
6. Salary positioning response
7. Concise self-introduction

**Requirements:**

- Use job details, fit analysis, and evidence mapping.
- Allow tone options:
  - Direct
  - Warm professional
  - Confident
  - Concise
- Allow draft length:
  - Short
  - Medium
  - Detailed
- Store every generated draft version.
- Allow section-level regeneration.

**Acceptance Criteria:**

- User can generate all application assets from one job post.
- User can regenerate only the recruiter reply without rerunning full analysis.
- Generated salary response respects the configured target compensation.
- E2E test confirms draft is displayed and can be approved.

---

### F6. Human Review and Approval

**Description:** User must review generated outputs before marking them ready.

**Requirements:**

- Draft status values:
  - `generated`
  - `needs_review`
  - `approved`
  - `rejected`
  - `edited`
- User can approve a draft.
- User can edit generated text.
- User can add review notes.
- Approved draft is locked from accidental overwrite unless explicitly regenerated.

**Acceptance Criteria:**

- New drafts default to `needs_review`.
- User cannot mark an application as `ready_to_apply` until at least one draft is approved.
- E2E test approves a generated recruiter reply and verifies status change.

---

### F7. Job Application Tracker

**Description:** Track job applications locally.

**Statuses:**

- `saved`
- `analyzed`
- `drafted`
- `ready_to_apply`
- `applied`
- `interviewing`
- `offer`
- `rejected`
- `archived`

**Requirements:**

- List applications.
- Filter by status.
- Search by company, role, skill, or note.
- Show created date and latest activity.
- Allow notes and follow-up reminders as plain records, not scheduled background jobs.

**Acceptance Criteria:**

- User can create, update, and archive an application.
- Status changes are persisted.
- App list shows latest analysis summary.
- Search returns seeded application examples.

---

### F8. Local Seed Data

**Description:** Database should be seeded with realistic demo data.

**Seed data should include:**

- One user profile.
- Three work experiences.
- Five projects.
- Twenty to forty evidence chunks.
- Three sample job posts:
  - Senior Full-Stack Engineer
  - Senior AI Engineer
  - Web3 Product Engineer
- Sample analyses and drafts.
- Test user preferences:
  - Remote preferred
  - Target compensation
  - Time zone
  - Preferred tone

**Acceptance Criteria:**

- `make seed` resets and seeds the database.
- App is usable immediately after seeding.
- E2E tests can rely on stable seed records.

---

### F9. Observability and Debugging

**Description:** The app should expose enough visibility to debug agent behavior locally.

**Requirements:**

- Log each graph run.
- Store graph state snapshots.
- Store model request metadata:
  - model provider
  - model name
  - token counts if available
  - latency
  - error state
- Store retrieved evidence for each analysis.
- Optional LangSmith tracing when environment variables are provided.
- Local logs should be useful even without cloud tracing.

**Acceptance Criteria:**

- User can inspect a run history page.
- Failed graph runs show failed node and error message.
- Integration test verifies run metadata is stored.

---

## 9. Suggested UI Pages

### 9.1 Dashboard

- Total applications
- Drafts needing review
- High-fit opportunities
- Recent applications
- Red flag summary

### 9.2 Applications List

- Table of applications
- Filters by status
- Search
- Create new application button

### 9.3 New Application

- Paste job post
- Optional metadata fields
- Submit for analysis

### 9.4 Application Detail

Tabs:

1. Overview
2. Job Details
3. Fit Analysis
4. Evidence
5. Drafts
6. Interview Prep
7. Run Logs

### 9.5 Profile Knowledge Base

- View profile items
- Add/edit profile item
- Regenerate embeddings
- Search evidence

### 9.6 Settings

- Model provider
- Target salary
- Preferred work setup
- Tone preference
- Local test mode toggle

---

## 10. Agent Workflow Requirements

The main workflow should be implemented as a LangGraph graph.

### 10.1 Graph State

The graph state should include:

```ts
type ApplicationGraphState = {
  applicationId: string;
  rawJobPost: string;
  extractedJob?: ExtractedJob;
  requirements?: JobRequirement[];
  evidenceMatches?: EvidenceMatch[];
  fitAnalysis?: FitAnalysis;
  draftBundle?: DraftBundle;
  reviewDecision?: ReviewDecision;
  errors?: GraphError[];
};
```

### 10.2 Graph Nodes

Recommended nodes:

1. `validate_input`
2. `extract_job_details`
3. `extract_requirements`
4. `retrieve_evidence`
5. `rank_evidence`
6. `generate_fit_analysis`
7. `generate_draft_bundle`
8. `human_review_interrupt`
9. `persist_approved_outputs`
10. `finalize_application_status`

### 10.3 Conditional Edges

- If job post is invalid → stop with validation error.
- If evidence retrieval is weak → continue, but mark confidence lower.
- If salary/work setup conflicts with user preferences → add red flag.
- If user rejects draft → route to regeneration or final save as rejected.
- If user approves draft → finalize application as `ready_to_apply`.

---

## 11. Data Requirements

### 11.1 Core Entities

- User profile
- Profile item
- Evidence chunk
- Embedding
- Job application
- Extracted job
- Requirement
- Evidence match
- Fit analysis
- Draft
- Graph run
- Review decision

### 11.2 Data Retention

Because this is a local-first app:

- All application data remains in local Postgres.
- Uploaded files are stored locally.
- LLM provider calls may send selected prompt context externally unless using a local model.
- The app should clearly display whether the active model provider is local or external.

---

## 12. Testing Requirements

### 12.1 Unit Tests

Cover:

- Requirement extraction schema validation.
- Fit score calculation helper.
- Evidence ranking helper.
- Draft status transitions.
- API validation.
- Database repositories.

### 12.2 Integration Tests

Cover:

- API + Postgres.
- API + pgvector retrieval.
- LangGraph run with fake model.
- Seed script.
- Draft approval persistence.
- Error state persistence.

### 12.3 E2E Tests

Use Playwright to cover:

1. Seeded app loads.
2. User creates a new application.
3. User pastes sample job post.
4. Agent analysis completes using deterministic test mode.
5. Fit analysis appears.
6. Evidence mappings appear.
7. Draft bundle appears.
8. User edits and approves recruiter reply.
9. Application status becomes `ready_to_apply`.

### 12.4 Test Mode

The app must support a deterministic test mode:

- Use fake/mocked LLM responses.
- Use fixed embeddings or deterministic vector fixtures.
- Use seeded data.
- Avoid external API calls.
- Disable flaky background behavior.

---

## 13. Local Deployment Requirements

The production-like deployment should run through Docker Compose.

Required local services:

- Web app
- API/agent service
- Worker service if long-running graph execution is separated
- Postgres with pgvector
- Redis
- Object storage or local file volume
- Optional local LLM runtime
- Optional observability stack

Required commands:

```bash
make bootstrap
make up
make migrate
make seed
make test
make test-integration
make test-e2e
make reset
make down
```

---

## 14. Security and Privacy Requirements

- Do not log API keys.
- Do not expose local services publicly by default.
- Store secrets only in `.env.local`.
- Provide `.env.example`.
- Clearly label external model provider usage.
- User must approve drafts before final status.
- Do not implement automatic job applications in MVP.
- Do not send emails automatically in MVP.

---

## 15. Success Metrics

Because this is a local portfolio app, success metrics are product and engineering quality metrics.

### Product Metrics

- Time from job post paste to usable draft: under 2 minutes with external LLM.
- At least 80% of generated claims include evidence.
- User can complete the core application flow without editing seed data.
- User can approve a draft in under 5 clicks after analysis.

### Engineering Metrics

- `make up` starts the full local stack.
- `make seed` produces a usable demo environment.
- E2E test passes from a clean database.
- Integration tests do not require external LLM calls.
- All structured outputs validate against schemas.
- Graph run state is persisted and inspectable.

---

## 16. Milestones

### Milestone 1: Local Skeleton

- Monorepo setup
- Docker Compose
- Next.js web app
- FastAPI agent API
- Postgres + pgvector
- Seed script
- Health checks

### Milestone 2: Knowledge Base

- Profile item CRUD
- Evidence chunking
- Embedding generation
- Search API
- Seeded profile data

### Milestone 3: Job Analysis

- Job post ingestion
- Structured extraction
- Requirement parsing
- Evidence retrieval
- Fit analysis generation

### Milestone 4: Draft Generation

- Draft bundle generation
- Draft versioning
- Section-level regeneration
- Human review status flow

### Milestone 5: Testing and Demo Polish

- Unit tests
- Integration tests
- Playwright E2E tests
- Demo seed data
- Run logs page
- README demo script

---

## 17. Release Criteria

The MVP is complete when:

- The app runs locally with one Docker Compose command.
- Seed data creates a realistic demo environment.
- User can create a job application from pasted job text.
- Agent generates fit analysis with evidence.
- Agent generates draft bundle.
- User can approve a draft.
- Application status updates to `ready_to_apply`.
- Core workflow passes E2E tests.
- Integration tests run without external LLM calls.
- README explains setup, test commands, and architecture.

---

## 18. Future Enhancements

- Resume PDF export.
- Browser extension for job pages.
- Gmail draft creation after user approval.
- Calendar follow-up reminders.
- Multi-profile support.
- Local-only model mode with Ollama.
- Evaluation datasets for fit analysis quality.
- Prompt/version comparison dashboard.
- Job board scraping.
- Company research agent.
- Salary negotiation simulator.
