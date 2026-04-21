from __future__ import annotations

from uuid import UUID, uuid4

from app.api.routes.documents import get_indexing_service as get_document_indexing_service
from app.api.routes.indexing import get_indexing_service as get_run_indexing_service
from app.schemas.indexing import ChunkListResponse, ChunkResponse, RunIndexingResponse
from app.services.exceptions import ResourceNotFoundError


DOCUMENT_ID = UUID("33333333-3333-3333-3333-333333333333")
CHUNK_ID = UUID("44444444-4444-4444-4444-444444444444")


class StubIndexingService:
    def __init__(self, *, missing_document: bool = False) -> None:
        self.missing_document = missing_document

    def run_indexing(self, payload) -> RunIndexingResponse:
        if payload.document_ids:
            raise ResourceNotFoundError("One or more documents not found")

        return RunIndexingResponse(
            indexed_documents=1,
            created_chunks=2,
            failed_documents=0,
        )

    def list_document_chunks(self, document_id) -> ChunkListResponse:
        if self.missing_document:
            raise ResourceNotFoundError("Document not found")

        items = [
            ChunkResponse(
                id=CHUNK_ID,
                document_id=document_id,
                venue_id=None,
                chunk_index=0,
                content="First chunk",
                document_title="Skyline Foundry FAQ",
                document_type="faq",
            ),
            ChunkResponse(
                id=uuid4(),
                document_id=document_id,
                venue_id=None,
                chunk_index=1,
                content="Second chunk",
                document_title="Skyline Foundry FAQ",
                document_type="faq",
            ),
        ]
        return ChunkListResponse(items=items, count=len(items))


def test_run_indexing_endpoint_returns_200_for_pending_documents(client) -> None:
    from app.main import app

    app.dependency_overrides[get_run_indexing_service] = lambda: StubIndexingService()

    response = client.post("/indexing/run")

    assert response.status_code == 200
    assert response.json() == {
        "indexed_documents": 1,
        "created_chunks": 2,
        "failed_documents": 0,
    }


def test_run_indexing_endpoint_returns_404_for_missing_explicit_document_ids(client) -> None:
    from app.main import app

    app.dependency_overrides[get_run_indexing_service] = lambda: StubIndexingService()

    response = client.post("/indexing/run", json={"document_ids": [str(DOCUMENT_ID)]})

    assert response.status_code == 404
    assert response.json() == {"detail": "One or more documents not found"}


def test_list_document_chunks_endpoint_returns_ordered_chunks(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_indexing_service] = lambda: StubIndexingService()

    response = client.get(f"/documents/{DOCUMENT_ID}/chunks")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert [item["chunk_index"] for item in response.json()["items"]] == [0, 1]
    assert "normalized_content" not in response.json()["items"][0]


def test_list_document_chunks_endpoint_returns_404_for_missing_document(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_indexing_service] = lambda: StubIndexingService(
        missing_document=True
    )

    response = client.get(f"/documents/{DOCUMENT_ID}/chunks")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}
