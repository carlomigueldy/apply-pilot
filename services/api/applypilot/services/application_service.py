"""Application domain service — orchestrates the full job-application lifecycle.

:class:`ApplicationService` is the single point of contact between the HTTP layer
and all lower-level concerns: repositories, the LLM provider, and the analysis
graph.  It is intentionally **synchronous** (no async/await).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from applypilot.agents.grounding import build_context_block
from applypilot.agents.llm.factory import get_llm_provider
from applypilot.agents.prompts import load_prompt
from applypilot.core.config import get_settings
from applypilot.db.models import (
    Draft,
    EvidenceChunk,
    EvidenceMatch,
    FitAnalysis,
    GraphRun,
    JobRequirement,
    ProfileItem,
    ReviewDecision,
)
from applypilot.db.repositories.application_repository import (
    JobApplicationRepository,
)
from applypilot.db.repositories.draft_repository import DraftRepository
from applypilot.db.repositories.evidence_repository import FitAnalysisRepository
from applypilot.db.repositories.graph_run_repository import GraphRunRepository
from applypilot.schemas.application import (
    AnalyzeResponse,
    ApplicationListItem,
    JobApplicationCreate,
    JobApplicationRead,
    JobApplicationUpdate,
)
from applypilot.schemas.drafts import (
    DraftApproveRequest,
    DraftBundle,
    DraftRead,
    RegenerateSectionRequest,
)
from applypilot.schemas.enums import ApplicationStatus, DraftStatus, DraftType
from applypilot.schemas.fit import FitAnalysis as FitAnalysisSchema
from applypilot.schemas.fit import FitAnalysisItem
from applypilot.services.graph_run_service import GraphRunService


class ApplicationService:
    """Domain service for job-application CRUD and AI-driven analysis.

    Args:
        session: A bound, synchronous SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    def create_application(
        self, data: JobApplicationCreate, user_id: uuid.UUID
    ) -> JobApplicationRead:
        """Persist a new job application with status ``saved``.

        Args:
            data: Validated creation payload.
            user_id: UUID of the owning user.

        Returns:
            The persisted application as a :class:`JobApplicationRead`.
        """
        repo = JobApplicationRepository(self._session)
        application = repo.create(
            user_id=user_id,
            raw_job_post=data.raw_job_post,
            company_name=data.company_name,
            role_title=data.role_title,
            job_url=data.job_url,
            salary_text=data.salary_text,
            work_arrangement=data.work_arrangement.value if data.work_arrangement else None,
            timezone_text=data.timezone_text,
            recruiter_name=data.recruiter_name,
            recruiter_email=data.recruiter_email,
            status=ApplicationStatus.SAVED.value,
        )
        self._session.commit()
        return JobApplicationRead.model_validate(application)

    def list_applications(self, user_id: uuid.UUID) -> list[ApplicationListItem]:
        """Return all applications for *user_id*, newest first, with latest fit score.

        Args:
            user_id: The owning user UUID.

        Returns:
            List of condensed application items including ``fit_score``.
        """
        repo = JobApplicationRepository(self._session)
        rows = repo.list_with_fit_summary(user_id)
        items: list[ApplicationListItem] = []
        for application, fit in rows:
            items.append(
                ApplicationListItem(
                    id=application.id,
                    company_name=application.company_name,
                    role_title=application.role_title,
                    status=ApplicationStatus(application.status),
                    fit_score=fit.fit_score if fit is not None else None,
                    created_at=application.created_at,
                    updated_at=application.updated_at,
                )
            )
        return items

    def get_application(self, application_id: uuid.UUID) -> JobApplicationRead:
        """Return a single application or raise :exc:`ValueError`.

        Args:
            application_id: UUID of the application.

        Returns:
            The application as a :class:`JobApplicationRead`.

        Raises:
            ValueError: When the application is not found.
        """
        application = JobApplicationRepository(self._session).get(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")
        return JobApplicationRead.model_validate(application)

    def update_application(
        self, application_id: uuid.UUID, data: JobApplicationUpdate
    ) -> JobApplicationRead:
        """Partially update a job application.

        Only non-``None`` fields in *data* are applied.

        Args:
            application_id: UUID of the application to update.
            data: Partial update payload.

        Returns:
            The updated application as a :class:`JobApplicationRead`.

        Raises:
            ValueError: When the application is not found.
        """
        updates: dict[str, Any] = {
            k: (v.value if hasattr(v, "value") else v)
            for k, v in data.model_dump(exclude_none=True).items()
        }
        application = JobApplicationRepository(self._session).update(
            application_id, **updates
        )
        if application is None:
            raise ValueError(f"Application {application_id} not found")
        self._session.commit()
        return JobApplicationRead.model_validate(application)

    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------

    def analyze(self, application_id: uuid.UUID) -> AnalyzeResponse:
        """Clear prior analysis data and run the full application-analysis graph.

        Deletes existing :class:`~applypilot.db.models.JobRequirement` rows (which
        cascade-delete ``EvidenceMatch`` via the DB FK) and
        :class:`~applypilot.db.models.FitAnalysis` rows for the application, then
        delegates to :class:`~applypilot.services.graph_run_service.GraphRunService`.

        Args:
            application_id: UUID of the application to analyse.

        Returns:
            An :class:`AnalyzeResponse` with the graph-run id and final status.

        Raises:
            ValueError: When the application is not found.
        """
        application = JobApplicationRepository(self._session).get(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")

        self._session.execute(
            sa_delete(FitAnalysis).where(FitAnalysis.application_id == application_id)
        )
        self._session.execute(
            sa_delete(JobRequirement).where(
                JobRequirement.application_id == application_id
            )
        )
        self._session.commit()

        graph_run = GraphRunService(self._session).run_analysis(application_id)

        return AnalyzeResponse(
            application_id=str(application_id),
            graph_run_id=str(graph_run.id),
            status=graph_run.status,
        )

    def get_analysis(self, application_id: uuid.UUID) -> FitAnalysisSchema:
        """Return the latest fit analysis for *application_id*.

        Args:
            application_id: UUID of the application.

        Returns:
            A validated :class:`~applypilot.schemas.fit.FitAnalysis`.

        Raises:
            ValueError: When no fit analysis exists yet.
        """
        db_fit = FitAnalysisRepository(self._session).get_latest_by_application(
            application_id
        )
        if db_fit is None:
            raise ValueError(f"No fit analysis found for application {application_id}")

        if db_fit.raw_output:
            return FitAnalysisSchema.model_validate(db_fit.raw_output)

        items = [FitAnalysisItem.model_validate(item) for item in (db_fit.items or [])]
        return FitAnalysisSchema(
            fit_score=db_fit.fit_score,
            summary=db_fit.summary or "",
            items=items,
            red_flags=list(db_fit.red_flags or []),
            positioning_strategy=db_fit.positioning_strategy or "",
        )

    def get_evidence(self, application_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return evidence matches for *application_id* joined with chunk and title data.

        Args:
            application_id: UUID of the application.

        Returns:
            List of dicts with combined evidence-match, chunk, and profile-item fields.
        """
        stmt = (
            select(EvidenceMatch, EvidenceChunk, ProfileItem, JobRequirement)
            .join(EvidenceChunk, EvidenceMatch.evidence_chunk_id == EvidenceChunk.id)
            .join(ProfileItem, EvidenceChunk.profile_item_id == ProfileItem.id)
            .join(JobRequirement, EvidenceMatch.requirement_id == JobRequirement.id)
            .where(EvidenceMatch.application_id == application_id)
            .order_by(EvidenceMatch.created_at)
        )
        rows = self._session.execute(stmt).all()
        return [
            {
                "id": str(row[0].id),
                "requirement_id": str(row[0].requirement_id),
                "requirement_text": row[3].text,
                "evidence_chunk_id": str(row[0].evidence_chunk_id),
                "chunk_text": row[1].chunk_text,
                "profile_item_id": str(row[1].profile_item_id),
                "profile_item_title": row[2].title,
                "summary": row[0].summary,
                "confidence": float(row[0].confidence),
            }
            for row in rows
        ]

    # -------------------------------------------------------------------------
    # Drafts
    # -------------------------------------------------------------------------

    def get_drafts(self, application_id: uuid.UUID) -> list[DraftRead]:
        """Return all drafts for *application_id*, newest version first.

        Args:
            application_id: UUID of the application.

        Returns:
            List of :class:`~applypilot.schemas.drafts.DraftRead` items.
        """
        drafts = DraftRepository(self._session).list_by_application(application_id)
        return [DraftRead.model_validate(d) for d in drafts]

    def generate_drafts(self, application_id: uuid.UUID) -> list[DraftRead]:
        """Regenerate the full draft bundle as new versioned rows with ``needs_review``.

        Constructs context from the application and latest fit analysis, then asks
        the LLM provider to produce a :class:`~applypilot.schemas.drafts.DraftBundle`.
        Each item is persisted as a new draft version; no existing drafts are
        deleted.

        Args:
            application_id: UUID of the application.

        Returns:
            List of newly created :class:`~applypilot.schemas.drafts.DraftRead` items.

        Raises:
            ValueError: When the application is not found.
        """
        application = JobApplicationRepository(self._session).get(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")

        provider = get_llm_provider(get_settings())

        latest_fit = FitAnalysisRepository(self._session).get_latest_by_application(
            application_id
        )

        context: dict[str, Any] = {
            "extracted_job": {
                "company_name": application.company_name,
                "role_title": application.role_title,
                "work_arrangement": application.work_arrangement,
                "salary_text": application.salary_text,
            },
            "fit_summary": latest_fit.summary if latest_fit else "",
            "fit_score": latest_fit.fit_score if latest_fit else 0,
            "draft_types": [dt.value for dt in DraftType],
        }

        prompt = load_prompt("draft_bundle") + build_context_block(context)
        bundle: DraftBundle = provider.structured(prompt, DraftBundle)

        draft_repo = DraftRepository(self._session)
        created_drafts: list[DraftRead] = []
        for item in bundle.drafts:
            draft = draft_repo.create(
                application_id=application_id,
                type=item.type.value,
                title=item.title,
                body=item.body,
                status=DraftStatus.NEEDS_REVIEW.value,
            )
            created_drafts.append(DraftRead.model_validate(draft))

        if application.status == ApplicationStatus.ANALYZED.value:
            JobApplicationRepository(self._session).update(
                application_id, status=ApplicationStatus.DRAFTED.value
            )

        self._session.commit()
        return created_drafts

    def approve_draft(self, data: DraftApproveRequest) -> DraftRead:
        """Approve (and optionally edit) a draft, recording the review decision.

        If ``edited_body`` is provided the draft body is replaced and the status
        becomes ``edited``; otherwise the status is set to ``approved``.  A
        :class:`~applypilot.db.models.ReviewDecision` row is created for the audit
        trail.  When this is the **first** approved/edited draft for the
        application, the application status advances to ``ready_to_apply``.

        Args:
            data: Approval payload including ``draft_id`` and optional edit.

        Returns:
            The updated :class:`~applypilot.schemas.drafts.DraftRead`.

        Raises:
            ValueError: When the draft is not found.
        """
        draft_repo = DraftRepository(self._session)
        draft_id = uuid.UUID(data.draft_id)
        draft = draft_repo.get(draft_id)
        if draft is None:
            raise ValueError(f"Draft {data.draft_id} not found")

        application_id = draft.application_id

        if data.edited_body is not None:
            draft = draft_repo.update(draft_id, body=data.edited_body, status=DraftStatus.EDITED.value)
        else:
            draft = draft_repo.set_status(draft_id, DraftStatus.APPROVED.value)

        if draft is None:
            raise ValueError(f"Draft {data.draft_id} could not be updated")

        decision_value = "edit" if data.edited_body is not None else "approve"
        decision = ReviewDecision(
            application_id=application_id,
            draft_id=draft_id,
            decision=decision_value,
            notes=data.notes,
        )
        self._session.add(decision)
        self._session.flush()

        # Advance application status on the first approved/edited draft.
        other_approved_count = self._session.execute(
            select(func.count()).where(
                Draft.application_id == application_id,
                Draft.id != draft_id,
                Draft.status.in_([DraftStatus.APPROVED.value, DraftStatus.EDITED.value]),
            )
        ).scalar_one()

        if other_approved_count == 0:
            JobApplicationRepository(self._session).update(
                application_id, status=ApplicationStatus.READY_TO_APPLY.value
            )

        self._session.commit()
        return DraftRead.model_validate(draft)

    def regenerate_section(
        self, application_id: uuid.UUID, request: RegenerateSectionRequest
    ) -> DraftRead:
        """Regenerate a single draft type as a new versioned row.

        Fetches the latest existing draft of the requested type for context, then
        calls the LLM provider with tone/length/instructions to produce a fresh
        version, persisted with status ``needs_review``.

        Args:
            application_id: UUID of the application.
            request: Specifies the draft type, tone, length, and optional instructions.

        Returns:
            The newly created :class:`~applypilot.schemas.drafts.DraftRead`.

        Raises:
            ValueError: When the application is not found or the provider produces
                no drafts for the requested type.
        """
        application = JobApplicationRepository(self._session).get(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")

        provider = get_llm_provider(get_settings())

        latest_fit = FitAnalysisRepository(self._session).get_latest_by_application(
            application_id
        )

        # Retrieve the latest existing draft of this type for original_body context.
        existing_drafts = DraftRepository(self._session).list_by_application(
            application_id, type=request.type.value
        )
        original_body = existing_drafts[0].body if existing_drafts else ""

        context: dict[str, Any] = {
            "draft_type": request.type.value,
            "draft_types": [request.type.value],
            "original_body": original_body,
            "instructions": request.instructions,
            "tone": request.tone.value if request.tone else "warm_professional",
            "length": request.length.value if request.length else "medium",
            "extracted_job": {
                "company_name": application.company_name,
                "role_title": application.role_title,
            },
            "fit_summary": latest_fit.summary if latest_fit else "",
        }

        prompt = load_prompt("draft_bundle") + build_context_block(context)
        bundle: DraftBundle = provider.structured(prompt, DraftBundle)

        if not bundle.drafts:
            raise ValueError(
                f"Provider returned an empty bundle for draft type {request.type.value!r}"
            )

        item = bundle.drafts[0]
        draft_repo = DraftRepository(self._session)
        draft = draft_repo.create(
            application_id=application_id,
            type=item.type.value,
            title=item.title,
            body=item.body,
            status=DraftStatus.NEEDS_REVIEW.value,
            tone=request.tone.value if request.tone else None,
            length=request.length.value if request.length else None,
        )
        self._session.commit()
        return DraftRead.model_validate(draft)

    def list_graph_runs(
        self, application_id: uuid.UUID | None = None
    ) -> list[Any]:
        """Return graph runs, optionally filtered by *application_id*.

        Args:
            application_id: When provided, only runs for this application are
                returned; otherwise all runs are returned in descending start order.

        Returns:
            List of :class:`~applypilot.db.models.GraphRun` ORM objects.
        """
        run_repo = GraphRunRepository(self._session)
        if application_id is not None:
            return list(run_repo.list_by_application(application_id))
        stmt = select(GraphRun).order_by(GraphRun.started_at.desc())
        return list(self._session.execute(stmt).scalars().all())
