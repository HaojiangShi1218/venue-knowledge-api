from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.document import SourceDocument


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, document: SourceDocument) -> SourceDocument:
        self.session.add(document)
        return document

    def list(
        self,
        *,
        venue_id: UUID | None = None,
        document_type: str | None = None,
        ingestion_status: str | None = None,
    ) -> list[SourceDocument]:
        stmt: Select[tuple[SourceDocument]] = select(SourceDocument).order_by(SourceDocument.created_at.desc())

        if venue_id is not None:
            stmt = stmt.where(SourceDocument.venue_id == venue_id)
        if document_type is not None:
            stmt = stmt.where(SourceDocument.document_type == document_type)
        if ingestion_status is not None:
            stmt = stmt.where(SourceDocument.ingestion_status == ingestion_status)

        return list(self.session.scalars(stmt).all())

    def get_by_id(self, document_id: UUID) -> SourceDocument | None:
        stmt = select(SourceDocument).where(SourceDocument.id == document_id)
        return self.session.scalar(stmt)

    def get_by_external_id(self, external_doc_id: str) -> SourceDocument | None:
        stmt = select(SourceDocument).where(SourceDocument.external_doc_id == external_doc_id)
        return self.session.scalar(stmt)

    def get_by_ids(self, document_ids: list[UUID]) -> list[SourceDocument]:
        if not document_ids:
            return []

        stmt = select(SourceDocument).where(SourceDocument.id.in_(document_ids))
        return list(self.session.scalars(stmt).all())

    def list_pending_for_indexing(self) -> list[SourceDocument]:
        stmt = (
            select(SourceDocument)
            .where(SourceDocument.ingestion_status == "pending")
            .order_by(SourceDocument.created_at.asc(), SourceDocument.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def set_ingestion_status(self, document: SourceDocument, ingestion_status: str) -> SourceDocument:
        document.ingestion_status = ingestion_status
        self.session.add(document)
        return document
