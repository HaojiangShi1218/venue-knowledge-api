from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.chunk import DocumentChunk
from app.schemas.indexing import RunIndexingRequest
from app.services.exceptions import ResourceNotFoundError
from app.services.indexing_service import IndexingService


DOC_ONE_ID = UUID("55555555-5555-5555-5555-555555555555")
DOC_TWO_ID = UUID("66666666-6666-6666-6666-666666666666")
VENUE_ID = UUID("77777777-7777-7777-7777-777777777777")


@dataclass
class FakeDocument:
    id: UUID
    title: str
    document_type: str
    content: str
    ingestion_status: str = "pending"
    venue_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FakeDocumentRepository:
    def __init__(self, documents: list[FakeDocument]) -> None:
        self.documents = {document.id: document for document in documents}

    def get_by_id(self, document_id: UUID) -> FakeDocument | None:
        return self.documents.get(document_id)

    def get_by_ids(self, document_ids: list[UUID]) -> list[FakeDocument]:
        return [self.documents[document_id] for document_id in document_ids if document_id in self.documents]

    def list_pending_for_indexing(self) -> list[FakeDocument]:
        return [
            document
            for document in sorted(self.documents.values(), key=lambda item: (item.created_at, item.id))
            if document.ingestion_status == "pending"
        ]

    def set_ingestion_status(self, document: FakeDocument, ingestion_status: str) -> FakeDocument:
        document.ingestion_status = ingestion_status
        return document


class FakeChunkRepository:
    def __init__(self, chunks: list[DocumentChunk] | None = None) -> None:
        self.chunks = list(chunks or [])

    def delete_by_document_id(self, document_id: UUID) -> None:
        self.chunks = [chunk for chunk in self.chunks if chunk.document_id != document_id]

    def bulk_create(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        self.chunks.extend(chunks)
        return chunks

    def list_by_document_id(self, document_id: UUID) -> list[DocumentChunk]:
        return sorted(
            [chunk for chunk in self.chunks if chunk.document_id == document_id],
            key=lambda chunk: chunk.chunk_index,
        )


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def make_service(
    documents: list[FakeDocument],
    *,
    chunks: list[DocumentChunk] | None = None,
    chunk_size: int = 40,
    chunk_overlap: int = 10,
) -> tuple[IndexingService, FakeDocumentRepository, FakeChunkRepository, FakeSession]:
    document_repository = FakeDocumentRepository(documents)
    chunk_repository = FakeChunkRepository(chunks)
    session = FakeSession()
    service = IndexingService(
        session=session,
        document_repository=document_repository,
        chunk_repository=chunk_repository,
    )
    service.settings.CHUNK_SIZE = chunk_size
    service.settings.CHUNK_OVERLAP = chunk_overlap
    return service, document_repository, chunk_repository, session


def test_indexing_pending_document_creates_chunks_and_marks_indexed() -> None:
    document = FakeDocument(
        id=DOC_ONE_ID,
        title="Skyline Foundry FAQ",
        document_type="faq",
        venue_id=VENUE_ID,
        content="Skyline Foundry supports startup mixers. Outside catering is not allowed.",
    )
    service, document_repository, chunk_repository, _session = make_service([document], chunk_size=30, chunk_overlap=5)

    response = service.run_indexing(RunIndexingRequest())

    assert response.indexed_documents == 1
    assert response.failed_documents == 0
    assert response.created_chunks == len(chunk_repository.list_by_document_id(DOC_ONE_ID))
    assert response.created_chunks > 0
    assert document_repository.get_by_id(DOC_ONE_ID).ingestion_status == "indexed"

    created_chunks = chunk_repository.list_by_document_id(DOC_ONE_ID)
    assert [chunk.chunk_index for chunk in created_chunks] == list(range(len(created_chunks)))
    assert all(chunk.normalized_content for chunk in created_chunks)
    assert created_chunks[0].document_title == "Skyline Foundry FAQ"
    assert created_chunks[0].document_type == "faq"


def test_reindexing_replaces_old_chunks_instead_of_duplicating() -> None:
    document = FakeDocument(
        id=DOC_ONE_ID,
        title="Harbor Loft Policies",
        document_type="policy",
        content="Harbor Loft allows outside catering with prior approval.",
    )
    existing_chunk = DocumentChunk(
        id=uuid4(),
        document_id=DOC_ONE_ID,
        venue_id=None,
        chunk_index=0,
        content="old",
        normalized_content="old",
        document_title="Old Title",
        document_type="policy",
    )
    service, _document_repository, chunk_repository, _session = make_service(
        [document],
        chunks=[existing_chunk],
        chunk_size=25,
        chunk_overlap=5,
    )

    response = service.run_indexing(RunIndexingRequest(document_ids=[DOC_ONE_ID]))
    created_chunks = chunk_repository.list_by_document_id(DOC_ONE_ID)

    assert response.indexed_documents == 1
    assert len(created_chunks) == response.created_chunks
    assert all(chunk.content != "old" for chunk in created_chunks)


def test_list_document_chunks_returns_chunks_ordered_by_chunk_index() -> None:
    document = FakeDocument(
        id=DOC_ONE_ID,
        title="Cambridge Private Table Notes",
        document_type="notes",
        content="content",
    )
    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=DOC_ONE_ID,
            venue_id=None,
            chunk_index=2,
            content="third",
            normalized_content="third",
            document_title=document.title,
            document_type=document.document_type,
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=DOC_ONE_ID,
            venue_id=None,
            chunk_index=0,
            content="first",
            normalized_content="first",
            document_title=document.title,
            document_type=document.document_type,
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=DOC_ONE_ID,
            venue_id=None,
            chunk_index=1,
            content="second",
            normalized_content="second",
            document_title=document.title,
            document_type=document.document_type,
        ),
    ]
    service, _document_repository, _chunk_repository, _session = make_service([document], chunks=chunks)

    response = service.list_document_chunks(DOC_ONE_ID)

    assert response.count == 3
    assert [chunk.chunk_index for chunk in response.items] == [0, 1, 2]


def test_run_indexing_raises_not_found_for_missing_explicit_document_ids() -> None:
    service, _document_repository, _chunk_repository, _session = make_service([])

    try:
        service.run_indexing(RunIndexingRequest(document_ids=[DOC_TWO_ID]))
    except ResourceNotFoundError as exc:
        assert str(exc) == "One or more documents not found"
    else:
        raise AssertionError("Expected ResourceNotFoundError for missing document IDs")
