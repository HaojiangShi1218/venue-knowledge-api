from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.venue_repository import VenueRepository
from app.schemas.venue import VenueCreate, VenueListResponse, VenueRead
from app.services.exceptions import DuplicateResourceError
from app.services.venue_service import VenueFilters, VenueService

router = APIRouter(tags=["venues"])


def get_venue_service(db: Session = Depends(get_db)) -> VenueService:
    return VenueService(session=db, venue_repository=VenueRepository(db))


@router.post("/venues", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
def create_venue(
    payload: VenueCreate,
    service: VenueService = Depends(get_venue_service),
) -> VenueRead:
    try:
        return service.create_venue(payload)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/venues", response_model=VenueListResponse)
def list_venues(
    city: str | None = Query(default=None),
    neighborhood: str | None = Query(default=None),
    min_capacity: int | None = Query(default=None, ge=0),
    outside_catering: bool | None = Query(default=None),
    venue_type: str | None = Query(default=None),
    service: VenueService = Depends(get_venue_service),
) -> VenueListResponse:
    filters = VenueFilters(
        city=city,
        neighborhood=neighborhood,
        min_capacity=min_capacity,
        outside_catering=outside_catering,
        venue_type=venue_type,
    )
    items = service.list_venues(filters)
    return VenueListResponse(items=items, count=len(items))
