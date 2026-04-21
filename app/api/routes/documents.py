from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.venue_repository import VenueRepository
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentRead,
    DocumentTypeEnum,
    IngestionStatusEnum,
)
from app.schemas.indexing import ChunkListResponse
from app.services.document_service import DocumentFilters, DocumentService
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError
from app.services.indexing_service import IndexingService

router = APIRouter(tags=["documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(
        session=db,
        document_repository=DocumentRepository(db),
        venue_repository=VenueRepository(db),
    )


def get_indexing_service(db: Session = Depends(get_db)) -> IndexingService:
    return IndexingService(
        session=db,
        document_repository=DocumentRepository(db),
        chunk_repository=ChunkRepository(db),
    )


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    try:
        return service.create_document(payload)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    venue_id: UUID | None = Query(default=None),
    document_type: DocumentTypeEnum | None = Query(default=None),
    ingestion_status: IngestionStatusEnum | None = Query(default=None),
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    filters = DocumentFilters(
        venue_id=venue_id,
        document_type=document_type.value if document_type else None,
        ingestion_status=ingestion_status.value if ingestion_status else None,
    )
    items = service.list_documents(filters)
    return DocumentListResponse(items=items, count=len(items))


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    try:
        return service.get_document(document_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
def list_document_chunks(
    document_id: UUID,
    service: IndexingService = Depends(get_indexing_service),
) -> ChunkListResponse:
    try:
        return service.list_document_chunks(document_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
