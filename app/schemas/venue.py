from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VenueCreate(BaseModel):
    external_id: str | None = None
    name: str
    city: str
    neighborhood: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    price_per_head_usd: int | None = Field(default=None, ge=0)
    venue_type: str | None = None
    amenities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    outside_catering: bool | None = None
    alcohol_allowed: bool | None = None
    min_notice_days: int | None = Field(default=None, ge=0)

    @field_validator("name", "city")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class VenueRead(BaseModel):
    id: UUID
    external_id: str | None
    name: str
    city: str
    neighborhood: str | None
    capacity: int | None
    price_per_head_usd: int | None
    venue_type: str | None
    amenities: list[str]
    tags: list[str]
    description: str | None
    outside_catering: bool | None
    alcohol_allowed: bool | None
    min_notice_days: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VenueListResponse(BaseModel):
    items: list[VenueRead]
    count: int
