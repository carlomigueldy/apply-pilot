"""``persist_outputs`` node — write the graph's results to the database.

Persists, in dependency order, the extracted requirements, the ranked evidence
matches, the fit analysis, and the generated drafts, then advances the
application to ``drafted``. The injected session is *flushed* but never committed
— transaction ownership stays with the service that drives the graph, so the
whole run can be committed or rolled back atomically.

A key responsibility here is id translation: requirements carry schema-level ids
like ``"req-0"`` throughout the graph, but the database keys evidence matches by
the real :class:`~applypilot.db.models.JobRequirement` UUID. This node builds and
applies that mapping; the original schema id is preserved in ``req_metadata`` for
traceability.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from applypilot.agents.nodes._common import append_error, attr, dump
from applypilot.agents.state import ApplicationGraphState
from applypilot.db.repositories.application_repository import (
    JobApplicationRepository,
    JobRequirementRepository,
)
from applypilot.db.repositories.draft_repository import DraftRepository
from applypilot.db.repositories.evidence_repository import (
    EvidenceMatchRepository,
    FitAnalysisRepository,
)
from applypilot.schemas.enums import ApplicationStatus, DraftLength, DraftStatus, Tone


def persist_outputs(session: Session, state: ApplicationGraphState) -> dict[str, Any]:
    """Persist requirements, evidence, fit analysis, and drafts; mark drafted.

    Args:
        session: Injected SQLAlchemy session (flushed, not committed).
        state: Current graph state holding the produced artefacts.

    Returns:
        ``{'persisted_ids': {...}}`` describing the rows written, or an ``errors``
        update if persistence fails.
    """
    try:
        application_id = uuid.UUID(str(state["application_id"]))

        requirement_id_map = _persist_requirements(session, application_id, state)
        evidence_match_ids = _persist_evidence_matches(
            session, application_id, state, requirement_id_map
        )
        fit_analysis_id = _persist_fit_analysis(session, application_id, state)
        draft_ids = _persist_drafts(session, application_id, state)

        _backfill_extracted_fields(session, application_id, state)
        JobApplicationRepository(session).update(
            application_id, status=ApplicationStatus.DRAFTED.value
        )

        return {
            "persisted_ids": {
                "application_id": str(application_id),
                "requirement_ids": list(requirement_id_map.values()),
                "evidence_match_ids": evidence_match_ids,
                "fit_analysis_id": fit_analysis_id,
                "draft_ids": draft_ids,
            }
        }
    except Exception as exc:
        return {
            "errors": append_error(
                state, "persist_outputs", str(exc), type(exc).__name__
            )
        }


# --- application backfill -------------------------------------------------------


def _backfill_extracted_fields(
    session: Session,
    application_id: uuid.UUID,
    state: ApplicationGraphState,
) -> None:
    """Fill empty application fields from the extracted job, preserving user input.

    The structured-extraction step recovers company, role, work arrangement, etc.
    from the raw job post; persisting them here is what makes the extracted detail
    surface in the UI (PRD F2). Existing non-empty values (supplied by the user at
    creation) are never overwritten.
    """
    extracted = state.get("extracted_job")
    if extracted is None:
        return
    application = JobApplicationRepository(session).get(application_id)
    if application is None:
        return

    arrangement = attr(extracted, "work_arrangement")
    arrangement_value = getattr(arrangement, "value", arrangement)
    if arrangement_value == "unknown":
        arrangement_value = None

    candidates = {
        "company_name": attr(extracted, "company_name"),
        "role_title": attr(extracted, "role_title"),
        "work_arrangement": arrangement_value,
        "salary_text": attr(extracted, "salary_text"),
        "timezone_text": attr(extracted, "timezone_text"),
    }
    for field, value in candidates.items():
        if value and not getattr(application, field, None):
            setattr(application, field, value)
    session.flush()


# --- per-artefact writers ------------------------------------------------------


def _persist_requirements(
    session: Session,
    application_id: uuid.UUID,
    state: ApplicationGraphState,
) -> dict[str, str]:
    """Persist requirements; return a ``schema_id -> db_uuid_str`` mapping."""
    repo = JobRequirementRepository(session)
    mapping: dict[str, str] = {}
    for requirement in state.get("requirements") or []:
        category = attr(requirement, "category")
        priority = attr(requirement, "priority")
        created = repo.create(
            application_id=application_id,
            text=attr(requirement, "text", ""),
            category=getattr(category, "value", str(category)),
            priority=getattr(priority, "value", str(priority)),
            req_metadata={"schema_id": attr(requirement, "id")},
        )
        mapping[str(attr(requirement, "id"))] = str(created.id)
    return mapping


def _persist_evidence_matches(
    session: Session,
    application_id: uuid.UUID,
    state: ApplicationGraphState,
    requirement_id_map: dict[str, str],
) -> list[str]:
    """Persist evidence matches whose requirement and chunk ids resolve cleanly."""
    rows: list[dict[str, Any]] = []
    for match in state.get("evidence_matches") or []:
        db_requirement_id = requirement_id_map.get(str(match.requirement_id))
        if db_requirement_id is None:
            continue
        try:
            chunk_id = uuid.UUID(str(match.evidence_chunk_id))
        except (ValueError, TypeError):
            continue
        rows.append(
            {
                "application_id": application_id,
                "requirement_id": uuid.UUID(db_requirement_id),
                "evidence_chunk_id": chunk_id,
                "summary": match.summary,
                "confidence": float(match.confidence),
            }
        )
    if not rows:
        return []
    created = EvidenceMatchRepository(session).bulk_create(rows)
    return [str(row.id) for row in created]


def _persist_fit_analysis(
    session: Session,
    application_id: uuid.UUID,
    state: ApplicationGraphState,
) -> str | None:
    """Persist the fit analysis (items + raw output as JSON); return its id."""
    fit = state.get("fit_analysis")
    if fit is None:
        return None
    created = FitAnalysisRepository(session).create(
        application_id=application_id,
        fit_score=attr(fit, "fit_score", 0),
        summary=attr(fit, "summary", ""),
        items=[dump(item) for item in attr(fit, "items", []) or []],
        red_flags=list(attr(fit, "red_flags", []) or []),
        positioning_strategy=attr(fit, "positioning_strategy"),
        raw_output=dump(fit),
    )
    return str(created.id)


def _persist_drafts(
    session: Session,
    application_id: uuid.UUID,
    state: ApplicationGraphState,
) -> list[str]:
    """Persist each generated draft as a ``needs_review`` row; return their ids."""
    bundle = state.get("draft_bundle")
    if bundle is None:
        return []

    tone = state.get("tone") or Tone.WARM_PROFESSIONAL.value
    length = state.get("length") or DraftLength.MEDIUM.value

    repo = DraftRepository(session)
    draft_ids: list[str] = []
    for item in attr(bundle, "drafts", []) or []:
        draft_type = attr(item, "type")
        created = repo.create(
            application_id=application_id,
            type=getattr(draft_type, "value", str(draft_type)),
            title=attr(item, "title", ""),
            body=attr(item, "body", ""),
            status=DraftStatus.NEEDS_REVIEW.value,
            tone=tone,
            length=length,
        )
        draft_ids.append(str(created.id))
    return draft_ids
