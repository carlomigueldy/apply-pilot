# Prompt: draft_bundle

**Version:** 1.0.0
**Output schema:** `applypilot.schemas.drafts.DraftBundle`

---

## Purpose

Generate a complete bundle of application materials tailored to the candidate
and the specific job.  Each draft is grounded in the candidate's evidence and
the job context so that every sentence can be verified against real experience.

---

## Inputs

All inputs are delivered via the `<<CONTEXT_JSON>>` block appended after this
prompt body.  Expected keys:

| Key | Type | Description |
|-----|------|-------------|
| `extracted_job` | `object` | `ExtractedJob` (company_name, role_title, summary, work_arrangement). |
| `fit_summary` | `string` | 2–4 sentence summary from the fit analysis. |
| `fit_score` | `integer` | 0–100 overall fit score. |
| `top_evidence` | `list[object]` | Top evidence snippets: `{evidence_chunk_id, title, snippet, source_type}`. |
| `positioning_strategy` | `string` | Advice from the fit analysis on how to frame the application. |
| `draft_types` | `list[string]` | Which draft types to generate (default: all seven). |
| `tone` | `string` | Desired tone: `direct`, `warm_professional`, `confident`, `concise`. |
| `length` | `string` | Desired length: `short`, `medium`, `detailed`. |
| `red_flags` | `list[string]` | Concerns to acknowledge or work around in the drafts. |

---

## Output schema

Return a single JSON object conforming to `DraftBundle`:

```json
{
  "drafts": [
    {
      "type": "recruiter_reply | cover_email | resume_summary | resume_bullets | interview_talking_points | salary_response | self_introduction",
      "title": "string",
      "body": "string"
    }
  ]
}
```

Field constraints:
- `type` MUST be one of the seven `DraftType` enum values:
  `recruiter_reply`, `cover_email`, `resume_summary`, `resume_bullets`,
  `interview_talking_points`, `salary_response`, `self_introduction`.
- Produce one `DraftItem` for each type listed in `draft_types`.
- `title` should be a concise heading (≤ 80 characters).
- `body` must be non-empty and reference the company name, role title, and at
  least one piece of evidence.

---

## Draft type guidelines

| Type | Length guidance | Key elements |
|------|-----------------|--------------|
| `recruiter_reply` | 3–5 sentences | Enthusiasm, top 2 strengths, availability |
| `cover_email` | 3–4 paragraphs | Hook, evidence-backed strengths, cultural fit, CTA |
| `resume_summary` | 3–5 sentences | Who you are, key skills, career highlight, value prop |
| `resume_bullets` | 5–8 bullet points | STAR-format achievements referencing actual evidence |
| `interview_talking_points` | 4–6 bullet points | Prepared stories mapped to role requirements |
| `salary_response` | 2–4 sentences | Anchored range, evidence-backed justification |
| `self_introduction` | 3–5 sentences | 30-second pitch covering background, skills, fit |

Apply the requested `tone` and `length` modifiers:
- `short`: cut to essentials; `medium`: standard; `detailed`: expand with more
  evidence citations.
- `direct`: plain statements; `warm_professional`: friendly yet formal;
  `confident`: assertive; `concise`: remove all filler.

---

## Rules

1. Every claim in every draft MUST be backed by the provided `top_evidence`.
   Do NOT invent achievements or skills.
2. Reference the company name and role title naturally in each draft.
3. Acknowledge `red_flags` where appropriate (e.g. a gap in a must-have
   requirement) — never hide weaknesses that a recruiter will spot; instead
   frame them positively.
4. Do not reproduce the evidence verbatim — paraphrase and contextualise.
5. Use first-person ("I") throughout.
6. If `salary_text` is available in the extracted job, reference it in the
   `salary_response` draft.

---

## Failure behavior

- If `top_evidence` is empty, generate drafts that focus on the role fit and
  transferable skills inferred from `fit_summary`; add a note at the end of
  each draft body: "[Evidence grounding unavailable — review before sending.]"
- If a `draft_type` is listed in `draft_types` but cannot be meaningfully
  produced (e.g. `salary_response` with no salary context), still produce a
  placeholder draft with a clear note.
- Never raise; always return a valid `DraftBundle`.

---

## Evidence requirements

**Required.** `top_evidence` must be pre-populated by the evidence retrieval
node.  This prompt does not perform its own retrieval.

---

Grounding context follows immediately below in a `<<CONTEXT_JSON>>` block.
