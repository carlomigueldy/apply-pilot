"""``generate_fit_analysis`` node — score requirement-by-requirement fit.

Grounds the ``fit_analysis`` prompt with the requirements, the ranked evidence
matches, the extracted job, and a deterministically-computed ``red_flags`` list
derived from the candidate's preferences (remote vs on-site, salary band). The
provider returns a validated :class:`~applypilot.schemas.fit.FitAnalysis` whose
strong/partial matches are guaranteed to cite evidence chunk ids.

The session is injected so this node can read the owning ``User`` preferences;
it never writes to the database.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from applypilot.agents.grounding import build_context_block
from applypilot.agents.llm.base import LLMProvider
from applypilot.agents.nodes._common import append_error, attr, dump
from applypilot.agents.prompts import load_prompt
from applypilot.agents.state import ApplicationGraphState
from applypilot.agents.tools import salary_strategy
from applypilot.db.models import User
from applypilot.db.repositories.application_repository import JobApplicationRepository
from applypilot.schemas.enums import Tone, WorkArrangement
from applypilot.schemas.fit import FitAnalysis


def generate_fit_analysis(
    session: Session, provider: LLMProvider, state: ApplicationGraphState
) -> dict[str, Any]:
    """Produce ``{'fit_analysis': FitAnalysis}`` (plus a derived ``tone``).

    Args:
        session: Injected SQLAlchemy session, used only to read user preferences.
        provider: Injected LLM provider.
        state: Current graph state; ``requirements``, ``evidence_matches`` and
            ``extracted_job`` are read.

    Returns:
        Partial state with the synthesised ``fit_analysis``. When the user has a
        valid preferred tone and the caller has not already pinned ``state['tone']``,
        that tone is forwarded for the draft node to consume. On provider failure
        an ``errors`` update is returned instead.
    """
    try:
        requirements = state.get("requirements") or []
        evidence_matches = state.get("evidence_matches") or []
        extracted = state.get("extracted_job")

        user = _load_user(session, state)
        red_flags = _compute_red_flags(user, extracted)

        context = {
            "requirements": [dump(req) for req in requirements],
            "evidence": [
                {
                    "requirement_id": match.requirement_id,
                    "evidence_chunk_id": match.evidence_chunk_id,
                    "profile_item_id": match.profile_item_id,
                    "summary": match.summary,
                    "confidence": match.confidence,
                }
                for match in evidence_matches
            ],
            "extracted_job": dump(extracted),
            "red_flags": red_flags,
        }
        prompt = load_prompt("fit_analysis") + build_context_block(context)
        fit = provider.structured(prompt, FitAnalysis)

        result: dict[str, Any] = {"fit_analysis": fit}
        tone = _user_tone(user)
        if tone is not None and not state.get("tone"):
            result["tone"] = tone
        return result
    except Exception as exc:
        return {
            "errors": append_error(
                state, "generate_fit_analysis", str(exc), type(exc).__name__
            )
        }


# --- preference helpers --------------------------------------------------------


def _load_user(session: Session | None, state: ApplicationGraphState) -> User | None:
    """Best-effort load of the owning ``User`` from state or the application row.

    Never raises: returns ``None`` when the session is absent, ids are malformed,
    or no matching user exists. Red-flag and tone derivation degrade gracefully.
    """
    if session is None:
        return None
    try:
        raw_user_id = state.get("user_id")
        if raw_user_id:
            user = session.get(User, uuid.UUID(str(raw_user_id)))
            if user is not None:
                return user

        raw_application_id = state.get("application_id")
        if raw_application_id:
            application = JobApplicationRepository(session).get(
                uuid.UUID(str(raw_application_id))
            )
            if application is not None:
                return session.get(User, application.user_id)
    except (ValueError, TypeError):
        return None
    return None


def _compute_red_flags(user: User | None, extracted: Any) -> list[str]:
    """Derive concrete red flags from the job vs the user's preferences.

    Deterministic and side-effect free. Returns an empty list when the user or
    extracted job is unavailable, or when no concern is detected.
    """
    if user is None or extracted is None:
        return []

    flags: list[str] = []
    try:
        arrangement = attr(extracted, "work_arrangement")
        arrangement_value = (
            arrangement.value
            if isinstance(arrangement, WorkArrangement)
            else (str(arrangement) if arrangement else "")
        )
        remote_pref = (user.remote_preference or "").lower()
        if "remote" in remote_pref and arrangement_value == WorkArrangement.ONSITE.value:
            flags.append("This role is on-site, but your profile prefers remote work.")

        salary_text = attr(extracted, "salary_text")
        if salary_text and user.target_salary_min_usd and user.target_salary_max_usd:
            strategy = salary_strategy(
                user.target_salary_min_usd,
                user.target_salary_max_usd,
                str(salary_text),
                user.remote_preference,
            )
            if strategy.get("below_target"):
                flags.append(
                    f"Compensation may fall below your target band — {strategy['rationale']}"
                )
    except Exception:  # noqa: BLE001 - red flags are advisory; never break analysis
        return flags
    return flags


def _user_tone(user: User | None) -> str | None:
    """Return the user's preferred tone as a valid ``Tone`` value, or ``None``."""
    if user is None or not user.preferred_tone:
        return None
    try:
        return Tone(user.preferred_tone).value
    except ValueError:
        return None
