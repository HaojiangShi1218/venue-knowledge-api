from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.venue import Venue
from app.repositories.venue_repository import VenueRepository
from app.schemas.venue import VenueCreate
from app.services.exceptions import DuplicateResourceError


@dataclass(slots=True)
class VenueFilters:
    city: str | None = None
    neighborhood: str | None = None
    min_capacity: int | None = None
    outside_catering: bool | None = None
    venue_type: str | None = None


class VenueService:
    def __init__(self, *, session: Session, venue_repository: VenueRepository) -> None:
        self.session = session
        self.venue_repository = venue_repository

    def create_venue(self, payload: VenueCreate) -> Venue:
        if payload.external_id and self.venue_repository.get_by_external_id(payload.external_id):
            raise DuplicateResourceError("Venue external_id already exists")

        venue = Venue(
            external_id=payload.external_id,
            name=payload.name,
            city=payload.city,
            neighborhood=payload.neighborhood,
            capacity=payload.capacity,
            price_per_head_usd=payload.price_per_head_usd,
            venue_type=payload.venue_type,
            amenities=payload.amenities,
            tags=payload.tags,
            description=payload.description,
            outside_catering=payload.outside_catering,
            alcohol_allowed=payload.alcohol_allowed,
            min_notice_days=payload.min_notice_days,
        )
        self.venue_repository.create(venue)

        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateResourceError("Venue external_id already exists") from exc

        self.session.refresh(venue)
        return venue

    def list_venues(self, filters: VenueFilters) -> list[Venue]:
        return self.venue_repository.list(
            city=filters.city,
            neighborhood=filters.neighborhood,
            min_capacity=filters.min_capacity,
            outside_catering=filters.outside_catering,
            venue_type=filters.venue_type,
        )
