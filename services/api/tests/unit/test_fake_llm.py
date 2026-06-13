"""Unit tests for FakeLLMProvider determinism and grounding.

Verifies:
- ExtractedJob: same prompt -> identical output; fields extracted from context.
- JobRequirementList: 3-6 requirements from context; deterministic across calls.
- FitAnalysis: grounding (strong/partial items carry non-empty evidence_chunk_ids
  from context); schema validator always passes; fit_score computed deterministically.
- DraftBundle: one DraftItem per requested DraftType; body references company/role.
- Generic fallback: unknown schema produces a minimal valid instance.
- text(): short deterministic string derived from the prompt.
- Determinism: same (prompt, schema) pair -> identical model_dump().
"""

from __future__ import annotations

from applypilot.agents.grounding import build_context_block
from applypilot.agents.llm.fake import FakeLLMProvider
from applypilot.schemas.drafts import DraftBundle
from applypilot.schemas.enums import (
    DraftType,
    MatchLevel,
)
from applypilot.schemas.fit import FitAnalysis
from applypilot.schemas.jobs import ExtractedJob, JobRequirementList

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_RAW_JOB_POST = """
Company: AcmeCorp
Role: Senior Python Engineer
Location: Remote

We are looking for a Senior Python Engineer to join our team.
Requirements:
- 5+ years of Python backend experience required
- Proficiency in FastAPI and SQLAlchemy
- Experience with PostgreSQL and database design
- Strong understanding of REST APIs
- Ability to mentor junior engineers
- Experience with Docker and CI/CD pipelines
Salary: $150,000 - $180,000 per year
"""

_REQUIREMENTS_CTX = [
    {"id": "req-1", "text": "5+ years of Python backend experience", "category": "backend", "priority": "must_have"},
    {"id": "req-2", "text": "Proficiency in FastAPI", "category": "backend", "priority": "must_have"},
    {"id": "req-3", "text": "PostgreSQL database design", "category": "backend", "priority": "nice_to_have"},
]

_EVIDENCE_CTX = [
    {
        "requirement_id": "req-1",
        "evidence_chunk_id": "chunk-abc-111",
        "profile_item_id": "item-001",
        "summary": "7 years of Python engineering across multiple production systems.",
        "confidence": 0.9,
    },
    {
        "requirement_id": "req-1",
        "evidence_chunk_id": "chunk-abc-222",
        "profile_item_id": "item-001",
        "summary": "Led backend Python architecture for high-traffic platform.",
        "confidence": 0.85,
    },
    {
        "requirement_id": "req-2",
        "evidence_chunk_id": "chunk-bcd-333",
        "profile_item_id": "item-002",
        "summary": "Built production FastAPI microservices serving 100k requests/day.",
        "confidence": 0.8,
    },
    # req-3 has no evidence -> missing
]


def _make_provider() -> FakeLLMProvider:
    return FakeLLMProvider()


def _prompt_with(context: dict) -> str:
    return "Analyse the following job post." + build_context_block(context)


# ---------------------------------------------------------------------------
# ExtractedJob
# ---------------------------------------------------------------------------


