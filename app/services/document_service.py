from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.document import SourceDocument
from app.repositories.document_repository import DocumentRepository
from app.repositories.venue_repository import VenueRepository
from app.schemas.document import DocumentCreate
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError


@dataclass(slots=True)
class DocumentFilters:
    venue_id: UUID | None = None
    document_type: str | None = None
    ingestion_status: str | None = None


class DocumentService:
    def __init__(
        self,
        *,
        session: Session,
        document_repository: DocumentRepository,
        venue_repository: VenueRepository,
    ) -> None:
        self.session = session
        self.document_repository = document_repository
        self.venue_repository = venue_repository

    def create_document(self, payload: DocumentCreate) -> SourceDocument:
        if payload.external_doc_id and self.document_repository.get_by_external_id(payload.external_doc_id):
            raise DuplicateResourceError("Document external_doc_id already exists")

        if payload.venue_id and self.venue_repository.get_by_id(payload.venue_id) is None:
            raise ResourceNotFoundError("Venue not found")

        document = SourceDocument(
            external_doc_id=payload.external_doc_id,
            venue_id=payload.venue_id,
            title=payload.title,
            document_type=payload.document_type.value,
            content=payload.content,
        )
        self.document_repository.create(document)

        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateResourceError("Document external_doc_id already exists") from exc

        self.session.refresh(document)
        return document

    def list_documents(self, filters: DocumentFilters) -> list[SourceDocument]:
        return self.document_repository.list(
            venue_id=filters.venue_id,
            document_type=filters.document_type,
            ingestion_status=filters.ingestion_status,
        )

    def get_document(self, document_id: UUID) -> SourceDocument:
        document = self.document_repository.get_by_id(document_id)
        if document is None:
            raise ResourceNotFoundError("Document not found")
        return document
