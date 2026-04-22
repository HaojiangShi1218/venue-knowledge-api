from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.query_source import QuerySource
from app.repositories.query_repository import QueryRepository
from app.schemas.query import QueryLogResponse, QueryRequest, QueryResponse, QuerySourceResponse
from app.services.exceptions import ResourceNotFoundError
from app.services.retrieval_service import RetrievalService
from app.utils.answer_building import build_answer
from app.utils.query_parsing import parse_query
from app.utils.scoring import select_best_excerpt


class QueryService:
    def __init__(
        self,
        *,
        session: Session,
        retrieval_service: RetrievalService,
        query_repository: QueryRepository,
    ) -> None:
        self.session = session
        self.retrieval_service = retrieval_service
        self.query_repository = query_repository

    def create_query(self, payload: QueryRequest) -> QueryResponse:
        retrieval_result = self.retrieval_service.retrieve(payload.question)
        sources = [
            _build_query_source_response(
                scored_chunk,
                parsed_query=retrieval_result.parsed_query,
                rank=index + 1,
            )
            for index, scored_chunk in enumerate(retrieval_result.scored_chunks)
        ]
        answer = build_answer(
            sources=sources,
            scored_chunks=retrieval_result.scored_chunks,
            confidence_score=retrieval_result.confidence_score,
        )

        query_log = self.query_repository.create_query_log(
            question=payload.question,
            normalized_question=retrieval_result.parsed_query.normalized_question,
            answer=answer,
            confidence_score=retrieval_result.confidence_score,
        )
        query_source_rows = [
            QuerySource(
                query_log_id=query_log.id,
                chunk_id=scored_chunk.chunk.id,
                rank=index + 1,
                relevance_score=scored_chunk.relevance_score,
            )
            for index, scored_chunk in enumerate(retrieval_result.scored_chunks)
        ]
        if query_source_rows:
            self.query_repository.create_query_sources(query_source_rows)

        self.session.commit()

        return QueryResponse(
            query_id=query_log.id,
            answer=answer,
            confidence_score=retrieval_result.confidence_score,
            sources=sources,
        )

    def get_query(self, query_id: UUID) -> QueryLogResponse:
        query_log = self.query_repository.get_query_log(query_id)
        if query_log is None:
            raise ResourceNotFoundError("Query not found")
        parsed_query = parse_query(query_log.question)

        sources = [
            QuerySourceResponse(
                document_id=query_source.chunk.document_id,
                chunk_id=query_source.chunk_id,
                venue_id=query_source.chunk.venue_id,
                venue_name=query_source.chunk.venue.name if query_source.chunk.venue else None,
                document_title=query_source.chunk.document_title,
                document_type=query_source.chunk.document_type,
                excerpt=select_best_excerpt(parsed_query, query_source.chunk.content),
                rank=query_source.rank,
                relevance_score=round(query_source.relevance_score, 2),
            )
            for query_source in sorted(query_log.query_sources, key=lambda item: item.rank)
        ]

        return QueryLogResponse(
            query_id=query_log.id,
            question=query_log.question,
            answer=query_log.answer,
            confidence_score=round(query_log.confidence_score, 2),
            created_at=query_log.created_at,
            sources=sources,
        )


def _build_query_source_response(scored_chunk, *, parsed_query, rank: int) -> QuerySourceResponse:
    return QuerySourceResponse(
        document_id=scored_chunk.chunk.document_id,
        chunk_id=scored_chunk.chunk.id,
        venue_id=scored_chunk.chunk.venue_id,
        venue_name=scored_chunk.venue.name if scored_chunk.venue else None,
        document_title=scored_chunk.chunk.document_title,
        document_type=scored_chunk.chunk.document_type,
        excerpt=select_best_excerpt(parsed_query, scored_chunk.chunk.content),
        rank=rank,
        relevance_score=scored_chunk.relevance_score,
    )