class TestFakeLLMExtractedJob:
    def test_returns_extracted_job_instance(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, ExtractedJob)
        assert isinstance(result, ExtractedJob)

    def test_company_name_extracted(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, ExtractedJob)
        assert result.company_name == "AcmeCorp"

    def test_role_title_extracted(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, ExtractedJob)
        assert result.role_title == "Senior Python Engineer"

    def test_summary_non_empty(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, ExtractedJob)
        assert result.summary and len(result.summary) > 0

    def test_determinism(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        r1 = provider.structured(prompt, ExtractedJob)
        r2 = provider.structured(prompt, ExtractedJob)
        assert r1.model_dump() == r2.model_dump()

    def test_remote_arrangement_detected(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, ExtractedJob)
        from applypilot.schemas.enums import WorkArrangement
        assert result.work_arrangement == WorkArrangement.REMOTE

    def test_salary_text_extracted(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, ExtractedJob)
        # Salary is present — either from label extraction or regex
        assert result.salary_text is not None


# ---------------------------------------------------------------------------
# JobRequirementList
# ---------------------------------------------------------------------------


class TestFakeLLMJobRequirementList:
    def test_returns_requirement_list_instance(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, JobRequirementList)
        assert isinstance(result, JobRequirementList)

    def test_produces_3_to_6_requirements(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, JobRequirementList)
        assert 3 <= len(result.requirements) <= 6

    def test_requirement_ids_are_sequential(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, JobRequirementList)
        ids = [r.id for r in result.requirements]
        assert all(id_.startswith("req-") for id_ in ids)

    def test_determinism(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        r1 = provider.structured(prompt, JobRequirementList)
        r2 = provider.structured(prompt, JobRequirementList)
        assert r1.model_dump() == r2.model_dump()

    def test_requirements_have_valid_category(self) -> None:
        from applypilot.schemas.enums import RequirementCategory
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, JobRequirementList)
        valid_categories = {c.value for c in RequirementCategory}
        for req in result.requirements:
            assert req.category.value in valid_categories

    def test_requirements_have_valid_priority(self) -> None:
        from applypilot.schemas.enums import RequirementPriority
        provider = _make_provider()
        prompt = _prompt_with({"raw_job_post": _RAW_JOB_POST})
        result = provider.structured(prompt, JobRequirementList)
        valid_priorities = {p.value for p in RequirementPriority}
        for req in result.requirements:
            assert req.priority.value in valid_priorities


# ---------------------------------------------------------------------------
# FitAnalysis — grounding linchpin
# ---------------------------------------------------------------------------


class TestFakeLLMFitAnalysis:
    def test_returns_fit_analysis_instance(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        result = provider.structured(prompt, FitAnalysis)
        assert isinstance(result, FitAnalysis)

    def test_schema_validator_passes(self) -> None:
        """FitAnalysis model_validator must not raise (strong/partial must have chunk ids)."""
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        # Should not raise ValidationError
        result = provider.structured(prompt, FitAnalysis)
        assert result is not None

    def test_strong_items_carry_evidence_chunk_ids(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        result = provider.structured(prompt, FitAnalysis)
        for item in result.items:
            if item.match_level in (MatchLevel.STRONG, MatchLevel.PARTIAL):
                assert len(item.evidence_chunk_ids) > 0, (
                    f"Requirement {item.requirement_id} has {item.match_level} but no chunk ids"
                )

    def test_req_with_multiple_evidence_is_strong(self) -> None:
        """req-1 has 2 evidence entries with high confidence -> STRONG."""
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        result = provider.structured(prompt, FitAnalysis)
        req1_item = next((i for i in result.items if i.requirement_id == "req-1"), None)
        assert req1_item is not None
        assert req1_item.match_level == MatchLevel.STRONG
        assert "chunk-abc-111" in req1_item.evidence_chunk_ids or "chunk-abc-222" in req1_item.evidence_chunk_ids

    def test_req_without_evidence_is_missing(self) -> None:
        """req-3 has no evidence -> MISSING with empty evidence_chunk_ids."""
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        result = provider.structured(prompt, FitAnalysis)
        req3_item = next((i for i in result.items if i.requirement_id == "req-3"), None)
        assert req3_item is not None
        assert req3_item.match_level == MatchLevel.MISSING
        assert req3_item.evidence_chunk_ids == []

    def test_fit_score_in_valid_range(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        result = provider.structured(prompt, FitAnalysis)
        assert 0 <= result.fit_score <= 100

    def test_determinism(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": _EVIDENCE_CTX})
        r1 = provider.structured(prompt, FitAnalysis)
        r2 = provider.structured(prompt, FitAnalysis)
        assert r1.model_dump() == r2.model_dump()

    def test_red_flags_from_context(self) -> None:
        provider = _make_provider()
        prompt = _prompt_with({
            "requirements": _REQUIREMENTS_CTX,
            "evidence": [],
            "red_flags": ["Salary below target", "Requires relocation"],
        })
        result = provider.structured(prompt, FitAnalysis)
        assert "Salary below target" in result.red_flags
        assert "Requires relocation" in result.red_flags

    def test_no_evidence_all_missing(self) -> None:
        """With no evidence at all, all items should be MISSING."""
        provider = _make_provider()
        prompt = _prompt_with({"requirements": _REQUIREMENTS_CTX, "evidence": []})
        result = provider.structured(prompt, FitAnalysis)
        for item in result.items:
            assert item.match_level == MatchLevel.MISSING
            assert item.evidence_chunk_ids == []


# ---------------------------------------------------------------------------
# DraftBundle
# ---------------------------------------------------------------------------


class TestFakeLLMDraftBundle:
    def test_returns_draft_bundle_instance(self) -> None:
        provider = _make_provider()
        context = {
            "extracted_job": {"company_name": "AcmeCorp", "role_title": "Senior Python Engineer"},
            "fit_summary": "Strong fit with 7 years Python experience.",
            "draft_types": [DraftType.RECRUITER_REPLY.value, DraftType.COVER_EMAIL.value],
        }
        prompt = "Generate drafts." + build_context_block(context)
        result = provider.structured(prompt, DraftBundle)
        assert isinstance(result, DraftBundle)

    def test_one_draft_per_requested_type(self) -> None:
        provider = _make_provider()
        requested = [DraftType.RECRUITER_REPLY.value, DraftType.COVER_EMAIL.value, DraftType.RESUME_SUMMARY.value]
        context = {
            "extracted_job": {"company_name": "AcmeCorp", "role_title": "Python Engineer"},
            "draft_types": requested,
        }
        prompt = "Generate drafts." + build_context_block(context)
        result = provider.structured(prompt, DraftBundle)
        produced_types = {d.type.value for d in result.drafts}
        assert produced_types == set(requested)

    def test_default_draft_types_when_unspecified(self) -> None:
        """Without draft_types in context, all 7 default types should be produced."""
        provider = _make_provider()
        context = {
            "extracted_job": {"company_name": "AcmeCorp", "role_title": "Python Engineer"},
        }
        prompt = "Generate drafts." + build_context_block(context)
        result = provider.structured(prompt, DraftBundle)
        assert len(result.drafts) == 7

    def test_draft_body_references_company(self) -> None:
        provider = _make_provider()
        context = {
            "extracted_job": {"company_name": "AcmeCorp", "role_title": "Python Engineer"},
            "draft_types": [DraftType.COVER_EMAIL.value],
        }
        prompt = "Generate drafts." + build_context_block(context)
        result = provider.structured(prompt, DraftBundle)
        assert len(result.drafts) == 1
        assert "AcmeCorp" in result.drafts[0].body

    def test_draft_body_references_role(self) -> None:
        provider = _make_provider()
        context = {
            "extracted_job": {"company_name": "AcmeCorp", "role_title": "Python Engineer"},
            "draft_types": [DraftType.RECRUITER_REPLY.value],
        }
        prompt = "Generate drafts." + build_context_block(context)
        result = provider.structured(prompt, DraftBundle)
        assert "Python Engineer" in result.drafts[0].body

    def test_determinism(self) -> None:
        provider = _make_provider()
        context = {
            "extracted_job": {"company_name": "AcmeCorp", "role_title": "Python Engineer"},
            "draft_types": [DraftType.COVER_EMAIL.value],
        }
        prompt = "Generate drafts." + build_context_block(context)
        r1 = provider.structured(prompt, DraftBundle)
        r2 = provider.structured(prompt, DraftBundle)
        assert r1.model_dump() == r2.model_dump()


# ---------------------------------------------------------------------------
# text() method
# ---------------------------------------------------------------------------


class TestFakeLLMText:
    def test_returns_string(self) -> None:
        provider = _make_provider()
        result = provider.text("Summarise this job post.")
        assert isinstance(result, str)

    def test_non_empty_for_non_empty_prompt(self) -> None:
        provider = _make_provider()
        result = provider.text("Summarise this job post.")
        assert len(result) > 0

    def test_determinism(self) -> None:
        provider = _make_provider()
        r1 = provider.text("Summarise this job post.")
        r2 = provider.text("Summarise this job post.")
        assert r1 == r2

    def test_different_prompts_differ(self) -> None:
        provider = _make_provider()
        r1 = provider.text("First prompt about Python.")
        r2 = provider.text("Second prompt about JavaScript.")
        assert r1 != r2


# ---------------------------------------------------------------------------
# Generic fallback
# ---------------------------------------------------------------------------


class TestFakeLLMGenericFallback:
    def test_generic_unknown_schema_does_not_raise(self) -> None:
        """A simple BaseModel with only optional fields should produce a valid instance."""
        from pydantic import BaseModel

        class SimpleSchema(BaseModel):
            value: str = "default"
            count: int = 0

        provider = _make_provider()
        result = provider.structured("some prompt", SimpleSchema)
        assert isinstance(result, SimpleSchema)
