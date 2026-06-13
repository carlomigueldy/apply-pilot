# Prompt: fit_analysis

**Version:** 1.0.0
**Output schema:** `applypilot.schemas.fit.FitAnalysis`

---

## Purpose

Score how well a candidate's demonstrated experience (retrieved evidence chunks)
matches each job requirement, producing an overall fit score, per-requirement
assessments, and strategic positioning guidance.

---

## Inputs

All inputs are delivered via the `<<CONTEXT_JSON>>` block appended after this
prompt body.  Expected keys:

| Key | Type | Description |
|-----|------|-------------|
| `requirements` | `list[object]` | Each object has `id`, `text`, `category`, `priority`. |
| `evidence` | `list[object]` | Each object has `requirement_id`, `evidence_chunk_id`, `profile_item_id`, `summary`, `confidence`. |
| `extracted_job` | `object` | `ExtractedJob` with company, role, summary. |
| `red_flags` | `list[string]` | Optional list of pre-identified concerns (may be empty). |

---

## Output schema

Return a single JSON object conforming to `FitAnalysis`:

```json
{
  "fit_score": 0,
  "summary": "string",
  "items": [
    {
      "requirement_id": "req-0",
      "match_level": "strong | partial | weak | missing | unknown",
      "explanation": "string",
      "evidence_chunk_ids": ["chunk-uuid-1"],
      "confidence": 0.85
    }
  ],
  "red_flags": ["string"],
  "positioning_strategy": "string"
}
```

Field constraints:
- `fit_score`: integer 0–100.
- `match_level` MUST be one of: `strong`, `partial`, `weak`, `missing`,
  `unknown`.
- `confidence`: float 0.0–1.0.
- `evidence_chunk_ids`: **For `strong` or `partial` matches, this list MUST be
  non-empty.**  Include the `evidence_chunk_id` values from the matching
  evidence entries.
- `evidence_chunk_ids` MAY be empty only for `weak`, `missing`, or `unknown`
  matches.

---

## Match level definitions

| Level | Meaning |
|-------|---------|
| `strong` | Candidate has direct, demonstrated experience matching the requirement.  Confidence ≥ 0.7.  **MUST cite evidence_chunk_ids.** |
| `partial` | Candidate has related or adjacent experience.  Confidence 0.4–0.7.  **MUST cite evidence_chunk_ids.** |
| `weak` | Tangential or inferential match; low confidence.  Confidence < 0.4.  Evidence optional. |
| `missing` | No matching evidence found.  Evidence empty. |
| `unknown` | Cannot be determined from available information. |

**CRITICAL RULE: For strong/partial matches, include evidence_chunk_ids; never
claim experience absent from the provided evidence.**

---

## Fit score formula

Use the following weighted formula:

```
score = round(
    100 * (
        (strong_count * 1.0 + partial_count * 0.5 + weak_count * 0.1)
        / max(total_requirements, 1)
    )
)
```

Apply a boost of +5 for each `must_have` requirement with a `strong` match
(capped at 100).

---

## Rules

1. Produce exactly one `FitAnalysisItem` per requirement in the context.
2. Base EVERY assessment on the supplied evidence.  Do NOT hallucinate skills or
   experience.
3. `explanation` should be 1–2 sentences referencing actual evidence snippets.
4. `summary` should be 2–4 sentences providing an overall candidate assessment.
5. `positioning_strategy` should be 2–4 sentences advising how to frame the
   application given the fit profile (strengths first, gaps acknowledged).
6. `red_flags` should list genuine concerns (gaps in must-have requirements,
   role level mismatch, location constraints, etc.).  Carry forward any
   `red_flags` provided in the context; add new ones if discovered.

---

## Failure behavior

- If `requirements` is empty, return a `FitAnalysis` with `fit_score = 0`,
  empty `items`, and `summary = "No requirements provided for analysis."`.
- If `evidence` is empty, all items MUST have `match_level = "missing"` and
  empty `evidence_chunk_ids`.
- Never raise; always return a valid schema instance that satisfies the
  model validator (no strong/partial without evidence).

---

## Evidence requirements

**Required.** This node consumes pre-retrieved evidence chunks keyed by
`requirement_id`.  The calling graph node must have already run semantic search
over the candidate's profile.  Do not attempt to fetch additional evidence.

---

Grounding context follows immediately below in a `<<CONTEXT_JSON>>` block.
