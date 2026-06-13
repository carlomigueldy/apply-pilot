"""Integration tests for profile semantic search.

Tests POST /api/profile/search by:
1. Seeding the test DB with domain-specific profile items via ProfileService.
2. Issuing HTTP search requests via the TestClient.
3. Asserting that the correct items appear in the top results.

The FakeEmbeddingProvider is used (via the test fixture settings) so that
shared keyword tokens reliably rank related items above unrelated ones.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from applypilot.db.models import User
from applypilot.schemas.enums import ProfileItemType
from applypilot.schemas.profile import ProfileItemCreate
from applypilot.services.profile_service import ProfileService

# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _make_user(db_session: Session) -> User:
    user = User(name="Search Test User", email=f"{uuid.uuid4()}@test.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_frontend_item(service: ProfileService, user_id: uuid.UUID) -> str:
    """Seed a frontend engineering profile item; returns item id."""
    item = service.create_item(
        user_id=user_id,
        data=ProfileItemCreate(
            type=ProfileItemType.ROLE,
            title="Senior Frontend Engineer at TechCorp",
            body=(
                "Led Next.js production deployments serving 500k daily active users. "
                "Architected a React component library adopted across 6 product teams. "
                "Championed TypeScript migration from JavaScript for type safety. "
                "Mentored junior engineers on frontend best practices and performance. "
                "Improved Core Web Vitals by 40% through code-splitting and lazy loading."
            ),
        ),
    )
    return str(item.id)


def _seed_web3_item(service: ProfileService, user_id: uuid.UUID) -> str:
    """Seed a blockchain/Web3 engineering profile item; returns item id."""
    item = service.create_item(
        user_id=user_id,
        data=ProfileItemCreate(
            type=ProfileItemType.PROJECT,
            title="Web3 DeFi Protocol Engineering",
            body=(
                "Designed and deployed Solidity smart contracts for a DeFi lending protocol. "
                "Integrated Web3 wallet connections with wagmi and ethers.js libraries. "
                "Implemented Ethereum blockchain event listeners and indexing pipelines. "
                "Conducted Solidity security audits and fixed reentrancy vulnerabilities. "
                "Led Web3 engineering team of 4 to ship Ethereum mainnet contracts."
            ),
        ),
    )
    return str(item.id)


def _seed_ai_item(service: ProfileService, user_id: uuid.UUID) -> str:
    """Seed an AI/ML engineering profile item; returns item id."""
    item = service.create_item(
        user_id=user_id,
        data=ProfileItemCreate(
            type=ProfileItemType.PROJECT,
            title="AI Agents and RAG Pipeline Architecture",
            body=(
                "Built production LangGraph AI agents for multi-step document reasoning. "
                "Designed RAG retrieval pipeline with pgvector embeddings and reranking. "
                "Fine-tuned LLM prompts for structured extraction with 92% precision. "
                "Integrated OpenAI and Anthropic APIs with retry and fallback logic. "
                "Shipped agentic AI features adopted by 200+ enterprise customers."
            ),
        ),
    )
    return str(item.id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProfileSearch:
    def test_nextjs_query_returns_frontend_item(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Query 'Next.js production experience' must surface the frontend item."""
        user = _make_user(db_session)
        service = ProfileService(db_session)
        frontend_id = _seed_frontend_item(service, user.id)
        _seed_web3_item(service, user.id)
        _seed_ai_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "Next.js production experience", "top_k": 5},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) > 0, "Search must return at least one result"

        assert results[0]["profile_item_id"] == frontend_id, (
            "Frontend item must be the TOP result for 'Next.js production experience'; "
            f"got {[(r['title'], r['score']) for r in results[:3]]}"
        )

    def test_web3_query_returns_blockchain_item(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Query 'Web3 engineering' must surface the blockchain/DeFi item."""
        user = _make_user(db_session)
        service = ProfileService(db_session)
        _seed_frontend_item(service, user.id)
        web3_id = _seed_web3_item(service, user.id)
        _seed_ai_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "Web3 engineering Ethereum blockchain", "top_k": 5},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) > 0

        assert results[0]["profile_item_id"] == web3_id, (
            "Web3 item must be the TOP result for the Web3/Ethereum/blockchain query; "
            f"got {[(r['title'], r['score']) for r in results[:3]]}"
        )

    def test_ai_agents_query_returns_ai_item(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Query 'AI agents' must surface the LangGraph/RAG item."""
        user = _make_user(db_session)
        service = ProfileService(db_session)
        _seed_frontend_item(service, user.id)
        _seed_web3_item(service, user.id)
        ai_id = _seed_ai_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "AI agents LLM RAG pipeline", "top_k": 5},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) > 0

        assert results[0]["profile_item_id"] == ai_id, (
            "AI item must be the TOP result for the AI agents/LLM/RAG query; "
            f"got {[(r['title'], r['score']) for r in results[:3]]}"
        )

    def test_search_response_schema(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Each result must have the required RetrievedEvidence fields."""
        user = _make_user(db_session)
        service = ProfileService(db_session)
        _seed_frontend_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "Next.js frontend React", "top_k": 3},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) > 0

        required_fields = {
            "evidence_chunk_id",
            "profile_item_id",
            "title",
            "snippet",
            "score",
            "source_type",
        }
        for result in results:
            missing = required_fields - result.keys()
            assert not missing, f"Result missing fields: {missing}"

    def test_search_scores_are_positive(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        service = ProfileService(db_session)
        _seed_frontend_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "Next.js React", "top_k": 5},
        )
        results = response.json()["results"]
        for r in results:
            assert r["score"] >= 0.0, "All scores must be non-negative"

    def test_search_top_k_limits_results(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        service = ProfileService(db_session)
        _seed_frontend_item(service, user.id)
        _seed_web3_item(service, user.id)
        _seed_ai_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "engineering experience", "top_k": 2},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) <= 2, "top_k=2 must return at most 2 results"

    def test_search_empty_db_returns_empty_results(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.post(
            "/api/profile/search",
            json={"query": "Python engineer", "top_k": 5},
        )
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_frontend_ranks_higher_than_web3_for_nextjs_query(
        self, client: TestClient, db_session: Session
    ) -> None:
        """The frontend item should have a higher score than the web3 item for Next.js query."""
        user = _make_user(db_session)
        service = ProfileService(db_session)
        frontend_id = _seed_frontend_item(service, user.id)
        web3_id = _seed_web3_item(service, user.id)
        _seed_ai_item(service, user.id)

        response = client.post(
            "/api/profile/search",
            json={"query": "Next.js production experience", "top_k": 10},
        )
        results = response.json()["results"]
        id_to_score = {r["profile_item_id"]: r["score"] for r in results}

        if frontend_id in id_to_score and web3_id in id_to_score:
            assert id_to_score[frontend_id] >= id_to_score[web3_id], (
                "Frontend item must rank higher than Web3 item for Next.js query"
            )
