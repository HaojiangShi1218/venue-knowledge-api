from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class DocumentTypeEnum(str, Enum):
    FAQ = "faq"
    POLICY = "policy"
    NOTES = "notes"
    BOOKING_DETAILS = "booking_details"
    OTHER = "other"


class IngestionStatusEnum(str, Enum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    external_doc_id: str | None = None
    venue_id: UUID | None = None
    title: str
    document_type: DocumentTypeEnum
    content: str

    @field_validator("title", "content")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class DocumentRead(BaseModel):
    id: UUID
    external_doc_id: str | None
    venue_id: UUID | None
    title: str
    document_type: DocumentTypeEnum
    content: str
    ingestion_status: IngestionStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    count: int
