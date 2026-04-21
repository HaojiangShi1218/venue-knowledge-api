from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QuerySource(Base):
    __tablename__ = "query_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_logs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    query_log: Mapped["QueryLog"] = relationship(back_populates="query_sources")
    chunk: Mapped["DocumentChunk"] = relationship(back_populates="query_sources")
