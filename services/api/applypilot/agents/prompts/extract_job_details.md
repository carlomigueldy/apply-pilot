# Prompt: extract_job_details

**Version:** 1.0.0
**Output schema:** `applypilot.schemas.jobs.ExtractedJob`

---

## Purpose

Parse a raw job posting into structured, machine-readable fields that downstream
nodes (requirements extraction, evidence retrieval, fit scoring) can consume
without re-parsing free-form text.

---

## Inputs

All inputs are delivered via the `<<CONTEXT_JSON>>` block appended after this
prompt body.  Expected keys:

| Key | Type | Description |
|-----|------|-------------|
| `raw_job_post` | `string` | The verbatim job posting text (may contain HTML artefacts or markdown). |

---

## Output schema

Return a single JSON object conforming to `ExtractedJob`:

```json
{
  "company_name": "string | null",
  "role_title": "string | null",
  "work_arrangement": "remote | hybrid | onsite | unknown",
  "salary_text": "string | null",
  "timezone_text": "string | null",
  "location": "string | null",
  "summary": "string"
}
```

- `work_arrangement` MUST be one of the four enum values: `remote`, `hybrid`,
  `onsite`, or `unknown`.
- `summary` is REQUIRED and non-empty; write 1–3 sentences capturing the role
  essence.
- `salary_text` and `timezone_text` should preserve the exact phrasing from the
  posting when available; set to `null` when absent.

---

## Rules

1. Extract only what is explicitly stated in the posting.  Do NOT infer a
   company name from a job board URL or email domain.
2. `company_name` and `role_title` may be `null` if genuinely absent.
3. If multiple work arrangements are mentioned (e.g. "hybrid / remote"), choose
   the most specific or default to `hybrid`.
4. Keep `summary` factual — no editorialising.
5. Strip HTML tags and artefacts from all fields.
6. All string values should be trimmed of leading/trailing whitespace.

---

## Failure behavior

- If the `raw_job_post` is empty or unintelligible, return an `ExtractedJob`
  with `summary = "Unable to extract job details from the provided text."` and
  `null` for all optional fields and `work_arrangement = "unknown"`.
- Never raise an exception; always return a valid schema instance.

---

## Evidence requirements

None — this node operates purely on the raw job post text.

---

Grounding context follows immediately below in a `<<CONTEXT_JSON>>` block.
