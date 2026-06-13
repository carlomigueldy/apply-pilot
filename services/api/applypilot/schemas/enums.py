"""Enumerations shared across ApplyPilot schemas.

All enums subclass ``(str, Enum)`` so they serialize as their string values and
interoperate cleanly with JSON, SQLAlchemy text columns, and Pydantic.
"""

from __future__ import annotations

from enum import Enum


class ProfileItemType(str, Enum):  # noqa: UP042
    """Type of a profile item stored for a user."""

    ROLE = "role"
    PROJECT = "project"
    SKILL = "skill"
    ACHIEVEMENT = "achievement"
    TESTIMONIAL = "testimonial"
    SALARY = "salary"
    INTERVIEW_ANSWER = "interview_answer"
    PREFERENCE = "preference"


class ApplicationStatus(str, Enum):  # noqa: UP042
    """Lifecycle status of a job application."""

    SAVED = "saved"
    ANALYZED = "analyzed"
    DRAFTED = "drafted"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DraftType(str, Enum):  # noqa: UP042
    """Type of generated draft artifact."""

    RECRUITER_REPLY = "recruiter_reply"
    COVER_EMAIL = "cover_email"
    RESUME_SUMMARY = "resume_summary"
    RESUME_BULLETS = "resume_bullets"
    INTERVIEW_TALKING_POINTS = "interview_talking_points"
    SALARY_RESPONSE = "salary_response"
    SELF_INTRODUCTION = "self_introduction"


class DraftStatus(str, Enum):  # noqa: UP042
    """Review status of a draft."""

    GENERATED = "generated"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class RequirementCategory(str, Enum):  # noqa: UP042
    """Category bucket for an extracted job requirement."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    AI = "ai"
    WEB3 = "web3"
    DEVOPS = "devops"
    SOFT_SKILL = "soft_skill"
    DOMAIN = "domain"
    OTHER = "other"


class RequirementPriority(str, Enum):  # noqa: UP042
    """How critical a requirement is to the role."""

    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    UNKNOWN = "unknown"


class MatchLevel(str, Enum):  # noqa: UP042
    """Strength of a candidate's match against a requirement."""

    STRONG = "strong"
    PARTIAL = "partial"
    WEAK = "weak"
    MISSING = "missing"
    UNKNOWN = "unknown"


class WorkArrangement(str, Enum):  # noqa: UP042
    """Work arrangement for a role."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class GraphRunStatus(str, Enum):  # noqa: UP042
    """Execution status of an agent graph run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class ReviewDecisionType(str, Enum):  # noqa: UP042
    """Human-in-the-loop review decision for a draft."""

    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    REGENERATE = "regenerate"


class Tone(str, Enum):  # noqa: UP042
    """Desired tone for generated drafts."""

    DIRECT = "direct"
    WARM_PROFESSIONAL = "warm_professional"
    CONFIDENT = "confident"
    CONCISE = "concise"


class DraftLength(str, Enum):  # noqa: UP042
    """Desired length for generated drafts."""

    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"
