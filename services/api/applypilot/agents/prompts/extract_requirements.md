# Prompt: extract_requirements

**Version:** 1.0.0
**Output schema:** `applypilot.schemas.jobs.JobRequirementList`

---

## Purpose

Identify and categorise the discrete requirements expressed in a job posting so
that they can be independently matched against the candidate's profile evidence.

---

## Inputs

All inputs are delivered via the `<<CONTEXT_JSON>>` block appended after this
prompt body.  Expected keys:

| Key | Type | Description |
|-----|------|-------------|
| `raw_job_post` | `string` | The verbatim job posting text. |
| `extracted_job` | `object` | The `ExtractedJob` already produced (company_name, role_title, summary, etc.). |

---

## Output schema

Return a single JSON object conforming to `JobRequirementList`:

```json
{
  "requirements": [
    {
      "id": "req-0",
      "text": "string",
      "category": "frontend | backend | ai | web3 | devops | soft_skill | domain | other",
      "priority": "must_have | nice_to_have | unknown"
    }
  ]
}
```

Field constraints:
- `id` MUST follow the pattern `req-{N}` where N is the 0-based index (e.g.
  `req-0`, `req-1`, …).
- `text` should be the requirement as a concise, self-contained sentence.
- `category` MUST be one of: `frontend`, `backend`, `ai`, `web3`, `devops`,
  `soft_skill`, `domain`, `other`.
- `priority` MUST be one of: `must_have`, `nice_to_have`, `unknown`.

---

## Categorisation guidance

| Category | Keywords / signals |
|----------|-------------------|
| `frontend` | React, Vue, Angular, CSS, HTML, TypeScript (UI context), mobile, iOS, Android |
| `backend` | Python, Node.js, Java, Go, Rust, API, REST, GraphQL, microservices |
| `ai` | ML, machine learning, LLM, embeddings, RAG, NLP, model training, AI |
| `web3` | blockchain, Solidity, Ethereum, DeFi, smart contracts, NFT, wallet |
| `devops` | Docker, Kubernetes, CI/CD, AWS, GCP, Azure, Terraform, infrastructure |
| `soft_skill` | communication, leadership, collaboration, mentoring, cross-functional |
| `domain` | finance, healthcare, legal, e-commerce, SaaS, industry-specific knowledge |
| `other` | anything not clearly fitting above categories |

## Priority guidance

| Priority | Signals |
|----------|---------|
| `must_have` | "required", "must have", "essential", "3+ years", mandatory bullets |
| `nice_to_have` | "preferred", "nice to have", "bonus", "plus", "desired" |
| `unknown` | No explicit qualifier; use judgement or default to `unknown` |

---

## Rules

1. Produce between 3 and 12 requirements.  Merge near-duplicate requirements
   (e.g. "5 years Python" and "Python proficiency" become one).
2. Each requirement should be a distinct, testable criterion.
3. Do NOT invent requirements not present in the posting.
4. Soft skills and cultural fit items count as requirements.
5. If the posting is a single paragraph with no clear list structure, infer
   requirements from key phrases.

---

## Failure behavior

- If the posting contains no discernible requirements, return a
  `JobRequirementList` with a single requirement:
  `{ "id": "req-0", "text": "No specific requirements identified.", "category": "other", "priority": "unknown" }`.
- Never return an empty `requirements` list.
- Never raise; always return a valid schema instance.

---

## Evidence requirements

None — this node operates on the raw job post and the previously extracted job
metadata only.

---

Grounding context follows immediately below in a `<<CONTEXT_JSON>>` block.
