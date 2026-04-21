from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Venue(TimestampMixin, Base):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    price_per_head_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue_type: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amenities: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    outside_catering: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    alcohol_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    min_notice_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    documents: Mapped[list["SourceDocument"]] = relationship(back_populates="venue")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="venue")
