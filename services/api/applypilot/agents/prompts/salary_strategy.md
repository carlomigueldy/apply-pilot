# Prompt: salary_strategy

**Version:** 1.0.0
**Output schema:** `applypilot.schemas.drafts.DraftItem` (type = `salary_response`)

---

## Purpose

Craft a single, evidence-backed salary negotiation response that positions the
candidate's compensation expectation against the market context and their
demonstrated value, without being either too timid or overreaching.

---

## Inputs

All inputs are delivered via the `<<CONTEXT_JSON>>` block appended after this
prompt body.  Expected keys:

| Key | Type | Description |
|-----|------|-------------|
| `extracted_job` | `object` | `ExtractedJob` including `salary_text` (may be null), `company_name`, `role_title`. |
| `fit_score` | `integer` | 0–100; higher scores justify stronger anchoring. |
| `top_evidence` | `list[object]` | Evidence snippets: `{evidence_chunk_id, title, snippet, source_type}`. |
| `positioning_strategy` | `string` | Fit analysis advice on candidate strengths. |
| `candidate_salary_floor` | `string \| null` | Candidate's minimum acceptable compensation (from profile), if available. |
| `tone` | `string` | One of: `direct`, `warm_professional`, `confident`, `concise`. |

---

## Output schema

Return a single JSON object conforming to `DraftItem`:

```json
{
  "type": "salary_response",
  "title": "string",
  "body": "string"
}
```

- `type` MUST be `"salary_response"`.
- `title`: concise heading ≤ 80 characters, e.g. `"Salary Expectation —
  {Role Title} at {Company}"`.
- `body`: the full negotiation response (2–5 sentences for `concise`/`direct`
  tones; up to 2 short paragraphs for `warm_professional`/`confident`).

---

## Strategy guidelines

1. **Anchor high, justify with evidence.** Open with a specific range or figure,
   then immediately cite 1–2 evidence snippets that demonstrate the value
   delivered.
2. **Reference the posting salary if provided.** If `salary_text` is present,
   align the anchor to or above the top of the advertised range.
3. **Acknowledge flexibility.** End with a statement of openness to discuss
   total compensation (equity, benefits, etc.).
4. **Fit score modulation.**
   - fit_score ≥ 80: anchor at or above market; emphasise unique value.
   - fit_score 60–79: anchor at market; highlight evidence of impact.
   - fit_score < 60: anchor at market or slightly below; lean on growth
     potential and adjacent strengths.
5. **Tone application.**
   - `direct`: "My expectation is $X–$Y based on …"
   - `warm_professional`: "Given my background in …, I'd be looking for …"
   - `confident`: "Based on the value I bring …, I'm targeting …"
   - `concise`: One sentence anchor + one sentence rationale.

---

## Rules

1. Never fabricate salary figures — derive from `salary_text` or leave as a
   range placeholder `"$[LOW]–$[HIGH]"` if no data is available.
2. Ground every justification in `top_evidence`; do not invent achievements.
3. Do not reveal `candidate_salary_floor` in the response body.
4. Use first-person ("I").
5. Keep the response professional — no ultimatums or aggressive language.

---

## Failure behavior

- If `salary_text` is null and `candidate_salary_floor` is null and
  `top_evidence` is empty, produce a generic placeholder:
  `"I'm targeting a competitive range aligned with the market rate for this
  role and level.  I'm happy to discuss the full compensation package."`.
- Never raise; always return a valid `DraftItem`.

---

## Evidence requirements

**Required.** `top_evidence` should be pre-populated by the evidence retrieval
node.  At least one snippet grounding the salary justification is expected.

---

Grounding context follows immediately below in a `<<CONTEXT_JSON>>` block.
