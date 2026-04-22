from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.config import get_settings
from app.models.chunk import DocumentChunk
from app.models.venue import Venue
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.venue_repository import VenueRepository
from app.utils.query_parsing import ParsedQuery, parse_query
from app.utils.scoring import ScoredChunk, compute_confidence, score_chunk
from app.utils.text_normalization import normalize_text


@dataclass(slots=True)
class RetrievalResult:
    parsed_query: ParsedQuery
    scored_chunks: list[ScoredChunk]
    confidence_score: float


class RetrievalService:
    def __init__(
        self,
        *,
        venue_repository: VenueRepository,
        chunk_repository: ChunkRepository,
    ) -> None:
        self.venue_repository = venue_repository
        self.chunk_repository = chunk_repository
        self.settings = get_settings()

    def retrieve(self, question: str) -> RetrievalResult:
        parsed_query = parse_query(question)
        candidate_venue_ids = self._candidate_venue_ids(parsed_query)
        chunks = self.chunk_repository.list_for_retrieval(candidate_venue_ids)

        if not chunks and candidate_venue_ids:
            chunks = self.chunk_repository.list_for_retrieval()

        scored_chunks = [
            score_chunk(parsed_query, chunk, chunk.venue)
            for chunk in chunks
        ]
        scored_chunks = [chunk for chunk in scored_chunks if chunk.relevance_score > 0]
        scored_chunks.sort(
            key=lambda item: (
                -item.relevance_score,
                -item.matched_major_constraints,
                -item.topic_alignment_score,
                -item.matched_constraints,
                -item.matched_phrases,
                item.chunk.chunk_index,
                str(item.chunk.id),
            )
        )
        scored_chunks = scored_chunks[: self.settings.RETRIEVAL_TOP_K]

        confidence_score = compute_confidence(scored_chunks)
        return RetrievalResult(
            parsed_query=parsed_query,
            scored_chunks=scored_chunks,
            confidence_score=confidence_score,
        )

    def _candidate_venue_ids(self, parsed_query: ParsedQuery) -> list[UUID] | None:
        if not parsed_query.has_structured_constraints():
            return None

        matching_venues = [
            venue
            for venue in self.venue_repository.list_all()
            if _venue_matches_structured_constraints(venue, parsed_query)
        ]
        if not matching_venues:
            return None
        return [venue.id for venue in matching_venues]


def _venue_matches_structured_constraints(venue: Venue, parsed_query: ParsedQuery) -> bool:
    if parsed_query.city and normalize_text(venue.city) != parsed_query.city:
        return False

    if parsed_query.neighborhood:
        venue_neighborhood = normalize_text(venue.neighborhood or "")
        if venue_neighborhood != parsed_query.neighborhood:
            return False

    if parsed_query.min_capacity is not None:
        if venue.capacity is None or venue.capacity < parsed_query.min_capacity:
            return False

    if parsed_query.venue_type:
        venue_type = normalize_text(venue.venue_type or "")
        if venue_type != parsed_query.venue_type:
            return False

    if parsed_query.outside_catering_required is not None and venue.outside_catering is not parsed_query.outside_catering_required:
        return False

    if parsed_query.alcohol_allowed_required is not None and venue.alcohol_allowed is not parsed_query.alcohol_allowed_required:
        return False

    if any(amenity not in (venue.amenities or []) for amenity in parsed_query.amenities):
        return False

    if any(event_type not in (venue.tags or []) for event_type in parsed_query.event_types):
        return False

    return True
