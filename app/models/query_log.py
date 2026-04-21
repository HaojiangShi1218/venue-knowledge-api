from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    query_sources: Mapped[list["QuerySource"]] = relationship(back_populates="query_log")
