from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.query_repository import QueryRepository
from app.repositories.venue_repository import VenueRepository
from app.schemas.query import QueryLogResponse, QueryRequest, QueryResponse
from app.services.exceptions import ResourceNotFoundError
from app.services.query_service import QueryService
from app.services.retrieval_service import RetrievalService

router = APIRouter(tags=["queries"])


def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    retrieval_service = RetrievalService(
        venue_repository=VenueRepository(db),
        chunk_repository=ChunkRepository(db),
    )
    return QueryService(
        session=db,
        retrieval_service=retrieval_service,
        query_repository=QueryRepository(db),
    )


@router.post("/queries", response_model=QueryResponse)
def create_query(
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    return service.create_query(payload)


@router.get("/queries/{query_id}", response_model=QueryLogResponse)
def get_query(
    query_id: UUID,
    service: QueryService = Depends(get_query_service),
) -> QueryLogResponse:
    try:
        return service.get_query(query_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
