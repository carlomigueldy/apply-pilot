"""Schemas for fit analysis between a candidate and a job."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from applypilot.schemas.enums import MatchLevel

_REQUIRES_EVIDENCE = {MatchLevel.STRONG, MatchLevel.PARTIAL}


class FitAnalysisItem(BaseModel):
    """Per-requirement fit assessment."""

    requirement_id: str
    match_level: MatchLevel
    explanation: str
    evidence_chunk_ids: list[str]
    confidence: float = Field(ge=0, le=1)


class FitAnalysis(BaseModel):
    """Overall fit analysis for an application."""

    fit_score: int = Field(ge=0, le=100)
    summary: str
    items: list[FitAnalysisItem]
    red_flags: list[str]
    positioning_strategy: str

    @model_validator(mode="after")
    def _require_evidence_for_matches(self) -> FitAnalysis:
        """Strong/partial matches must cite at least one evidence chunk."""
        for item in self.items:
            if item.match_level in _REQUIRES_EVIDENCE and not item.evidence_chunk_ids:
                raise ValueError(
                    f"FitAnalysisItem for requirement '{item.requirement_id}' "
                    f"has match_level '{item.match_level.value}' but no "
                    "evidence_chunk_ids; strong/partial matches must cite evidence."
                )
        return self
