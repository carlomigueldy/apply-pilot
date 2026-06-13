"""Deterministic, network-free LLM provider for tests and local development.

:class:`FakeLLMProvider` produces schema-valid, *grounded* structured outputs by
reading the ``CONTEXT_JSON`` block embedded in the prompt (see
:mod:`applypilot.agents.grounding`). Given the same ``(prompt, schema)`` it always
returns an identical result — no time, no randomness, no I/O.

The canonical :class:`~applypilot.agents.llm.embeddings.FakeEmbeddingProvider` is
re-exported here so callers can import both fakes from one module.
"""

from __future__ import annotations

import re
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from applypilot.agents.grounding import parse_context_block, strip_context_block

# Re-exported so ``from applypilot.agents.llm.fake import FakeEmbeddingProvider``
# keeps working and isinstance checks line up with the factory's return value.
from applypilot.agents.llm.embeddings import FakeEmbeddingProvider
from applypilot.schemas.drafts import DraftBundle, DraftItem
from applypilot.schemas.enums import (
    DraftLength,
    DraftType,
    MatchLevel,
    RequirementCategory,
    RequirementPriority,
    WorkArrangement,
)
from applypilot.schemas.evidence import EvidenceMatch, EvidenceMatchList
from applypilot.schemas.fit import FitAnalysis, FitAnalysisItem
from applypilot.schemas.jobs import ExtractedJob, JobRequirement, JobRequirementList

__all__ = ["FakeEmbeddingProvider", "FakeLLMProvider"]

_T = TypeVar("_T", bound=BaseModel)

# --- Heuristic vocabularies (ordered; first match wins for determinism) --------

# Category keyword buckets, checked in this fixed priority order.
_CATEGORY_KEYWORDS: tuple[tuple[RequirementCategory, tuple[str, ...]], ...] = (
    (
        RequirementCategory.WEB3,
        ("web3", "solidity", "ethereum", "blockchain", "smart contract", "onchain", "evm", "defi"),
    ),
    (
        RequirementCategory.AI,
        ("machine learning", "langchain", "embedding", "llm", "openai", "pytorch",
         "tensorflow", "nlp", "ai", "rag"),
    ),
    (
        RequirementCategory.FRONTEND,
        ("frontend", "front-end", "react", "vue", "angular", "next.js", "nextjs",
         "tailwind", "css", "html", "typescript", "ui", "ux"),
    ),
    (
        RequirementCategory.DEVOPS,
        ("devops", "kubernetes", "docker", "ci/cd", "cicd", "terraform", "aws",
         "gcp", "azure", "infrastructure", "deployment", "observability"),
    ),
    (
        RequirementCategory.BACKEND,
        ("backend", "back-end", "api", "server", "database", "sql", "postgres",
         "python", "node", "django", "fastapi", "microservice", "golang", "rust"),
    ),
    (
        RequirementCategory.SOFT_SKILL,
        ("communication", "collaborat", "leadership", "mentor", "stakeholder",
         "teamwork", "team player", "ownership"),
    ),
    (
        RequirementCategory.DOMAIN,
        ("fintech", "healthcare", "e-commerce", "ecommerce", "saas", "b2b", "b2c",
         "compliance", "domain"),
    ),
)

_MUST_HAVE_MARKERS: tuple[str, ...] = ("required", "must have", "must-have", "must ", "essential")

_BULLET_RE = re.compile(r"^\s*[-*•▪◦‣·]\s+")
_REQUIREMENT_HINTS: tuple[str, ...] = (
    "experience", "years", "proficient", "proficiency", "knowledge of", "familiar",
    "expertise", "skilled", "strong", "ability to", "required", "must",
)

# Per-match-level contribution to the weighted fit score.
_LEVEL_SCORE: dict[MatchLevel, float] = {
    MatchLevel.STRONG: 1.0,
    MatchLevel.PARTIAL: 0.6,
    MatchLevel.WEAK: 0.3,
    MatchLevel.MISSING: 0.0,
    MatchLevel.UNKNOWN: 0.0,
}

