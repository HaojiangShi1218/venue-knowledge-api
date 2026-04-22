from __future__ import annotations

from app.schemas.query import QuerySourceResponse
from app.utils.scoring import ScoredChunk


def build_answer(
    *,
    sources: list[QuerySourceResponse],
    scored_chunks: list[ScoredChunk],
    confidence_score: float,
) -> str:
    if not sources:
        return "I could not find enough evidence to answer confidently."

    top_source = sources[0]
    top_chunk = scored_chunks[0]
    has_full_major_coverage = (
        top_chunk.total_major_constraints == 0
        or top_chunk.matched_major_constraints >= top_chunk.total_major_constraints
    )

    if confidence_score >= 0.75 and has_full_major_coverage:
        return top_source.excerpt

    unique_venues = []
    for source in sources:
        if source.venue_name and source.venue_name not in unique_venues:
            unique_venues.append(source.venue_name)
    venue_summary = ", ".join(unique_venues[:3])

    if confidence_score >= 0.45:
        return (
            "I could not find a venue that clearly satisfies all requested constraints. "
            f"The following venues appear partially relevant based on the available data: {venue_summary}."
        )

    venue_name = top_source.venue_name or "One venue"
    return (
        "I could not find enough evidence to answer confidently. "
        f"{venue_name} may be relevant based on the available venue documents."
    )
