from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

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
            .options(joinedload(DocumentChunk.document), joinedload(DocumentChunk.venue))
            .order_by(DocumentChunk.chunk_index.asc(), DocumentChunk.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def list_for_retrieval(self, venue_ids: list[UUID] | None = None) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.document), joinedload(DocumentChunk.venue))
            .order_by(DocumentChunk.created_at.asc(), DocumentChunk.chunk_index.asc(), DocumentChunk.id.asc())
        )

        if venue_ids:
            stmt = stmt.where(DocumentChunk.venue_id.in_(venue_ids))

        return list(self.session.scalars(stmt).all())
