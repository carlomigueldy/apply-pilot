"""Unit tests for Pydantic schema validation rules.

Covers:
- FitAnalysis: strong/partial match_level items must cite at least one
  evidence_chunk_id (validator rejects empty list).
- JobApplicationCreate: raw_job_post must be >= 30 characters.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from applypilot.schemas.application import JobApplicationCreate
from applypilot.schemas.enums import MatchLevel
from applypilot.schemas.fit import FitAnalysis, FitAnalysisItem  # noqa: I001

# ---------------------------------------------------------------------------
# FitAnalysis validator
# ---------------------------------------------------------------------------


def _make_item(
    match_level: MatchLevel,
    evidence_chunk_ids: list[str] | None = None,
    requirement_id: str = "req-001",
) -> FitAnalysisItem:
    """Construct a minimal FitAnalysisItem for testing."""
    return FitAnalysisItem(
        requirement_id=requirement_id,
        match_level=match_level,
        explanation="test explanation",
        evidence_chunk_ids=evidence_chunk_ids or [],
        confidence=0.9,
    )


def _make_fit_analysis(**overrides) -> FitAnalysis:
    """Build a valid FitAnalysis, merging *overrides* into sensible defaults."""
    defaults: dict = {
        "fit_score": 75,
        "summary": "Good overall fit",
        "items": [],
        "red_flags": [],
        "positioning_strategy": "Highlight backend experience",
    }
    return FitAnalysis(**{**defaults, **overrides})


class TestFitAnalysisValidator:
    def test_valid_strong_match_with_evidence(self) -> None:
        """STRONG match with non-empty evidence_chunk_ids must pass."""
        item = _make_item(
            match_level=MatchLevel.STRONG,
            evidence_chunk_ids=["chunk-abc", "chunk-def"],
        )
        analysis = _make_fit_analysis(items=[item])
        assert analysis.fit_score == 75

    def test_valid_partial_match_with_evidence(self) -> None:
        """PARTIAL match with non-empty evidence_chunk_ids must pass."""
        item = _make_item(
            match_level=MatchLevel.PARTIAL,
            evidence_chunk_ids=["chunk-xyz"],
        )
        analysis = _make_fit_analysis(items=[item])
        assert len(analysis.items) == 1

    def test_strong_match_without_evidence_raises(self) -> None:
        """STRONG match with empty evidence_chunk_ids must fail validation."""
        item = _make_item(match_level=MatchLevel.STRONG, evidence_chunk_ids=[])
        with pytest.raises(ValidationError) as exc_info:
            _make_fit_analysis(items=[item])
        errors = exc_info.value.errors()
        assert any("evidence" in str(e).lower() for e in errors)

    def test_partial_match_without_evidence_raises(self) -> None:
        """PARTIAL match with empty evidence_chunk_ids must fail validation."""
        item = _make_item(match_level=MatchLevel.PARTIAL, evidence_chunk_ids=[])
        with pytest.raises(ValidationError) as exc_info:
            _make_fit_analysis(items=[item])
        errors = exc_info.value.errors()
        assert any("evidence" in str(e).lower() for e in errors)

    def test_weak_match_without_evidence_is_valid(self) -> None:
        """WEAK match does NOT require evidence_chunk_ids."""
        item = _make_item(match_level=MatchLevel.WEAK, evidence_chunk_ids=[])
        analysis = _make_fit_analysis(items=[item])
        assert analysis.items[0].match_level == MatchLevel.WEAK

    def test_missing_match_without_evidence_is_valid(self) -> None:
        """MISSING match does NOT require evidence_chunk_ids."""
        item = _make_item(match_level=MatchLevel.MISSING, evidence_chunk_ids=[])
        analysis = _make_fit_analysis(items=[item])
        assert analysis.items[0].match_level == MatchLevel.MISSING

    def test_unknown_match_without_evidence_is_valid(self) -> None:
        """UNKNOWN match does NOT require evidence_chunk_ids."""
        item = _make_item(match_level=MatchLevel.UNKNOWN, evidence_chunk_ids=[])
        analysis = _make_fit_analysis(items=[item])
        assert analysis.items[0].match_level == MatchLevel.UNKNOWN

    def test_fit_score_bounds_valid(self) -> None:
        """fit_score must be between 0 and 100 inclusive."""
        _make_fit_analysis(fit_score=0)
        _make_fit_analysis(fit_score=100)

    def test_fit_score_out_of_bounds_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_fit_analysis(fit_score=101)
        with pytest.raises(ValidationError):
            _make_fit_analysis(fit_score=-1)

    def test_confidence_bounds(self) -> None:
        """confidence must be in [0, 1]."""
        with pytest.raises(ValidationError):
            FitAnalysisItem(
                requirement_id="req-001",
                match_level=MatchLevel.WEAK,
                explanation="test explanation",
                evidence_chunk_ids=[],
                confidence=1.1,
            )

    def test_mixed_items_strong_without_evidence_raises(self) -> None:
        """One valid partial + one invalid strong should still raise."""
        valid = _make_item(
            match_level=MatchLevel.PARTIAL,
            evidence_chunk_ids=["c1"],
            requirement_id="req-1",
        )
        invalid = _make_item(
            match_level=MatchLevel.STRONG,
            evidence_chunk_ids=[],
            requirement_id="req-2",
        )
        with pytest.raises(ValidationError):
            _make_fit_analysis(items=[valid, invalid])


# ---------------------------------------------------------------------------
# JobApplicationCreate validator
# ---------------------------------------------------------------------------


class TestJobApplicationCreate:
    def test_valid_raw_job_post(self) -> None:
        """A raw_job_post of exactly 30+ characters must pass."""
        payload = JobApplicationCreate(
            raw_job_post="We are hiring a Senior Python engineer with 5 years of experience.",
        )
        assert len(payload.raw_job_post) >= 30

    def test_raw_job_post_too_short_raises(self) -> None:
        """raw_job_post shorter than 30 characters must fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            JobApplicationCreate(raw_job_post="Too short")
        errors = exc_info.value.errors()
        assert any("min_length" in str(e) or "raw_job_post" in str(e) for e in errors)

    def test_raw_job_post_exactly_30_chars(self) -> None:
        """raw_job_post of exactly 30 characters must be accepted."""
        text = "x" * 30
        payload = JobApplicationCreate(raw_job_post=text)
        assert payload.raw_job_post == text

    def test_raw_job_post_29_chars_raises(self) -> None:
        """raw_job_post of 29 characters must be rejected."""
        with pytest.raises(ValidationError):
            JobApplicationCreate(raw_job_post="x" * 29)

    def test_optional_fields_default_to_none(self) -> None:
        """All optional fields default to None."""
        payload = JobApplicationCreate(
            raw_job_post="A" * 30,
        )
        assert payload.company_name is None
        assert payload.role_title is None
        assert payload.job_url is None
        assert payload.salary_text is None
        assert payload.work_arrangement is None

    def test_optional_fields_accepted(self) -> None:
        from applypilot.schemas.enums import WorkArrangement

        payload = JobApplicationCreate(
            raw_job_post="We are looking for a talented engineer to join our remote team.",
            company_name="Acme Corp",
            role_title="Senior Engineer",
            job_url="https://example.com/job/123",
            salary_text="$150k - $180k",
            work_arrangement=WorkArrangement.REMOTE,
        )
        assert payload.company_name == "Acme Corp"
        assert payload.work_arrangement == WorkArrangement.REMOTE