# Default ordered draft types when a request does not specify them.
_DEFAULT_DRAFT_TYPES: tuple[DraftType, ...] = (
    DraftType.RECRUITER_REPLY,
    DraftType.COVER_EMAIL,
    DraftType.RESUME_SUMMARY,
    DraftType.RESUME_BULLETS,
    DraftType.INTERVIEW_TALKING_POINTS,
    DraftType.SALARY_RESPONSE,
    DraftType.SELF_INTRODUCTION,
)


class FakeLLMProvider:
    """A deterministic, offline :class:`~applypilot.agents.llm.base.LLMProvider`.

    ``structured`` branches on the requested ``schema`` and synthesises a
    grounded, schema-valid instance from the prompt's ``CONTEXT_JSON`` block.
    Critically, :class:`~applypilot.schemas.fit.FitAnalysis` outputs ground their
    ``evidence_chunk_ids`` from the supplied evidence so the schema's
    strong/partial validator always passes.

    Args:
        settings: Optional settings override; ``model`` is taken from
            ``settings.llm_model``. Defaults to the cached global settings.
    """

    name: str = "fake"

    def __init__(self, settings: Any | None = None) -> None:
        from applypilot.core.config import get_settings

        s = settings or get_settings()
        self.model: str = s.llm_model

    # -- Public protocol surface ------------------------------------------------

    def structured(self, prompt: str, schema: type[_T]) -> _T:
        """Return a deterministic, grounded instance of *schema*."""
        context = parse_context_block(prompt)
        result: BaseModel

        if schema is ExtractedJob:
            result = self._extracted_job(prompt, context)
        elif schema is JobRequirementList:
            result = self._job_requirements(prompt, context)
        elif schema is FitAnalysis:
            result = self._fit_analysis(context)
        elif schema is DraftBundle:
            result = self._draft_bundle(context)
        elif schema is EvidenceMatchList:
            result = self._evidence_matches(context)
        else:
            result = self._generic(schema)

        return cast("_T", result)

    def text(self, prompt: str) -> str:
        """Return a short, deterministic completion derived from *prompt*."""
        instruction = " ".join(strip_context_block(prompt).split())
        head = instruction[:200]
        return f"[fake:{self.model}] {head}" if head else f"[fake:{self.model}] (empty prompt)"

    # -- ExtractedJob -----------------------------------------------------------

    def _extracted_job(self, prompt: str, context: dict[str, Any]) -> ExtractedJob:
        raw = str(context.get("raw_job_post") or "") or strip_context_block(prompt)

        company_name = _extract_labelled(raw, "company", "employer", "organization", "org")
        role_title = _extract_labelled(raw, "role", "title", "position", "job title")
        if role_title is None:
            role_title = _first_nonempty_line(raw)

        salary_text = _extract_labelled(raw, "salary", "compensation", "pay", "rate")
        if salary_text is None:
            salary_text = _search(r"\$\s?\d[\d,. ]*(?:k|K)?(?:\s*[-–]\s*\$?\d[\d,. ]*(?:k|K)?)?", raw)

        timezone_text = _extract_labelled(raw, "timezone", "time zone", "tz")
        if timezone_text is None:
            timezone_text = _search(
                r"\b(?:UTC|GMT|PST|PDT|EST|EDT|CST|CDT|MST|MDT|CET|CEST|IST|BST)"
                r"(?:[+-]\d{1,2}(?::\d{2})?)?\b",
                raw,
            )

        location = _extract_labelled(raw, "location", "based in", "located")

        collapsed = " ".join(raw.split())
        summary = collapsed[:200] if collapsed else "No job description was provided."

        return ExtractedJob(
            company_name=company_name,
            role_title=role_title,
            work_arrangement=_work_arrangement(raw),
            salary_text=salary_text,
            timezone_text=timezone_text,
            location=location,
            summary=summary,
        )

    # -- JobRequirementList -----------------------------------------------------

    def _job_requirements(self, prompt: str, context: dict[str, Any]) -> JobRequirementList:
        raw = str(context.get("raw_job_post") or "") or strip_context_block(prompt)
        candidates = _requirement_candidates(raw)

        requirements = [
            JobRequirement(
                id=f"req-{i}",
                text=text,
                category=_guess_category(text),
                priority=_guess_priority(text),
            )
            for i, text in enumerate(candidates, start=1)
        ]
        return JobRequirementList(requirements=requirements)

    # -- FitAnalysis (the linchpin) --------------------------------------------

    def _fit_analysis(self, context: dict[str, Any]) -> FitAnalysis:
        requirements = _as_dict_list(context.get("requirements"))
        evidence = _as_dict_list(context.get("evidence"))
        red_flags = [str(flag) for flag in (context.get("red_flags") or [])]

        evidence_by_req: dict[str, list[dict[str, Any]]] = {}
        for entry in evidence:
            rid = str(entry.get("requirement_id", ""))
            if rid:
                evidence_by_req.setdefault(rid, []).append(entry)

        items: list[FitAnalysisItem] = []
        weighted_sum = 0.0
        weight_total = 0.0

        for req in requirements:
            rid = str(req.get("id", ""))
            if not rid:
                continue
            ev = evidence_by_req.get(rid, [])
            match_level, confidence, chunk_ids = _assess_match(ev)

            items.append(
                FitAnalysisItem(
                    requirement_id=rid,
                    match_level=match_level,
                    explanation=_explain_match(req, match_level, ev),
                    evidence_chunk_ids=chunk_ids,
                    confidence=confidence,
                )
            )

            weight = _priority_weight(req)
            weighted_sum += weight * _LEVEL_SCORE[match_level]
            weight_total += weight

        fit_score = round(100 * weighted_sum / weight_total) if weight_total else 0

        return FitAnalysis(
            fit_score=fit_score,
            summary=_fit_summary(items, fit_score),
            items=items,
            red_flags=red_flags,
            positioning_strategy=_positioning_strategy(items, requirements, context),
        )

    # -- DraftBundle ------------------------------------------------------------

    def _draft_bundle(self, context: dict[str, Any]) -> DraftBundle:
        extracted = context.get("extracted_job") or {}
        company = _coalesce(extracted.get("company_name"), context.get("company_name"), "the company")
        role = _coalesce(extracted.get("role_title"), context.get("role_title"), "the role")

        tone = str(context.get("tone") or "warm_professional")
        length = _coerce_length(context.get("length"))

        fit = context.get("fit_analysis") or {}
        fit_summary = str(context.get("fit_summary") or fit.get("summary") or "")

        evidence = _as_dict_list(context.get("evidence") or context.get("top_evidence"))
        snippets = [str(e.get("summary", "")).strip() for e in evidence if e.get("summary")][:3]

        draft_types = _resolve_draft_types(context.get("draft_types"))

        drafts = [
            _build_draft(dtype, company, role, tone, length, fit_summary, snippets)
            for dtype in draft_types
        ]
        return DraftBundle(drafts=drafts)

    # -- EvidenceMatchList ------------------------------------------------------

    def _evidence_matches(self, context: dict[str, Any]) -> EvidenceMatchList:
        matches: list[EvidenceMatch] = []
        for entry in _as_dict_list(context.get("evidence")):
            rid = str(entry.get("requirement_id", ""))
            pid = str(entry.get("profile_item_id", ""))
            cid = str(entry.get("evidence_chunk_id", ""))
            if not (rid and pid and cid):
                continue
            matches.append(
                EvidenceMatch(
                    requirement_id=rid,
                    profile_item_id=pid,
                    evidence_chunk_id=cid,
                    summary=str(entry.get("summary", "")) or f"Evidence for {rid}.",
                    confidence=_clamp_unit(entry.get("confidence", 0.7)),
                )
            )
        return EvidenceMatchList(matches=matches)

    # -- Generic fallback -------------------------------------------------------

    def _generic(self, schema: type[_T]) -> _T:
        """Build a minimal valid instance for an otherwise-unhandled schema."""
        values: dict[str, Any] = {}
        for field_name, field in schema.model_fields.items():
            if not field.is_required():
                continue
            values[field_name] = _default_for_annotation(field.annotation)
        try:
            return schema(**values)
        except Exception as exc:  # noqa: BLE001 - re-raised with actionable context
            raise ValueError(
                f"FakeLLMProvider cannot synthesise a minimal instance of "
                f"{schema.__name__!r}; add an explicit branch in fake.py."
            ) from exc


