from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.text_normalization import normalize_text


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        if not normalize_text(value):
            raise ValueError("question must contain meaningful text")
        return value


class QuerySourceResponse(BaseModel):
    document_id: UUID
    chunk_id: UUID
    venue_id: UUID | None
    venue_name: str | None
    document_title: str
    document_type: str
    excerpt: str
    rank: int
    relevance_score: float


class QueryResponse(BaseModel):
    query_id: UUID
    answer: str
    confidence_score: float
    sources: list[QuerySourceResponse]


class QueryLogResponse(BaseModel):
    query_id: UUID
    question: str
    answer: str
    confidence_score: float
    created_at: datetime
    sources: list[QuerySourceResponse]
