from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.venue import Venue


class VenueRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, venue: Venue) -> Venue:
        self.session.add(venue)
        return venue

    def list(
        self,
        *,
        city: str | None = None,
        neighborhood: str | None = None,
        min_capacity: int | None = None,
        outside_catering: bool | None = None,
        venue_type: str | None = None,
    ) -> list[Venue]:
        stmt: Select[tuple[Venue]] = select(Venue).order_by(Venue.created_at.desc())

        if city is not None:
            stmt = stmt.where(Venue.city == city)
        if neighborhood is not None:
            stmt = stmt.where(Venue.neighborhood == neighborhood)
        if min_capacity is not None:
            stmt = stmt.where(Venue.capacity.is_not(None), Venue.capacity >= min_capacity)
        if outside_catering is not None:
            stmt = stmt.where(Venue.outside_catering == outside_catering)
        if venue_type is not None:
            stmt = stmt.where(Venue.venue_type == venue_type)

        return list(self.session.scalars(stmt).all())

    def get_by_id(self, venue_id: UUID) -> Venue | None:
        stmt = select(Venue).where(Venue.id == venue_id)
        return self.session.scalar(stmt)

    def get_by_external_id(self, external_id: str) -> Venue | None:
        stmt = select(Venue).where(Venue.external_id == external_id)
        return self.session.scalar(stmt)
