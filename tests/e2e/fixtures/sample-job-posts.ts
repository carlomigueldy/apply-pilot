/**
 * Realistic sample job posts used in E2E tests.
 * Must be >= 30 characters and contain enough signal for the AI analysis pipeline.
 */

export const SENIOR_FULLSTACK_JOB = `
Senior Full-Stack Engineer — ApplyPilot

About the Role
We are looking for a Senior Full-Stack Engineer to join our product team and help build
the next generation of AI-powered career tools. You will work across the entire stack —
from designing and shipping React/Next.js user interfaces to implementing robust FastAPI
backend services and LangGraph-powered AI pipelines.

Responsibilities
- Design and build performant, accessible web UIs using Next.js 15 (App Router), React 19,
  TypeScript, and Tailwind CSS.
- Develop RESTful APIs and async background workers with Python/FastAPI and SQLAlchemy.
- Integrate and maintain LangGraph/LangChain orchestration flows for LLM-based features.
- Write and maintain a test suite covering unit, integration, and Playwright E2E scenarios
  (target: 80% coverage).
- Contribute to architecture decisions around PostgreSQL (pgvector), Redis, and cloud
  deployments on AWS / Vercel.
- Collaborate with product designers to ship polished, responsive experiences on both web
  and mobile (React Native / Expo).
- Participate in code reviews, pair-programming sessions, and sprint planning.

Requirements
- 5+ years of professional software engineering experience.
- Strong proficiency in TypeScript and modern React patterns (hooks, server components).
- Solid Python skills including async programming and REST API design.
- Experience with relational databases (PostgreSQL preferred) and vector search (pgvector,
  Pinecone, or similar).
- Familiarity with LLM tooling: OpenAI API, LangChain, or equivalent frameworks.
- Experience with CI/CD pipelines (GitHub Actions) and containerised deployments (Docker).
- Excellent communication skills; comfortable working in a remote-first, async environment.

Nice to Have
- Contributions to open-source projects.
- Experience with Turborepo or other monorepo tooling.
- Familiarity with Playwright, Vitest, or pytest for automated testing.

Compensation & Benefits
- Salary range: $160,000 – $200,000 USD (depending on experience).
- 100% remote; flexible hours across US/EU time zones.
- Equity package, health / dental / vision insurance, $2,000 annual learning budget.
- Generous PTO policy + paid public holidays.

How to Apply
Send your resume and a brief note about your proudest engineering achievement to
careers@applypilot.io. We review applications on a rolling basis.
`.trim();