# --- Module-level deterministic helpers ----------------------------------------


def _extract_labelled(text: str, *labels: str) -> str | None:
    """Return the value following ``Label:``/``Label -`` for the first matching label."""
    for label in labels:
        match = re.search(
            rf"^\s*{re.escape(label)}\s*[:\-–]\s*(.+?)\s*$",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def _first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return None


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).strip() if match else None


def _work_arrangement(text: str) -> WorkArrangement:
    lowered = text.lower()
    if "hybrid" in lowered:
        return WorkArrangement.HYBRID
    if "remote" in lowered:
        return WorkArrangement.REMOTE
    if any(token in lowered for token in ("onsite", "on-site", "on site", "in office", "in-office")):
        return WorkArrangement.ONSITE
    return WorkArrangement.UNKNOWN


def _requirement_candidates(raw: str) -> list[str]:
    """Extract 3-6 deterministic requirement strings from a raw job post."""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    primary: list[str] = []
    secondary: list[str] = []
    seen: set[str] = set()

    for line in lines:
        cleaned = _BULLET_RE.sub("", line).strip()
        if not cleaned or len(cleaned) < 3:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        is_bullet = bool(_BULLET_RE.match(line))
        is_hinted = any(hint in key for hint in _REQUIREMENT_HINTS)
        if is_bullet or is_hinted:
            primary.append(cleaned)
            seen.add(key)
        else:
            secondary.append(cleaned)

    candidates = primary[:6]
    # Backfill toward a minimum of 3 from remaining non-empty lines, deterministically.
    for cleaned in secondary:
        if len(candidates) >= 3:
            break
        key = cleaned.lower()
        if key in seen:
            continue
        candidates.append(cleaned)
        seen.add(key)

    return candidates[:6]


