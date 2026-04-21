from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    query_id: UUID | None = None
    status: str = "not_implemented"
    answer: str | None = None
