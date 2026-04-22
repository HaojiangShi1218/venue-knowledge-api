from __future__ import annotations

from dataclasses import dataclass, field
import re

from app.models.chunk import DocumentChunk
from app.models.venue import Venue
from app.utils.query_parsing import (
    ParsedQuery,
    phrase_for_venue_type,
    phrases_for_amenity,
    phrases_for_event_type,
    phrases_for_policy,
)
from app.utils.text_normalization import normalize_text


@dataclass(slots=True)
class ScoredChunk:
    chunk: DocumentChunk
    venue: Venue | None
    relevance_score: float
    matched_keywords: int
    matched_phrases: int
    matched_structured: int
    matched_constraints: int
    total_constraints: int
    matched_major_constraints: int
    total_major_constraints: int
    agreement_matches: int
    capacity_penalty: float
    feature_penalty: float
    event_penalty: float
    topic_alignment_score: float
    matched_labels: set[str] = field(default_factory=set)


def score_chunk(parsed_query: ParsedQuery, chunk: DocumentChunk, venue: Venue | None) -> ScoredChunk:
    document_text = chunk.normalized_content
    matched_keywords = sum(1 for keyword in parsed_query.keywords if keyword in document_text.split())
    matched_phrases = sum(1 for phrase in parsed_query.phrases if phrase and phrase in document_text)

    structured_matches = 0
    matched_labels: set[str] = set()

    if venue is not None:
        if parsed_query.city and normalize_text(venue.city) == parsed_query.city:
            structured_matches += 1
            matched_labels.add(f"city:{parsed_query.city}")
        if parsed_query.neighborhood and venue.neighborhood and normalize_text(venue.neighborhood) == parsed_query.neighborhood:
            structured_matches += 1
            matched_labels.add(f"neighborhood:{parsed_query.neighborhood}")
        if parsed_query.min_capacity is not None and venue.capacity is not None and venue.capacity >= parsed_query.min_capacity:
            structured_matches += 1
            matched_labels.add(f"capacity:{parsed_query.min_capacity}")
        if parsed_query.venue_type and venue.venue_type and normalize_text(venue.venue_type) == parsed_query.venue_type:
            structured_matches += 1
            matched_labels.add(f"venue_type:{parsed_query.venue_type}")

        for amenity in parsed_query.amenities:
            if amenity in (venue.amenities or []):
                structured_matches += 1
                matched_labels.add(f"amenity:{amenity}")

        for event_type in parsed_query.event_types:
            if event_type in (venue.tags or []):
                structured_matches += 1
                matched_labels.add(f"event:{event_type}")

        if parsed_query.outside_catering_required is not None and venue.outside_catering is parsed_query.outside_catering_required:
            structured_matches += 1
            matched_labels.add(f"outside_catering:{parsed_query.outside_catering_required}")
            matched_labels.add("policy:outside_catering")

        if parsed_query.alcohol_allowed_required is not None and venue.alcohol_allowed is parsed_query.alcohol_allowed_required:
            structured_matches += 1
            matched_labels.add(f"alcohol_allowed:{parsed_query.alcohol_allowed_required}")
            matched_labels.add("policy:alcohol")

    agreement_matches = _count_agreement_matches(parsed_query, document_text, venue)
    matched_labels |= _document_constraint_matches(parsed_query, document_text)

    total_constraints = len(parsed_query.constraint_labels())
    matched_constraints = len(matched_labels)
    total_major_constraints = len(parsed_query.major_constraint_labels())
    matched_major_constraints = len(
        {
            label
            for label in matched_labels
            if label in set(parsed_query.major_constraint_labels())
        }
    )

    capacity_penalty = _capacity_penalty(parsed_query, venue)
    feature_penalty = _feature_penalty(parsed_query, venue, document_text)
    event_penalty = _event_penalty(parsed_query, venue, document_text)
    excerpt, topic_alignment_score = select_best_excerpt(parsed_query, chunk.content, return_score=True)
    topic_penalty = _topic_penalty(parsed_query, topic_alignment_score)
    total_penalty = capacity_penalty + feature_penalty + event_penalty + topic_penalty

    keyword_score = min(matched_keywords, 5) * 0.1
    phrase_score = min(matched_phrases, 4) * 0.15
    structured_score = min(structured_matches, 4) * 0.12
    constraint_score = (matched_constraints / total_constraints) * 0.2 if total_constraints else 0.0
    agreement_score = min(agreement_matches, 2) * 0.08

    relevance_score = max(
        0.0,
        min(
            1.0,
            keyword_score + phrase_score + structured_score + constraint_score + agreement_score - total_penalty,
        ),
    )

    return ScoredChunk(
        chunk=chunk,
        venue=venue,
        relevance_score=round(relevance_score, 2),
        matched_keywords=matched_keywords,
        matched_phrases=matched_phrases,
        matched_structured=structured_matches,
        matched_constraints=matched_constraints,
        total_constraints=total_constraints,
        matched_major_constraints=matched_major_constraints,
        total_major_constraints=total_major_constraints,
        agreement_matches=agreement_matches,
        capacity_penalty=capacity_penalty,
        feature_penalty=feature_penalty,
        event_penalty=event_penalty,
        topic_alignment_score=topic_alignment_score,
        matched_labels=matched_labels,
    )


