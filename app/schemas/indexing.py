from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunIndexingRequest(BaseModel):
    document_ids: list[UUID] = Field(default_factory=list)


class RunIndexingResponse(BaseModel):
    indexed_documents: int
    created_chunks: int
    failed_documents: int


class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    venue_id: UUID | None
    chunk_index: int
    content: str
    document_title: str
    document_type: str

    model_config = ConfigDict(from_attributes=True)


class ChunkListResponse(BaseModel):
    items: list[ChunkResponse]
    count: int
