"""Seed script for ApplyPilot demo data.

Usage::

    python -m applypilot.seeds.seed [--reset]

``--reset`` truncates all tables (via CASCADE) before inserting seed rows,
making the script safe to re-run from a clean state.

Without ``--reset`` the script is idempotent: each entity is looked up by its
fixed UUID before insertion; existing rows are skipped.

Implementation notes:

* All DB access is **synchronous** (``SessionLocal``).
* Profile item bodies are chunked into paragraph-aware text segments and
  embedded with the single canonical provider returned by
  :func:`applypilot.agents.llm.factory.get_embedding_provider`. Using the same
  provider as live search is what makes cosine similarity meaningful between
  seeded chunks and search queries.
"""

from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from applypilot.agents.llm.base import EmbeddingProvider
from applypilot.agents.llm.factory import get_embedding_provider
from applypilot.core.config import get_settings
from applypilot.db.models import Draft, EvidenceChunk, JobApplication, ProfileItem, User
from applypilot.db.session import SessionLocal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"

# Tables ordered so that children are deleted before parents (for manual
# DELETE fallback), though TRUNCATE ... CASCADE makes this ordering
# unnecessary when the DBMS supports it.
_ALL_TABLES = [
    "review_decisions",
    "graph_runs",
    "drafts",
    "evidence_matches",
    "fit_analyses",
    "job_requirements",
    "job_applications",
    "evidence_chunks",
    "profile_items",
    "users",
]


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------


def _chunk_text(text_input: str, max_chars: int = 600, overlap: int = 80) -> list[str]:
    """Split *text_input* into overlapping paragraph-aware chunks.

    Paragraphs (double-newline-separated) are accumulated until adding the next
    paragraph would exceed *max_chars*, at which point the current chunk is
    flushed and a new one starts — optionally carrying the last paragraph as an
    overlap prefix.  Single paragraphs that exceed *max_chars* are hard-split.

    Returns at least one chunk even for empty / very short inputs.
    """
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text_input) if p.strip()]
    if not paragraphs:
        return [text_input.strip()[:max_chars]] if text_input.strip() else [""]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for para in paragraphs:
        # +2 accounts for the "\n\n" separator when joining
        if current_parts and current_len + len(para) + 2 > max_chars:
            chunks.append("\n\n".join(current_parts))
            # Carry overlap: keep last part if small enough
            if current_parts and len(current_parts[-1]) <= overlap:
                current_parts = [current_parts[-1]]
                current_len = len(current_parts[-1])
            else:
                current_parts = []
                current_len = 0

        if len(para) > max_chars:
            # Hard-split an oversized single paragraph
            for start in range(0, len(para), max_chars - overlap):
                chunks.append(para[start : start + max_chars])
        else:
            current_parts.append(para)
            current_len += len(para) + 2

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks or [text_input[:max_chars]]


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def _reset_tables(session: Session) -> None:
    """Truncate every application table, cascading to all dependents."""
    table_list = ", ".join(_ALL_TABLES)
    session.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))
    session.commit()
    print("  [reset] All tables truncated.")


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def _load_json(filename: str) -> Any:
    path = _DATA_DIR / filename
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------


def _seed_user(session: Session, data: dict[str, Any]) -> User:
    """Insert the demo user if not already present; return the User ORM object."""
    user_data: dict[str, Any] = data["user"]
    user_id = uuid.UUID(user_data["id"])

    existing = session.get(User, user_id)
    if existing is not None:
        print(f"  [skip] User already exists: {existing.name}")
        return existing

    user = User(
        id=user_id,
        name=user_data["name"],
        email=user_data.get("email"),
        timezone=user_data.get("timezone"),
        target_salary_min_usd=user_data.get("target_salary_min_usd"),
        target_salary_max_usd=user_data.get("target_salary_max_usd"),
        remote_preference=user_data.get("remote_preference"),
        preferred_tone=user_data.get("preferred_tone"),
    )
    session.add(user)
    session.flush()
    print(f"  [insert] User: {user.name}  ({user.id})")
    return user