def _keyword_present(keyword: str, lowered: str) -> bool:
    """Whether *keyword* appears in *lowered* as a standalone token.

    Boundary-aware so short keywords like ``"ui"`` or ``"ai"`` do not match
    inside larger words (e.g. ``"required"`` must not count as ``"ui"``).
    """
    pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
    return re.search(pattern, lowered) is not None


def _guess_category(text: str) -> RequirementCategory:
    lowered = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(_keyword_present(keyword, lowered) for keyword in keywords):
            return category
    return RequirementCategory.OTHER


def _guess_priority(text: str) -> RequirementPriority:
    lowered = text.lower()
    if any(marker in lowered for marker in _MUST_HAVE_MARKERS):
        return RequirementPriority.MUST_HAVE
    return RequirementPriority.NICE_TO_HAVE


def _assess_match(
    evidence: list[dict[str, Any]],
) -> tuple[MatchLevel, float, list[str]]:
    """Map a requirement's evidence to (match_level, confidence, grounded chunk ids)."""
    chunk_ids = [
        str(e["evidence_chunk_id"]) for e in evidence if e.get("evidence_chunk_id")
    ]

    if not evidence or not chunk_ids:
        # No relevant, groundable evidence → an honest gap.
        return MatchLevel.MISSING, 0.2, []

    confidences = [_clamp_unit(e["confidence"]) for e in evidence if "confidence" in e]
    best = max(confidences) if confidences else 0.6

    # Strong: corroborated by multiple chunks, or a single high-relevance hit.
    if len(chunk_ids) >= 2 or best >= 0.7:
        return MatchLevel.STRONG, round(min(0.95, max(0.8, best)), 2), chunk_ids
    # Partial: a single, moderately-relevant piece of evidence.
    if best >= 0.5:
        return MatchLevel.PARTIAL, round(best, 2), chunk_ids
    # Weak: thin / low-relevance evidence — related background, not a direct match.
    return MatchLevel.WEAK, round(max(0.3, best), 2), chunk_ids


