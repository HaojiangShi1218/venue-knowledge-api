from __future__ import annotations

from app.schemas.query import QueryRequest
from tests.test_phase6_query_service import make_query_service


def run_query(question: str):
    query_service, _query_repository, _session = make_query_service()
    return query_service.create_query(QueryRequest(question=question))


def test_query_pack_1_direct_policy_lookup() -> None:
    response = run_query("Which venues allow outside catering?")

    assert response.answer == "Harbor Loft allows outside catering with prior approval."
    assert response.confidence_score >= 0.75
    assert response.sources[0].venue_name == "Harbor Loft"
    assert "outside catering" in response.sources[0].excerpt.lower()


def test_query_pack_2_feature_lookup() -> None:
    response = run_query("Which venues have built-in AV?")

    assert response.confidence_score >= 0.75
    assert response.sources[0].venue_name == "Skyline Foundry"
    assert "built-in av" in response.sources[0].excerpt.lower()


def test_query_pack_3_capacity_constrained_query_moderate_threshold() -> None:
    response = run_query("Which venues can host 100 people?")

    assert response.sources
    assert response.sources[0].venue_name == "Skyline Foundry"
    assert all(source.venue_name != "Cambridge Private Table" for source in response.sources)


def test_query_pack_4_capacity_constrained_query_high_threshold() -> None:
    response = run_query("Which venues can host 130 people?")

    assert response.answer == "I could not find enough evidence to answer confidently."
    assert response.confidence_score <= 0.25
    assert not response.sources


def test_query_pack_5_multi_constraint_weak_fit_query() -> None:
    response = run_query("Which venues are best for a 150-person launch event with built-in AV?")

    assert response.confidence_score < 0.75
    assert response.answer.startswith("I could not find a venue that clearly satisfies all requested constraints.")
    assert response.sources
    assert "outside catering" not in response.sources[0].excerpt.lower()
    assert any(term in response.sources[0].excerpt.lower() for term in ["launch", "av", "wireless microphones"])


def test_query_pack_6_multi_constraint_better_fit_query() -> None:
    better_fit = run_query("Which venues are best for a 110-person launch event with built-in AV?")
    weaker_fit = run_query("Which venues are best for a 150-person launch event with built-in AV?")

    assert better_fit.sources[0].venue_name == "Skyline Foundry"
    assert better_fit.confidence_score >= weaker_fit.confidence_score
    assert any(term in better_fit.sources[0].excerpt.lower() for term in ["av", "wireless microphones"])


def test_query_pack_7_specific_cancellation_detail_query() -> None:
    response = run_query("What are the cancellation rules for Harbor Loft?")

    assert response.sources[0].venue_name == "Harbor Loft"
    assert "14 days" in response.sources[0].excerpt.lower()
    assert "cancellation" in response.sources[0].excerpt.lower()


def test_query_pack_8_policy_search_by_condition() -> None:
    response = run_query("Which venues offer a full refund if cancelled 14 days in advance?")

    assert response.sources[0].venue_name == "Harbor Loft"
    assert "full refund" in response.sources[0].excerpt.lower()
    assert "14 days" in response.sources[0].excerpt.lower()


def test_query_pack_9_low_evidence_negative_query() -> None:
    response = run_query("Which venues have valet parking?")

    assert response.answer == "I could not find enough evidence to answer confidently."
    assert response.confidence_score <= 0.25
    assert not response.sources


def test_query_pack_10_broader_no_match_query() -> None:
    response = run_query("Which venues are best for a wedding reception with outdoor garden seating?")

    assert response.answer == "I could not find enough evidence to answer confidently."
    assert response.confidence_score <= 0.25
    assert not response.sources
