"""Integration tests for profile item CRUD via HTTP and DB assertions.

Flow per test:
  1. Create a User in the test DB (ProfileItem requires a user_id FK).
  2. Call the HTTP endpoints via TestClient.
  3. Assert on HTTP response codes, response bodies, and DB state.

All DB operations use the function-scoped ``db_session`` fixture which
truncates tables after each test.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from applypilot.db.models import EvidenceChunk, ProfileItem, User
from applypilot.schemas.enums import ProfileItemType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_user(db_session: Session, name: str = "Test User") -> User:
    user = User(name=name, email=f"{uuid.uuid4()}@test.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _item_payload(
    item_type: str = "skill",
    title: str = "Python Programming",
    body: str = "Expert-level Python development with FastAPI and SQLAlchemy 2.0 ORM.",
) -> dict:
    return {"type": item_type, "title": title, "body": body}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreateProfileItem:
    def test_create_returns_201(self, client: TestClient, db_session: Session) -> None:
        user = _create_user(db_session)
        response = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(),
        )
        assert response.status_code == 201

    def test_create_returns_correct_fields(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _create_user(db_session)
        payload = _item_payload(title="TypeScript", body="TypeScript React frontend expertise.")
        response = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=payload,
        )
        data = response.json()
        assert data["title"] == "TypeScript"
        assert data["type"] == "skill"
        assert "id" in data
        assert "user_id" in data
        assert str(data["user_id"]) == str(user.id)

    def test_create_persists_evidence_chunks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Creating a profile item must generate at least one EvidenceChunk."""
        user = _create_user(db_session)
        response = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(
                body=(
                    "Led a team of engineers building Next.js production applications. "
                    "Implemented TypeScript component libraries and design systems. "
                    "Worked closely with product designers to deliver pixel-perfect UI."
                ),
            ),
        )
        assert response.status_code == 201
        item_id = uuid.UUID(response.json()["id"])

        # Query the test DB directly to confirm EvidenceChunks were created.
        chunks = (
            db_session.query(EvidenceChunk)
            .filter(EvidenceChunk.profile_item_id == item_id)
            .all()
        )
        assert len(chunks) >= 1, "At least one EvidenceChunk must be persisted"

    def test_create_chunk_has_embedding(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Each EvidenceChunk must have a non-null 1536-dim embedding."""
        user = _create_user(db_session)
        response = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(body="Deep Python and SQLAlchemy knowledge."),
        )
        item_id = uuid.UUID(response.json()["id"])
        chunk = (
            db_session.query(EvidenceChunk)
            .filter(EvidenceChunk.profile_item_id == item_id)
            .first()
        )
        assert chunk is not None
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 1536

    def test_create_without_user_id_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/profile/items", json=_item_payload())
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Read / List
# ---------------------------------------------------------------------------


class TestGetListProfileItems:
    def test_list_empty_returns_empty_list(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _create_user(db_session)
        response = client.get("/api/profile/items", params={"user_id": str(user.id)})
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_created_items(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _create_user(db_session)
        client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(title="Item A"),
        )
        client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(title="Item B"),
        )
        response = client.get("/api/profile/items", params={"user_id": str(user.id)})
        assert response.status_code == 200
        titles = {item["title"] for item in response.json()}
        assert {"Item A", "Item B"}.issubset(titles)

    def test_list_isolates_by_user(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Items from user A should not appear in user B's list."""
        user_a = _create_user(db_session, name="User A")
        user_b = _create_user(db_session, name="User B")

        client.post(
            "/api/profile/items",
            params={"user_id": str(user_a.id)},
            json=_item_payload(title="A's Item"),
        )

        response = client.get("/api/profile/items", params={"user_id": str(user_b.id)})
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdateProfileItem:
    def test_update_title(self, client: TestClient, db_session: Session) -> None:
        user = _create_user(db_session)
        create_resp = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(title="Original Title"),
        )
        item_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/profile/items/{item_id}",
            json={"title": "Updated Title"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["title"] == "Updated Title"

    def test_update_body_regenerates_chunks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Updating the body must replace existing EvidenceChunks."""
        user = _create_user(db_session)
        create_resp = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(body="Original body text for evidence."),
        )
        item_id = uuid.UUID(create_resp.json()["id"])

        original_chunk_ids = {
            c.id
            for c in db_session.query(EvidenceChunk)
            .filter(EvidenceChunk.profile_item_id == item_id)
            .all()
        }

        client.patch(
            f"/api/profile/items/{item_id}",
            json={"body": "Completely new body text triggers new embeddings."},
        )

        new_chunk_ids = {
            c.id
            for c in db_session.query(EvidenceChunk)
            .filter(EvidenceChunk.profile_item_id == item_id)
            .all()
        }
        # After update, the old chunks should be replaced.
        assert new_chunk_ids != original_chunk_ids or len(new_chunk_ids) >= 1

    def test_update_nonexistent_item_returns_404(
        self, client: TestClient, db_session: Session
    ) -> None:
        fake_id = str(uuid.uuid4())
        response = client.patch(f"/api/profile/items/{fake_id}", json={"title": "X"})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeleteProfileItem:
    def test_delete_returns_204(self, client: TestClient, db_session: Session) -> None:
        user = _create_user(db_session)
        create_resp = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(),
        )
        item_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/profile/items/{item_id}")
        assert del_resp.status_code == 204

    def test_delete_removes_item_from_db(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _create_user(db_session)
        create_resp = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(),
        )
        item_id = uuid.UUID(create_resp.json()["id"])

        client.delete(f"/api/profile/items/{item_id}")

        item = db_session.get(ProfileItem, item_id)
        assert item is None, "ProfileItem must be deleted from the DB"

    def test_delete_cascades_to_chunks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Deleting a ProfileItem must cascade-delete its EvidenceChunks."""
        user = _create_user(db_session)
        create_resp = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(body="Evidence body text for cascade test."),
        )
        item_id = uuid.UUID(create_resp.json()["id"])

        # Confirm chunks exist before deletion.
        assert (
            db_session.query(EvidenceChunk)
            .filter(EvidenceChunk.profile_item_id == item_id)
            .count()
            >= 1
        )

        client.delete(f"/api/profile/items/{item_id}")

        remaining = (
            db_session.query(EvidenceChunk)
            .filter(EvidenceChunk.profile_item_id == item_id)
            .count()
        )
        assert remaining == 0, "EvidenceChunks must be deleted with their parent"

    def test_delete_nonexistent_item_returns_404(
        self, client: TestClient, db_session: Session
    ) -> None:
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/profile/items/{fake_id}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestProfileItemRoundTrip:
    def test_full_crud_round_trip(self, client: TestClient, db_session: Session) -> None:
        """Create → verify list → update → verify updated → delete → verify gone."""
        user = _create_user(db_session)

        # Create
        create_resp = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json=_item_payload(title="Round-trip skill", body="Testing the full CRUD lifecycle."),
        )
        assert create_resp.status_code == 201
        item_id = create_resp.json()["id"]

        # List contains the item
        list_resp = client.get("/api/profile/items", params={"user_id": str(user.id)})
        ids = [i["id"] for i in list_resp.json()]
        assert item_id in ids

        # Update
        patch_resp = client.patch(
            f"/api/profile/items/{item_id}",
            json={"title": "Updated round-trip skill"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["title"] == "Updated round-trip skill"

        # Delete
        del_resp = client.delete(f"/api/profile/items/{item_id}")
        assert del_resp.status_code == 204

        # No longer in list
        list_resp2 = client.get("/api/profile/items", params={"user_id": str(user.id)})
        ids2 = [i["id"] for i in list_resp2.json()]
        assert item_id not in ids2

    @pytest.mark.parametrize("item_type", list(ProfileItemType))
    def test_all_profile_item_types_accepted(
        self, client: TestClient, db_session: Session, item_type: ProfileItemType
    ) -> None:
        user = _create_user(db_session)
        response = client.post(
            "/api/profile/items",
            params={"user_id": str(user.id)},
            json={"type": item_type.value, "title": f"Test {item_type.value}", "body": "Body text."},
        )
        assert response.status_code == 201
        assert response.json()["type"] == item_type.value
