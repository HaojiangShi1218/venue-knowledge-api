from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chunk import DocumentChunk
from app.models.document import SourceDocument
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.indexing import ChunkListResponse, RunIndexingRequest, RunIndexingResponse
from app.services.exceptions import ResourceNotFoundError
from app.utils.chunking import chunk_text
from app.utils.text_normalization import normalize_text


class IndexingService:
    def __init__(
        self,
        *,
        session: Session,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
    ) -> None:
        self.session = session
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.settings = get_settings()

    def run_indexing(self, payload: RunIndexingRequest) -> RunIndexingResponse:
        target_documents = self._resolve_target_documents(payload.document_ids)

        indexed_documents = 0
        created_chunks = 0
        failed_documents = 0

        for document in target_documents:
            try:
                created_for_document = self._index_document(document.id)
            except Exception:
                self.session.rollback()
                self._mark_document_failed(document.id)
                failed_documents += 1
                continue

            indexed_documents += 1
            created_chunks += created_for_document

        return RunIndexingResponse(
            indexed_documents=indexed_documents,
            created_chunks=created_chunks,
            failed_documents=failed_documents,
        )

    def list_document_chunks(self, document_id: UUID) -> ChunkListResponse:
        document = self.document_repository.get_by_id(document_id)
        if document is None:
            raise ResourceNotFoundError("Document not found")

        chunks = self.chunk_repository.list_by_document_id(document_id)
        return ChunkListResponse(items=chunks, count=len(chunks))

    def _resolve_target_documents(self, document_ids: list[UUID]) -> list[SourceDocument]:
        unique_ids = list(dict.fromkeys(document_ids))

        if not unique_ids:
            return self.document_repository.list_pending_for_indexing()

        documents = self.document_repository.get_by_ids(unique_ids)
        documents_by_id = {document.id: document for document in documents}

        if len(documents_by_id) != len(unique_ids):
            raise ResourceNotFoundError("One or more documents not found")

        return [documents_by_id[document_id] for document_id in unique_ids]

    def _index_document(self, document_id: UUID) -> int:
        document = self.document_repository.get_by_id(document_id)
        if document is None:
            raise ResourceNotFoundError("One or more documents not found")

        chunks = chunk_text(
            document.content,
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP,
        )
        chunk_rows = [
            DocumentChunk(
                document_id=document.id,
                venue_id=document.venue_id,
                chunk_index=chunk_index,
                content=chunk_content,
                normalized_content=normalize_text(chunk_content),
                document_title=document.title,
                document_type=document.document_type,
            )
            for chunk_index, chunk_content in enumerate(chunks)
        ]

        self.chunk_repository.delete_by_document_id(document.id)
        self.chunk_repository.bulk_create(chunk_rows)
        self.document_repository.set_ingestion_status(document, "indexed")
        self.session.commit()

        return len(chunk_rows)

    def _mark_document_failed(self, document_id: UUID) -> None:
        try:
            document = self.document_repository.get_by_id(document_id)
            if document is None:
                return
            self.document_repository.set_ingestion_status(document, "failed")
            self.session.commit()
        except Exception:
            self.session.rollback()
