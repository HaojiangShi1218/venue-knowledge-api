from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SourceDocument(TimestampMixin, Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_doc_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    venue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("venues.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ingestion_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default=text("'pending'"),
        nullable=False,
    )

    venue: Mapped["Venue | None"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")