def _priority_weight(req: dict[str, Any]) -> float:
    priority = str(req.get("priority") or "").lower()
    if priority == RequirementPriority.MUST_HAVE.value:
        return 1.0
    if priority == RequirementPriority.NICE_TO_HAVE.value:
        return 0.5
    return 0.75


def _explain_match(
    req: dict[str, Any], match_level: MatchLevel, evidence: list[dict[str, Any]]
) -> str:
    text = str(req.get("text") or req.get("id") or "this requirement")
    if match_level == MatchLevel.STRONG:
        cited = next((str(e.get("summary")) for e in evidence if e.get("summary")), "")
        tail = f" Backed by: {cited}" if cited else ""
        return f"Strong, directly demonstrated match for '{text}'.{tail}"
    if match_level == MatchLevel.PARTIAL:
        return f"Partial match for '{text}'; some relevant evidence but not comprehensive."
    if match_level == MatchLevel.WEAK:
        return f"Weak signal for '{text}'; related background but no concrete evidence."
    return f"No evidence found for '{text}'; treat as a gap to address."


def _fit_summary(items: list[FitAnalysisItem], fit_score: int) -> str:
    if not items:
        return f"No requirements were available to assess. Fit score {fit_score}/100."
    strong = sum(1 for i in items if i.match_level == MatchLevel.STRONG)
    partial = sum(1 for i in items if i.match_level == MatchLevel.PARTIAL)
    gaps = sum(1 for i in items if i.match_level in (MatchLevel.WEAK, MatchLevel.MISSING))
    return (
        f"Overall fit score {fit_score}/100 across {len(items)} requirements: "
        f"{strong} strong, {partial} partial, and {gaps} gap(s)."
    )


def _positioning_strategy(
    items: list[FitAnalysisItem],
    requirements: list[dict[str, Any]],
    context: dict[str, Any],
) -> str:
    text_by_id = {str(r.get("id", "")): str(r.get("text", "")) for r in requirements}
    strong_texts = [
        text_by_id.get(i.requirement_id, i.requirement_id)
        for i in items
        if i.match_level == MatchLevel.STRONG
    ][:3]
    gap_texts = [
        text_by_id.get(i.requirement_id, i.requirement_id)
        for i in items
        if i.match_level in (MatchLevel.WEAK, MatchLevel.MISSING)
    ][:2]

    role = str((context.get("extracted_job") or {}).get("role_title") or "the role")

    lead = (
        f"Lead with proven strengths: {', '.join(strong_texts)}."
        if strong_texts
        else "Emphasise transferable strengths and demonstrated impact."
    )
    address = (
        f" Proactively address gaps around {', '.join(gap_texts)} with adjacent experience."
        if gap_texts
        else " No significant gaps to address."
    )
    return f"For {role}: {lead}{address}"


def _resolve_draft_types(raw: Any) -> list[DraftType]:
    if not raw:
        return list(_DEFAULT_DRAFT_TYPES)
    resolved: list[DraftType] = []
    for value in raw:
        try:
            dtype = value if isinstance(value, DraftType) else DraftType(str(value))
        except ValueError:
            continue
        if dtype not in resolved:
            resolved.append(dtype)
    return resolved or list(_DEFAULT_DRAFT_TYPES)