def compute_confidence(scored_chunks: list[ScoredChunk]) -> float:
    if not scored_chunks:
        return 0.0

    top_chunk = scored_chunks[0]
    top_score = top_chunk.relevance_score
    coverage_ratio = 0.0
    if top_chunk.total_constraints:
        coverage_ratio = top_chunk.matched_constraints / top_chunk.total_constraints
    supporting_scores = [chunk.relevance_score for chunk in scored_chunks[:3] if chunk.relevance_score >= 0.35]
    support_bonus = max(0, len(supporting_scores) - 1) * 0.05
    confidence = min(0.99, (top_score * 0.9) + (coverage_ratio * 0.1) + support_bonus)

    if top_chunk.total_major_constraints:
        major_coverage = top_chunk.matched_major_constraints / top_chunk.total_major_constraints
        confidence = min(confidence, 0.3 + (major_coverage * 0.45) + support_bonus)

    if top_chunk.capacity_penalty >= 0.12:
        confidence = min(confidence, 0.62)
    if top_chunk.feature_penalty >= 0.12:
        confidence = min(confidence, 0.68)
    if top_chunk.event_penalty >= 0.12:
        confidence = min(confidence, 0.68)

    return round(confidence, 2)


def _document_constraint_matches(parsed_query: ParsedQuery, document_text: str) -> set[str]:
    matched_labels: set[str] = set()

    if parsed_query.city and parsed_query.city in document_text:
        matched_labels.add(f"city:{parsed_query.city}")
    if parsed_query.neighborhood and parsed_query.neighborhood in document_text:
        matched_labels.add(f"neighborhood:{parsed_query.neighborhood}")
    if parsed_query.venue_type and phrase_for_venue_type(parsed_query.venue_type) in document_text:
        matched_labels.add(f"venue_type:{parsed_query.venue_type}")

    for amenity in parsed_query.amenities:
        if any(phrase in document_text for phrase in phrases_for_amenity(amenity)):
            matched_labels.add(f"amenity:{amenity}")

    for policy in parsed_query.policy_terms:
        if _document_supports_policy(policy, parsed_query, document_text):
            matched_labels.add(f"policy:{policy}")

    for event_type in parsed_query.event_types:
        if any(phrase in document_text for phrase in phrases_for_event_type(event_type)):
            matched_labels.add(f"event:{event_type}")

    return matched_labels


def _capacity_penalty(parsed_query: ParsedQuery, venue: Venue | None) -> float:
    if parsed_query.min_capacity is None or venue is None or venue.capacity is None:
        return 0.0
    if venue.capacity >= parsed_query.min_capacity:
        return 0.0

    shortfall_ratio = (parsed_query.min_capacity - venue.capacity) / parsed_query.min_capacity
    if shortfall_ratio <= 0.2:
        return 0.18
    if shortfall_ratio <= 0.4:
        return 0.3
    return 0.45


def _feature_penalty(parsed_query: ParsedQuery, venue: Venue | None, document_text: str) -> float:
    if not parsed_query.amenities:
        return 0.0

    missing_features = 0
    for amenity in parsed_query.amenities:
        venue_match = venue is not None and amenity in (venue.amenities or [])
        document_match = any(phrase in document_text for phrase in phrases_for_amenity(amenity))
        if not venue_match and not document_match:
            missing_features += 1

    return min(0.3, missing_features * 0.12)


def _event_penalty(parsed_query: ParsedQuery, venue: Venue | None, document_text: str) -> float:
    if not parsed_query.event_types:
        return 0.0

    missing_events = 0
    for event_type in parsed_query.event_types:
        venue_match = venue is not None and event_type in (venue.tags or [])
        document_match = any(phrase in document_text for phrase in phrases_for_event_type(event_type))
        if not venue_match and not document_match:
            missing_events += 1

    return min(0.3, missing_events * 0.15)


