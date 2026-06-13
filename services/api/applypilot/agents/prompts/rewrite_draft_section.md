# Prompt: rewrite_draft_section

**Version:** 1.0.0
**Output schema:** `applypilot.schemas.drafts.DraftItem`

---

## Purpose

Rewrite or refine a single draft section based on reviewer instructions, a new
tone, or a new length target — while preserving grounding in the candidate's
actual evidence and not introducing fabricated claims.

---

## Inputs

All inputs are delivered via the `<<CONTEXT_JSON>>` block appended after this
prompt body.  Expected keys:

| Key | Type | Description |
|-----|------|-------------|
| `draft_type` | `string` | The `DraftType` of the section being rewritten. |
| `original_body` | `string` | The existing draft text to revise. |
| `instructions` | `string \| null` | Free-form reviewer notes (e.g. "make it shorter", "mention Python more"). |
| `tone` | `string \| null` | Desired tone: `direct`, `warm_professional`, `confident`, `concise`. |
| `length` | `string \| null` | Desired length: `short`, `medium`, `detailed`. |
| `extracted_job` | `object` | `ExtractedJob` for role context. |
| `top_evidence` | `list[object]` | Evidence snippets: `{evidence_chunk_id, title, snippet, source_type}`. |
| `fit_summary` | `string \| null` | Optional fit summary for additional context. |

---

## Output schema

Return a single JSON object conforming to `DraftItem`:

```json
{
  "type": "string",
  "title": "string",
  "body": "string"
}
```

- `type` MUST equal the `draft_type` provided in the context (one of the seven
  `DraftType` enum values).
- `title` should be updated if the instructions suggest a new heading; otherwise
  preserve or slightly refine the original.
- `body` must be the rewritten draft content — non-empty and grounded in
  `top_evidence`.

---

## Rewrite guidelines

### Instruction handling

- Apply reviewer `instructions` literally where unambiguous.
- If instructions conflict with evidence grounding (e.g. "add 10 years of
  Kubernetes experience" when no evidence supports this), write the closest
  supportable version and append an inline note:
  `"[Note: revised to align with available evidence.]"`

### Tone application

If a new `tone` is specified, transform the writing style:
- `direct`: active voice, declarative statements, no hedging.
- `warm_professional`: polite, slightly warm opener, formal but not stiff.
- `confident`: assertive language, emphasise unique value delivered.
- `concise`: strip all filler words; every sentence must carry information.

### Length application

If a new `length` is specified:
- `short`: cut to the 3 most important points; ≤ 3 sentences or 5 bullets.
- `medium`: retain main structure; aim for standard draft lengths per type.
- `detailed`: expand with additional evidence citations and context.

---

## Rules

1. Preserve every factual claim that IS supported by `top_evidence`; remove or
   soften claims that are NOT supported.
2. Maintain first-person ("I") throughout.
3. Do not change the `draft_type` — the returned `type` MUST match the input
   `draft_type`.
4. Reference company name and role title where natural.
5. If `instructions` is null and `tone`/`length` are unchanged, return a lightly
   polished version of the original (fix grammar/clarity only).

---

## Failure behavior

- If `original_body` is empty, treat this as a fresh generation request and
  produce a new draft using the same guidelines as `draft_bundle.md` for the
  given `draft_type`.
- If `top_evidence` is empty, revise the original_body for tone/length/style
  only; do not add new factual claims; append:
  `"[Evidence grounding unavailable — review before sending.]"`
- Never raise; always return a valid `DraftItem`.

---

## Evidence requirements

**Required for factual preservation.** `top_evidence` must be provided so the
rewrite node can verify which claims are grounded.  New claims must only be
added if supported by a supplied evidence snippet.

---

Grounding context follows immediately below in a `<<CONTEXT_JSON>>` block.
