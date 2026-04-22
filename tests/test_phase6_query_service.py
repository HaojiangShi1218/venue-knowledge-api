from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.chunk import DocumentChunk
from app.models.document import SourceDocument
from app.models.query_log import QueryLog
from app.models.query_source import QuerySource
from app.models.venue import Venue
from app.schemas.query import QueryRequest
from app.services.query_service import QueryService
from app.services.retrieval_service import RetrievalService
from app.utils.text_normalization import normalize_text


HARBOR_VENUE_ID = UUID("10101010-1010-1010-1010-101010101010")
SKYLINE_VENUE_ID = UUID("20202020-2020-2020-2020-202020202020")
CAMBRIDGE_VENUE_ID = UUID("30303030-3030-3030-3030-303030303030")
HARBOR_DOC_ID = UUID("40404040-4040-4040-4040-404040404040")
SKYLINE_DOC_ID = UUID("50505050-5050-5050-5050-505050505050")
CAMBRIDGE_DOC_ID = UUID("60606060-6060-6060-6060-606060606060")


class FakeVenueRepository:
    def __init__(self, venues: list[Venue]) -> None:
        self.venues = venues

    def list_all(self) -> list[Venue]:
        return self.venues


class FakeChunkRepository:
    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.chunks = chunks

    def list_for_retrieval(self, venue_ids: list[UUID] | None = None) -> list[DocumentChunk]:
        if venue_ids:
            return [chunk for chunk in self.chunks if chunk.venue_id in venue_ids]
        return list(self.chunks)


class FakeQueryRepository:
    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.query_logs: dict[UUID, QueryLog] = {}
        self.chunk_map = {chunk.id: chunk for chunk in chunks}

    def create_query_log(self, *, question: str, normalized_question: str, answer: str, confidence_score: float) -> QueryLog:
        query_log = QueryLog(
            id=uuid4(),
            question=question,
            normalized_question=normalized_question,
            answer=answer,
            confidence_score=confidence_score,
            created_at=datetime.now(timezone.utc),
        )
        query_log.query_sources = []
        self.query_logs[query_log.id] = query_log
        return query_log

    def create_query_sources(self, query_sources: list[QuerySource]) -> list[QuerySource]:
        for query_source in query_sources:
            query_source.id = uuid4()
            query_source.chunk = self.chunk_map[query_source.chunk_id]
            self.query_logs[query_source.query_log_id].query_sources.append(query_source)
        return query_sources

    def get_query_log(self, query_id: UUID) -> QueryLog | None:
        return self.query_logs.get(query_id)


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def make_query_service() -> tuple[QueryService, FakeQueryRepository, FakeSession]:
    harbor_venue = Venue(
        id=HARBOR_VENUE_ID,
        name="Harbor Loft",
        city="Boston",
        neighborhood="Fort Point",
        capacity=80,
        venue_type="loft",
        amenities=["projector", "wifi", "stage"],
        tags=["team_dinner", "product_launch", "private_event"],
        description="Flexible loft space with exposed brick and stage lighting.",
        outside_catering=True,
        alcohol_allowed=True,
        min_notice_days=5,
    )
    skyline_venue = Venue(
        id=SKYLINE_VENUE_ID,
        name="Skyline Foundry",
        city="Boston",
        neighborhood="Seaport",
        capacity=120,
        venue_type="rooftop",
        amenities=["av", "bar", "wifi", "private_room"],
        tags=["startup", "networking", "demo_day", "industrial"],
        description="Industrial-style rooftop venue.",
        outside_catering=False,
        alcohol_allowed=True,
        min_notice_days=7,
    )
    cambridge_venue = Venue(
        id=CAMBRIDGE_VENUE_ID,
        name="Cambridge Private Table",
        city="Cambridge",
        neighborhood="Kendall Square",
        capacity=40,
        venue_type="private_dining",
        amenities=["private_room", "wifi"],
        tags=["team_dinner", "executive", "quiet"],
        description="Private dining venue for executive dinners.",
        outside_catering=False,
        alcohol_allowed=True,
        min_notice_days=3,
    )

    harbor_document = SourceDocument(
        id=HARBOR_DOC_ID,
        venue_id=HARBOR_VENUE_ID,
        title="Harbor Loft Policies",
        document_type="policy",
        content=(
            "Harbor Loft allows outside catering with prior approval. "
            "The venue supports launch events and internal company all-hands. "
            "Cancellation with full refund is available up to 14 days before the event."
        ),
        ingestion_status="indexed",
    )
    skyline_document = SourceDocument(
        id=SKYLINE_DOC_ID,
        venue_id=SKYLINE_VENUE_ID,
        title="Skyline Foundry FAQ",
        document_type="faq",
        content=(
            "Skyline Foundry supports startup mixers, networking events, and demo days. "
            "Outside catering is not allowed. Built-in AV support includes wireless microphones."
        ),
        ingestion_status="indexed",
    )
    cambridge_document = SourceDocument(
        id=CAMBRIDGE_DOC_ID,
        venue_id=CAMBRIDGE_VENUE_ID,
        title="Cambridge Private Table Notes",
        document_type="notes",
        content=(
            "Cambridge Private Table is best for small executive dinners and team gatherings. "
            "The space does not support large-scale AV setups, but it does provide stable Wi-Fi and a private dining room."
        ),
        ingestion_status="indexed",
    )

    harbor_chunk = DocumentChunk(
        id=uuid4(),
        document_id=HARBOR_DOC_ID,
        venue_id=HARBOR_VENUE_ID,
        chunk_index=0,
        content=harbor_document.content,
        normalized_content=normalize_text(harbor_document.content),
        document_title=harbor_document.title,
        document_type=harbor_document.document_type,
    )
    harbor_chunk.document = harbor_document
    harbor_chunk.venue = harbor_venue

    skyline_chunk = DocumentChunk(
        id=uuid4(),
        document_id=SKYLINE_DOC_ID,
        venue_id=SKYLINE_VENUE_ID,
        chunk_index=0,
        content=skyline_document.content,
        normalized_content=normalize_text(skyline_document.content),
        document_title=skyline_document.title,
        document_type=skyline_document.document_type,
    )
    skyline_chunk.document = skyline_document
    skyline_chunk.venue = skyline_venue

    cambridge_chunk = DocumentChunk(
        id=uuid4(),
        document_id=CAMBRIDGE_DOC_ID,
        venue_id=CAMBRIDGE_VENUE_ID,
        chunk_index=0,
        content=cambridge_document.content,
        normalized_content=normalize_text(cambridge_document.content),
        document_title=cambridge_document.title,
        document_type=cambridge_document.document_type,
    )
    cambridge_chunk.document = cambridge_document
    cambridge_chunk.venue = cambridge_venue

    chunks = [harbor_chunk, skyline_chunk, cambridge_chunk]
    retrieval_service = RetrievalService(
        venue_repository=FakeVenueRepository([harbor_venue, skyline_venue, cambridge_venue]),
        chunk_repository=FakeChunkRepository(chunks),
    )
    query_repository = FakeQueryRepository(chunks)
    session = FakeSession()
    query_service = QueryService(
        session=session,
        retrieval_service=retrieval_service,
        query_repository=query_repository,
    )
    return query_service, query_repository, session


