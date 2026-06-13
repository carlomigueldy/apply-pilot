"""Pydantic v2 schemas for the ApplyPilot API.

Re-exports the primary schema models and enums for convenient importing,
e.g. ``from applypilot.schemas import FitAnalysis``.
"""

from __future__ import annotations

from applypilot.schemas.application import (
    AnalyzeResponse,
    ApplicationListItem,
    JobApplicationCreate,
    JobApplicationRead,
    JobApplicationUpdate,
)
from applypilot.schemas.common import ORMModel, TimestampedSchema
from applypilot.schemas.drafts import (
    DraftApproveRequest,
    DraftBundle,
    DraftItem,
    DraftRead,
    RegenerateSectionRequest,
)
from applypilot.schemas.enums import (
    ApplicationStatus,
    DraftLength,
    DraftStatus,
    DraftType,
    GraphRunStatus,
    MatchLevel,
    ProfileItemType,
    RequirementCategory,
    RequirementPriority,
    ReviewDecisionType,
    Tone,
    WorkArrangement,
)
from applypilot.schemas.evidence import EvidenceMatch, EvidenceMatchList
from applypilot.schemas.fit import FitAnalysis, FitAnalysisItem
from applypilot.schemas.graph import GraphError, GraphRunRead
from applypilot.schemas.jobs import ExtractedJob, JobRequirement, JobRequirementList
from applypilot.schemas.profile import (
    ProfileItemBase,
    ProfileItemCreate,
    ProfileItemRead,
    ProfileItemUpdate,
    ProfileSearchRequest,
    ProfileSearchResponse,
    RetrievedEvidence,
)
from applypilot.schemas.settings import AppSettingsRead

__all__ = [
    # common
    "ORMModel",
    "TimestampedSchema",
    # enums
    "ApplicationStatus",
    "DraftLength",
    "DraftStatus",
    "DraftType",
    "GraphRunStatus",
    "MatchLevel",
    "ProfileItemType",
    "RequirementCategory",
    "RequirementPriority",
    "ReviewDecisionType",
    "Tone",
    "WorkArrangement",
    # profile
    "ProfileItemBase",
    "ProfileItemCreate",
    "ProfileItemUpdate",
    "ProfileItemRead",
    "ProfileSearchRequest",
    "RetrievedEvidence",
    "ProfileSearchResponse",
    # jobs
    "ExtractedJob",
    "JobRequirement",
    "JobRequirementList",
    # evidence
    "EvidenceMatch",
    "EvidenceMatchList",
    # fit
    "FitAnalysisItem",
    "FitAnalysis",
    # drafts
    "DraftItem",
    "DraftBundle",
    "DraftRead",
    "DraftApproveRequest",
    "RegenerateSectionRequest",
    # application
    "JobApplicationCreate",
    "JobApplicationUpdate",
    "JobApplicationRead",
    "ApplicationListItem",
    "AnalyzeResponse",
    # graph
    "GraphError",
    "GraphRunRead",
    # settings
    "AppSettingsRead",
]