def _coerce_length(value: Any) -> DraftLength:
    if isinstance(value, DraftLength):
        return value
    try:
        return DraftLength(str(value))
    except ValueError:
        return DraftLength.MEDIUM


def _build_draft(
    dtype: DraftType,
    company: str,
    role: str,
    tone: str,
    length: DraftLength,
    fit_summary: str,
    snippets: list[str],
) -> DraftItem:
    primary = snippets[0] if snippets else "directly relevant experience"
    secondary = snippets[1] if len(snippets) > 1 else "a track record of measurable impact"
    evidence_line = f"In particular, {primary}, and {secondary}."

    bodies: dict[DraftType, tuple[str, str]] = {
        DraftType.RECRUITER_REPLY: (
            f"Re: {role} at {company}",
            f"Hi,\n\nThanks for reaching out about the {role} role at {company} — "
            f"I'm genuinely interested. {evidence_line} I'd welcome a quick call to "
            f"explore how I can contribute.\n\nBest regards",
        ),
        DraftType.COVER_EMAIL: (
            f"Application for {role} at {company}",
            f"Dear Hiring Team,\n\nI'm excited to apply for the {role} position at "
            f"{company}. {evidence_line} I'm confident my background maps closely to "
            f"what you're looking for and would love to discuss further.\n\nSincerely",
        ),
        DraftType.RESUME_SUMMARY: (
            "Professional Summary",
            f"Results-driven candidate targeting the {role} role at {company}. "
            f"{evidence_line}",
        ),
        DraftType.RESUME_BULLETS: (
            "Resume Bullets",
            f"- Delivered work aligned with {role} at {company}: {primary}.\n"
            f"- Demonstrated {secondary}.\n"
            f"- Consistently translated requirements into measurable outcomes.",
        ),
        DraftType.INTERVIEW_TALKING_POINTS: (
            "Interview Talking Points",
            f"- Why {company}: alignment with the {role} mandate.\n"
            f"- Strongest proof point: {primary}.\n"
            f"- Supporting evidence: {secondary}.\n"
            f"- Questions to ask about team, scope, and success metrics.",
        ),
        DraftType.SALARY_RESPONSE: (
            "Salary Discussion",
            f"Thank you for sharing the details for the {role} role. I'm flexible and "
            f"focused on the overall fit; given {primary}, I'm confident we can align "
            f"on a package that reflects the value I'd bring to {company}.",
        ),
        DraftType.SELF_INTRODUCTION: (
            "Self Introduction",
            f"Hi, I'm a candidate excited about the {role} opportunity at {company}. "
            f"{evidence_line} I'm looking forward to contributing from day one.",
        ),
    }

    title, body = bodies.get(
        dtype,
        (dtype.value.replace("_", " ").title(), f"Draft for {role} at {company}. {evidence_line}"),
    )

    if length == DraftLength.SHORT:
        body = body.split("\n\n")[0]
    elif length == DraftLength.DETAILED and fit_summary:
        body = f"{body}\n\nFit context: {fit_summary}"

    return DraftItem(type=dtype, title=title, body=body)


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _coalesce(*values: Any) -> str:
    for value in values:
        if value:
            return str(value)
    return ""


def _clamp_unit(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.7
    return max(0.0, min(1.0, number))


def _default_for_annotation(annotation: Any) -> Any:
    """Best-effort default for a required field of unknown shape (generic fallback)."""
    origin = getattr(annotation, "__origin__", None)
    if origin in (list, tuple, set):
        return []
    if origin is dict:
        return {}
    if annotation in (str, None):
        return ""
    if annotation is int:
        return 0
    if annotation is float:
        return 0.0
    if annotation is bool:
        return False
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        nested: dict[str, Any] = {
            name: _default_for_annotation(field.annotation)
            for name, field in annotation.model_fields.items()
            if field.is_required()
        }
        return annotation(**nested)
    return ""
