from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_document_id_chunk_index", "document_id", "chunk_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    venue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("venues.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_content: Mapped[str] = mapped_column(Text, nullable=False)
    document_title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped["SourceDocument"] = relationship(back_populates="chunks")
    venue: Mapped["Venue | None"] = relationship(back_populates="chunks")
    query_sources: Mapped[list["QuerySource"]] = relationship(back_populates="chunk")