def _seed_profile_items(
    session: Session,
    user: User,
    data: dict[str, Any],
    provider: EmbeddingProvider,
) -> tuple[int, int]:
    """Insert profile items and their embedded evidence chunks.

    Returns ``(items_inserted, chunks_inserted)``.
    """
    items_data: list[dict[str, Any]] = data["profile_items"]
    items_inserted = 0
    chunks_inserted = 0

    for item_data in items_data:
        item_id = uuid.UUID(item_data["id"])
        if session.get(ProfileItem, item_id) is not None:
            continue

        item = ProfileItem(
            id=item_id,
            user_id=user.id,
            type=item_data["type"],
            title=item_data["title"],
            body=item_data["body"],
            item_metadata=item_data.get("item_metadata") or {},
        )
        session.add(item)
        session.flush()  # obtain item.id before creating chunks

        body: str = item_data["body"]
        chunks = _chunk_text(body)
        for idx, chunk_text in enumerate(chunks):
            embedding = provider.embed_text(chunk_text)
            chunk = EvidenceChunk(
                profile_item_id=item_id,
                chunk_text=chunk_text,
                chunk_index=idx,
                embedding=embedding,
                chunk_metadata={
                    "source_title": item_data["title"],
                    "source_type": item_data["type"],
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
            )
            session.add(chunk)
            chunks_inserted += 1

        items_inserted += 1

    session.flush()
    return items_inserted, chunks_inserted


def _seed_job_applications(
    session: Session,
    user: User,
    data: dict[str, Any],
) -> int:
    """Insert job applications; return the count of rows inserted."""
    apps_data: list[dict[str, Any]] = data["job_applications"]
    inserted = 0

    for app_data in apps_data:
        app_id = uuid.UUID(app_data["id"])
        if session.get(JobApplication, app_id) is not None:
            continue

        app = JobApplication(
            id=app_id,
            user_id=user.id,
            company_name=app_data.get("company_name"),
            role_title=app_data.get("role_title"),
            job_url=app_data.get("job_url"),
            raw_job_post=app_data["raw_job_post"],
            status=app_data.get("status", "saved"),
            work_arrangement=app_data.get("work_arrangement"),
            salary_text=app_data.get("salary_text"),
            timezone_text=app_data.get("timezone_text"),
            recruiter_name=app_data.get("recruiter_name"),
            recruiter_email=app_data.get("recruiter_email"),
        )
        session.add(app)
        inserted += 1

    session.flush()
    return inserted


def _seed_drafts(session: Session, data: dict[str, Any]) -> int:
    """Insert draft documents; return the count of rows inserted."""
    drafts_data: list[dict[str, Any]] = data.get("drafts", [])
    inserted = 0

    for draft_data in drafts_data:
        draft_id = uuid.UUID(draft_data["id"])
        if session.get(Draft, draft_id) is not None:
            continue

        draft = Draft(
            id=draft_id,
            application_id=uuid.UUID(draft_data["application_id"]),
            type=draft_data["type"],
            title=draft_data["title"],
            body=draft_data["body"],
            status=draft_data.get("status", "generated"),
            version=draft_data.get("version", 1),
            tone=draft_data.get("tone"),
            length=draft_data.get("length"),
            review_notes=draft_data.get("review_notes"),
        )
        session.add(draft)
        inserted += 1

    session.flush()
    return inserted


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments and run the seed pipeline."""
    parser = argparse.ArgumentParser(
        description="Seed ApplyPilot with deterministic demo data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m applypilot.seeds.seed          # idempotent insert\n"
            "  python -m applypilot.seeds.seed --reset  # truncate then insert\n"
        ),
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate all application tables before seeding (destructive).",
    )
    args = parser.parse_args()

    settings = get_settings()
    provider = get_embedding_provider(settings)
    db_url_preview = settings.database_url[:60]
    print(f"ApplyPilot seed  |  database: {db_url_preview}...")

    profile_data = _load_json("profile.seed.json")
    jobs_data = _load_json("jobs.seed.json")
    drafts_data = _load_json("drafts.seed.json")

    session: Session = SessionLocal()
    try:
        if args.reset:
            print("Resetting all tables …")
            _reset_tables(session)

        print("Seeding …")
        user = _seed_user(session, profile_data)
        n_items, n_chunks = _seed_profile_items(session, user, profile_data, provider)
        n_apps = _seed_job_applications(session, user, jobs_data)
        n_drafts = _seed_drafts(session, drafts_data)

        session.commit()

        print(
            f"\nDone.  1 user | {n_items} profile items"
            f" | {n_chunks} evidence chunks"
            f" | {n_apps} job applications"
            f" | {n_drafts} drafts"
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
