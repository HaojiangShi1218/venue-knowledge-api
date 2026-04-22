from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.chunk import DocumentChunk
from app.models.query_log import QueryLog
from app.models.query_source import QuerySource


class QueryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_query_log(
        self,
        *,
        question: str,
        normalized_question: str,
        answer: str,
        confidence_score: float,
    ) -> QueryLog:
        query_log = QueryLog(
            question=question,
            normalized_question=normalized_question,
            answer=answer,
            confidence_score=confidence_score,
        )
        self.session.add(query_log)
        self.session.flush()
        return query_log

    def create_query_sources(self, query_sources: list[QuerySource]) -> list[QuerySource]:
        self.session.add_all(query_sources)
        self.session.flush()
        return query_sources

    def get_query_log(self, query_id: UUID) -> QueryLog | None:
        stmt = (
            select(QueryLog)
            .where(QueryLog.id == query_id)
            .options(
                joinedload(QueryLog.query_sources)
                .joinedload(QuerySource.chunk)
                .joinedload(DocumentChunk.document),
                joinedload(QueryLog.query_sources)
                .joinedload(QuerySource.chunk)
                .joinedload(DocumentChunk.venue),
            )
        )
        result = self.session.execute(stmt).unique().scalar_one_or_none()
        return result