def _document_supports_policy(policy: str, parsed_query: ParsedQuery, document_text: str) -> bool:
    if policy == "outside_catering":
        if "outside catering is not allowed" in document_text or "outside catering not allowed" in document_text:
            return False
        return "outside catering" in document_text

    if policy == "alcohol":
        if "alcohol is not allowed" in document_text or "no alcohol" in document_text:
            return False
        return any(phrase in document_text for phrase in phrases_for_policy(policy))

    return any(phrase in document_text for phrase in phrases_for_policy(policy))


def select_best_excerpt(
    parsed_query: ParsedQuery,
    content: str,
    *,
    max_length: int = 240,
    return_score: bool = False,
):
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", content.strip()) if segment.strip()]
    if not sentences:
        excerpt = _truncate_excerpt(content, max_length)
        return (excerpt, 0.0) if return_score else excerpt

    scored_sentences = [
        (sentence, _score_sentence_alignment(parsed_query, sentence))
        for sentence in sentences
    ]
    scored_sentences.sort(key=lambda item: (-item[1], sentences.index(item[0])))

    best_sentence, best_score = scored_sentences[0]
    excerpt = _truncate_excerpt(best_sentence, max_length)
    if return_score:
        return excerpt, round(best_score, 2)
    return excerpt


def _score_sentence_alignment(parsed_query: ParsedQuery, sentence: str) -> float:
    normalized_sentence = normalize_text(sentence)
    sentence_tokens = set(normalized_sentence.split())

    keyword_matches = sum(1 for keyword in parsed_query.keywords if keyword in sentence_tokens)
    phrase_matches = sum(1 for phrase in parsed_query.phrases if phrase and phrase in normalized_sentence)

    major_matches = 0
    for amenity in parsed_query.amenities:
        if any(phrase in normalized_sentence for phrase in phrases_for_amenity(amenity)):
            major_matches += 1
    for event_type in parsed_query.event_types:
        if any(phrase in normalized_sentence for phrase in phrases_for_event_type(event_type)):
            major_matches += 1
    if parsed_query.min_capacity is not None and str(parsed_query.min_capacity) in normalized_sentence:
        major_matches += 1

    policy_only_penalty = 0.0
    if parsed_query.major_constraint_labels() and not major_matches and not parsed_query.policy_terms:
        if any(phrase in normalized_sentence for phrase in phrases_for_policy("outside_catering")):
            policy_only_penalty = 0.12
        if any(phrase in normalized_sentence for phrase in phrases_for_policy("cancellation")):
            policy_only_penalty = max(policy_only_penalty, 0.08)

    return max(0.0, (keyword_matches * 0.05) + (phrase_matches * 0.12) + (major_matches * 0.2) - policy_only_penalty)


def _topic_penalty(parsed_query: ParsedQuery, topic_alignment_score: float) -> float:
    if not parsed_query.major_constraint_labels():
        return 0.0
    if topic_alignment_score >= 0.2:
        return 0.0
    if topic_alignment_score >= 0.1:
        return 0.08
    return 0.16


def _truncate_excerpt(content: str, max_length: int) -> str:
    excerpt = content[:max_length].strip()
    if len(content) > max_length:
        return f"{excerpt}..."
    return excerpt


def _count_agreement_matches(parsed_query: ParsedQuery, document_text: str, venue: Venue | None) -> int:
    if venue is None:
        return 0

    agreement_matches = 0

    if parsed_query.outside_catering_required is not None and venue.outside_catering is parsed_query.outside_catering_required:
        if any(phrase in document_text for phrase in phrases_for_policy("outside_catering")):
            agreement_matches += 1

    if parsed_query.alcohol_allowed_required is not None and venue.alcohol_allowed is parsed_query.alcohol_allowed_required:
        if any(phrase in document_text for phrase in phrases_for_policy("alcohol")):
            agreement_matches += 1

    for amenity in parsed_query.amenities:
        if amenity in (venue.amenities or []) and any(phrase in document_text for phrase in phrases_for_amenity(amenity)):
            agreement_matches += 1

    for event_type in parsed_query.event_types:
        if event_type in (venue.tags or []) and any(phrase in document_text for phrase in phrases_for_event_type(event_type)):
            agreement_matches += 1

    return agreement_matches
