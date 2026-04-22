from __future__ import annotations

from dataclasses import dataclass, field
import re

from app.utils.text_normalization import normalize_text

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "best",
    "built",
    "can",
    "do",
    "does",
    "for",
    "guest",
    "guests",
    "have",
    "i",
    "in",
    "is",
    "looking",
    "me",
    "need",
    "of",
    "on",
    "show",
    "support",
    "supports",
    "tell",
    "that",
    "the",
    "these",
    "person",
    "people",
    "venues",
    "venue",
    "what",
    "which",
    "with",
}

KNOWN_CITIES = {"boston", "cambridge"}
KNOWN_NEIGHBORHOODS = {"seaport", "fort point", "kendall square"}
KNOWN_VENUE_TYPES = {
    "rooftop": ["rooftop"],
    "loft": ["loft"],
    "private_dining": ["private dining", "private dining room", "private table"],
}
AMENITY_ALIASES = {
    "av": [
        "av",
        "a v",
        "audio visual",
        "built in av",
        "built in a v",
        "built in audio visual",
        "wireless microphones",
        "presentation monitor",
        "projector output",
    ],
    "projector": ["projector", "projector output"],
    "stage": ["stage", "stage lighting"],
    "private_room": ["private room", "private dining room"],
    "wifi": ["wifi", "wi fi", "wireless internet"],
}
POLICY_ALIASES = {
    "outside_catering": ["outside catering"],
    "alcohol": ["alcohol", "bar"],
    "cancellation": ["cancellation", "cancel", "refund"],
}
EVENT_TYPE_ALIASES = {
    "product_launch": ["launch event", "launch events", "product launch", "product launches"],
    "networking": ["networking", "startup mixer", "startup mixers"],
    "executive": ["executive dinner", "founder meetings", "client hospitality"],
    "team_dinner": ["team dinner", "team dinners"],
    "demo_day": ["demo day", "demo days"],
}
ALLOW_TERMS = {"allow", "allows", "allowed", "permit", "permits", "permitted"}
ALCOHOL_TERMS = {"alcohol", "bar"}
CAPACITY_RE = re.compile(r"(\d+)\s*(?:people|person|guests|guest|attendees|attendee)")


@dataclass(slots=True)
class ParsedQuery:
    question: str
    normalized_question: str
    keywords: list[str]
    phrases: list[str]
    city: str | None = None
    neighborhood: str | None = None
    min_capacity: int | None = None
    venue_type: str | None = None
    amenities: list[str] = field(default_factory=list)
    policy_terms: list[str] = field(default_factory=list)
    event_types: list[str] = field(default_factory=list)
    outside_catering_required: bool | None = None
    alcohol_allowed_required: bool | None = None

    def has_structured_constraints(self) -> bool:
        return bool(
            self.city
            or self.neighborhood
            or self.min_capacity is not None
            or self.venue_type
            or self.amenities
            or self.event_types
            or self.outside_catering_required is not None
            or self.alcohol_allowed_required is not None
        )

    def constraint_labels(self) -> list[str]:
        labels: list[str] = []
        if self.city:
            labels.append(f"city:{self.city}")
        if self.neighborhood:
            labels.append(f"neighborhood:{self.neighborhood}")
        if self.min_capacity is not None:
            labels.append(f"capacity:{self.min_capacity}")
        if self.venue_type:
            labels.append(f"venue_type:{self.venue_type}")
        labels.extend(f"amenity:{amenity}" for amenity in self.amenities)
        labels.extend(f"policy:{policy}" for policy in self.policy_terms)
        labels.extend(f"event:{event_type}" for event_type in self.event_types)
        if self.outside_catering_required is not None:
            labels.append(f"outside_catering:{self.outside_catering_required}")
        if self.alcohol_allowed_required is not None:
            labels.append(f"alcohol_allowed:{self.alcohol_allowed_required}")
        return labels

    def major_constraint_labels(self) -> list[str]:
        labels: list[str] = []
        if self.min_capacity is not None:
            labels.append(f"capacity:{self.min_capacity}")
        labels.extend(f"amenity:{amenity}" for amenity in self.amenities)
        labels.extend(f"event:{event_type}" for event_type in self.event_types)
        return labels


