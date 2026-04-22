from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.api.routes.queries import get_query_service
from app.schemas.query import QueryLogResponse, QueryResponse, QuerySourceResponse
from app.services.exceptions import ResourceNotFoundError


QUERY_ID = UUID("88888888-8888-8888-8888-888888888888")
CHUNK_ID = UUID("99999999-9999-9999-9999-999999999999")
DOCUMENT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
VENUE_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


class StubQueryService:
    def create_query(self, payload) -> QueryResponse:
        return QueryResponse(
            query_id=QUERY_ID,
            answer="Harbor Loft allows outside catering with prior approval.",
            confidence_score=0.86,
            sources=[
                QuerySourceResponse(
                    document_id=DOCUMENT_ID,
                    chunk_id=CHUNK_ID,
                    venue_id=VENUE_ID,
                    venue_name="Harbor Loft",
                    document_title="Harbor Loft Policies",
                    document_type="policy",
                    excerpt="Harbor Loft allows outside catering with prior approval.",
                    rank=1,
                    relevance_score=0.91,
                )
            ],
        )

    def get_query(self, query_id) -> QueryLogResponse:
        if query_id != QUERY_ID:
            raise ResourceNotFoundError("Query not found")

        return QueryLogResponse(
            query_id=QUERY_ID,
            question="Which venues allow outside catering?",
            answer="Harbor Loft allows outside catering with prior approval.",
            confidence_score=0.86,
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
            sources=[
                QuerySourceResponse(
                    document_id=DOCUMENT_ID,
                    chunk_id=CHUNK_ID,
                    venue_id=VENUE_ID,
                    venue_name="Harbor Loft",
                    document_title="Harbor Loft Policies",
                    document_type="policy",
                    excerpt="Harbor Loft allows outside catering with prior approval.",
                    rank=1,
                    relevance_score=0.91,
                )
            ],
        )


def test_create_query_endpoint_returns_answer_and_sources(client) -> None:
    from app.main import app

    app.dependency_overrides[get_query_service] = lambda: StubQueryService()

    response = client.post("/queries", json={"question": "Which venues allow outside catering?"})

    assert response.status_code == 200
    assert response.json()["query_id"] == str(QUERY_ID)
    assert response.json()["sources"][0]["venue_name"] == "Harbor Loft"


def test_get_query_endpoint_returns_404_for_missing_query(client) -> None:
    from app.main import app

    app.dependency_overrides[get_query_service] = lambda: StubQueryService()

    response = client.get("/queries/cccccccc-cccc-cccc-cccc-cccccccccccc")

    assert response.status_code == 404
    assert response.json() == {"detail": "Query not found"}