def test_strong_match_query_returns_expected_venue_and_persists_query() -> None:
    query_service, query_repository, session = make_query_service()

    response = query_service.create_query(QueryRequest(question="Which venues allow outside catering?"))

    assert response.answer == "Harbor Loft allows outside catering with prior approval."
    assert response.confidence_score >= 0.75
    assert response.sources[0].venue_name == "Harbor Loft"
    assert "outside catering" in response.sources[0].excerpt.lower()
    assert len(query_repository.query_logs) == 1
    saved_query = query_service.get_query(response.query_id)
    assert saved_query.question == "Which venues allow outside catering?"
    assert saved_query.sources[0].document_title == "Harbor Loft Policies"
    assert session.commits == 1


def test_partial_support_query_returns_cautious_answer_and_lower_confidence() -> None:
    query_service, _query_repository, _session = make_query_service()

    response = query_service.create_query(
        QueryRequest(question="Which Cambridge venues allow outside catering and have a rooftop?")
    )

    assert response.confidence_score < 0.75
    assert response.answer.startswith("I could not find a venue that clearly satisfies all requested constraints.")
    assert response.sources


def test_multi_constraint_query_returns_cautious_partial_match_instead_of_irrelevant_excerpt() -> None:
    query_service, _query_repository, _session = make_query_service()

    response = query_service.create_query(
        QueryRequest(question="Which venues are best for a 150-person launch event with built-in AV?")
    )

    assert response.confidence_score < 0.75
    assert response.answer.startswith("I could not find a venue that clearly satisfies all requested constraints.")
    assert response.answer != "Harbor Loft allows outside catering with prior approval."
    assert response.sources[0].venue_name in {"Skyline Foundry", "Harbor Loft"}
    assert "outside catering" not in response.sources[0].excerpt.lower()
    assert any(
        term in response.sources[0].excerpt.lower()
        for term in ["launch", "av", "wireless microphones", "presentation monitor"]
    )


def test_capacity_requirement_reduces_confidence_for_same_launch_and_av_query() -> None:
    query_service, _query_repository, _session = make_query_service()

    without_capacity = query_service.create_query(
        QueryRequest(question="Which venues are best for a launch event with built-in AV?")
    )
    with_capacity = query_service.create_query(
        QueryRequest(question="Which venues are best for a 150-person launch event with built-in AV?")
    )

    assert with_capacity.confidence_score <= without_capacity.confidence_score


def test_partial_match_sources_align_with_cautious_answer_topic() -> None:
    query_service, _query_repository, _session = make_query_service()

    response = query_service.create_query(
        QueryRequest(question="Which venues are best for a 150-person launch event with built-in AV?")
    )

    assert response.answer.startswith("I could not find a venue that clearly satisfies all requested constraints.")
    assert all("outside catering" not in source.excerpt.lower() for source in response.sources[:2])


def test_query_sources_are_persisted_in_rank_order() -> None:
    query_service, query_repository, _session = make_query_service()

    response = query_service.create_query(QueryRequest(question="Which venues support launch events?"))
    query_log = query_repository.get_query_log(response.query_id)

    assert query_log is not None
    assert query_log.query_sources
    assert [source.rank for source in query_log.query_sources] == sorted(source.rank for source in query_log.query_sources)


def test_get_query_returns_saved_result() -> None:
    query_service, _query_repository, _session = make_query_service()

    created_query = query_service.create_query(QueryRequest(question="Which venues allow outside catering?"))
    fetched_query = query_service.get_query(created_query.query_id)

    assert fetched_query.query_id == created_query.query_id
    assert fetched_query.answer == created_query.answer
    assert fetched_query.sources[0].chunk_id == created_query.sources[0].chunk_id
