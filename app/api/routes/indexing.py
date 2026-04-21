from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.indexing import RunIndexingRequest, RunIndexingResponse
from app.services.exceptions import ResourceNotFoundError
from app.services.indexing_service import IndexingService

router = APIRouter(tags=["indexing"])


def get_indexing_service(db: Session = Depends(get_db)) -> IndexingService:
    return IndexingService(
        session=db,
        document_repository=DocumentRepository(db),
        chunk_repository=ChunkRepository(db),
    )


@router.post("/indexing/run", response_model=RunIndexingResponse)
def run_indexing(
    payload: RunIndexingRequest | None = Body(default=None),
    service: IndexingService = Depends(get_indexing_service),
) -> RunIndexingResponse:
    try:
        return service.run_indexing(payload or RunIndexingRequest())
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