def parse_query(question: str) -> ParsedQuery:
    normalized_question = normalize_text(question)
    keywords = [
        token
        for token in normalized_question.split()
        if token not in STOPWORDS and not token.isdigit() and len(token) > 1
    ]

    city = next((candidate for candidate in KNOWN_CITIES if _contains_phrase(normalized_question, candidate)), None)
    neighborhood = next(
        (candidate for candidate in KNOWN_NEIGHBORHOODS if _contains_phrase(normalized_question, candidate)),
        None,
    )

    capacity_match = CAPACITY_RE.search(normalized_question)
    min_capacity = int(capacity_match.group(1)) if capacity_match else None

    venue_type = None
    for candidate, aliases in KNOWN_VENUE_TYPES.items():
        if any(_contains_phrase(normalized_question, alias) for alias in aliases):
            venue_type = candidate
            break

    amenities = _extract_canonical_terms(normalized_question, AMENITY_ALIASES)
    policy_terms = _extract_canonical_terms(normalized_question, POLICY_ALIASES)
    event_types = _extract_canonical_terms(normalized_question, EVENT_TYPE_ALIASES)

    outside_catering_required = None
    if "outside_catering" in policy_terms:
        outside_catering_required = True

    alcohol_allowed_required = None
    if any(term in normalized_question.split() for term in ALCOHOL_TERMS):
        alcohol_allowed_required = True

    phrases = _build_phrases(
        city=city,
        neighborhood=neighborhood,
        venue_type=venue_type,
        amenities=amenities,
        policy_terms=policy_terms,
        event_types=event_types,
    )

    return ParsedQuery(
        question=question,
        normalized_question=normalized_question,
        keywords=keywords,
        phrases=phrases,
        city=city,
        neighborhood=neighborhood,
        min_capacity=min_capacity,
        venue_type=venue_type,
        amenities=amenities,
        policy_terms=policy_terms,
        event_types=event_types,
        outside_catering_required=outside_catering_required,
        alcohol_allowed_required=alcohol_allowed_required,
    )


def phrases_for_amenity(amenity: str) -> list[str]:
    return AMENITY_ALIASES.get(amenity, [amenity.replace("_", " ")])


def phrases_for_policy(policy: str) -> list[str]:
    return POLICY_ALIASES.get(policy, [policy.replace("_", " ")])


def phrases_for_event_type(event_type: str) -> list[str]:
    return EVENT_TYPE_ALIASES.get(event_type, [event_type.replace("_", " ")])


def phrase_for_venue_type(venue_type: str) -> str:
    return KNOWN_VENUE_TYPES.get(venue_type, [venue_type.replace("_", " ")])[0]


def _extract_canonical_terms(normalized_question: str, aliases: dict[str, list[str]]) -> list[str]:
    matches: list[str] = []
    for canonical, phrases in aliases.items():
        if any(_contains_phrase(normalized_question, phrase) for phrase in phrases):
            matches.append(canonical)
    return matches


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _build_phrases(
    *,
    city: str | None,
    neighborhood: str | None,
    venue_type: str | None,
    amenities: list[str],
    policy_terms: list[str],
    event_types: list[str],
) -> list[str]:
    phrases: list[str] = []
    if city:
        phrases.append(city)
    if neighborhood:
        phrases.append(neighborhood)
    if venue_type:
        phrases.extend(KNOWN_VENUE_TYPES.get(venue_type, [venue_type.replace("_", " ")]))
    for amenity in amenities:
        phrases.extend(phrases_for_amenity(amenity))
    for policy in policy_terms:
        phrases.extend(phrases_for_policy(policy))
    for event_type in event_types:
        phrases.extend(phrases_for_event_type(event_type))
    return list(dict.fromkeys(phrases))
