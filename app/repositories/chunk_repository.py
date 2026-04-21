from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk


class ChunkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def delete_by_document_id(self, document_id: UUID) -> None:
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        self.session.execute(stmt)

    def bulk_create(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        self.session.add_all(chunks)
        return chunks

    def list_by_document_id(self, document_id: UUID) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc(), DocumentChunk.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())
