"""Repository layer for ApplyPilot — thin, pure-DB wrappers around ORM models.

Each repository accepts a synchronous :class:`sqlalchemy.orm.Session` and
returns ORM objects.  No LLM or business logic lives here.
"""

from applypilot.db.repositories.application_repository import (
    JobApplicationRepository,
    JobRequirementRepository,
)
from applypilot.db.repositories.draft_repository import DraftRepository
from applypilot.db.repositories.evidence_repository import (
    EvidenceMatchRepository,
    FitAnalysisRepository,
)
from applypilot.db.repositories.graph_run_repository import GraphRunRepository
from applypilot.db.repositories.profile_repository import (
    EvidenceChunkRepository,
    ProfileItemRepository,
)

__all__ = [
    "DraftRepository",
    "EvidenceChunkRepository",
    "EvidenceMatchRepository",
    "FitAnalysisRepository",
    "GraphRunRepository",
    "JobApplicationRepository",
    "JobRequirementRepository",
    "ProfileItemRepository",
]
