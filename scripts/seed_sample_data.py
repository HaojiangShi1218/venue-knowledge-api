from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import SessionLocal
from app.models.document import SourceDocument
from app.models.venue import Venue
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.venue_repository import VenueRepository
from app.schemas.indexing import RunIndexingRequest
from app.services.indexing_service import IndexingService


SAMPLE_DATA_DIR = ROOT_DIR / "sample_data"
VENUES_PATH = SAMPLE_DATA_DIR / "venues.json"
VENUE_DOCS_PATH = SAMPLE_DATA_DIR / "venue_docs.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed sample venues and documents into the database.")
    parser.add_argument(
        "--index",
        action="store_true",
        help="Run the existing indexing service for the sample documents after seeding.",
    )
    args = parser.parse_args()

    venue_records = _load_json_file(VENUES_PATH)
    document_records = _load_json_file(VENUE_DOCS_PATH)

    session = SessionLocal()
    try:
        venue_repository = VenueRepository(session)
        document_repository = DocumentRepository(session)

        venue_summary = _seed_venues(venue_records, venue_repository)
        document_summary = _seed_documents(document_records, venue_repository, document_repository)

        indexing_summary = None
        if args.index:
            indexing_summary = _run_indexing(document_records, document_repository, session)

    except Exception as exc:
        session.rollback()
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    print("Seed complete.")
    print(f"Venues created: {venue_summary['created']}")
    print(f"Venues skipped: {venue_summary['skipped']}")
    print(f"Documents created: {document_summary['created']}")
    print(f"Documents skipped: {document_summary['skipped']}")

    errors = venue_summary["errors"] + document_summary["errors"]
    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")

    if indexing_summary is not None:
        print("Indexing complete.")
        print(f"Indexed documents: {indexing_summary.indexed_documents}")
        print(f"Created chunks: {indexing_summary.created_chunks}")
        print(f"Failed documents: {indexing_summary.failed_documents}")

    return 1 if errors else 0


def _load_json_file(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing sample data file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, list):
        raise RuntimeError(f"Expected a JSON list in {path}")
    return data


def _seed_venues(
    venue_records: list[dict[str, Any]],
    venue_repository: VenueRepository,
) -> dict[str, Any]:
    session = venue_repository.session
    summary = {"created": 0, "skipped": 0, "errors": []}

    for record in venue_records:
        external_id = record.get("id")
        if not external_id:
            summary["errors"].append("Encountered venue record without an 'id'.")
            continue

        if venue_repository.get_by_external_id(external_id) is not None:
            summary["skipped"] += 1
            continue

        policies = record.get("policies") or {}
        venue = Venue(
            external_id=external_id,
            name=record["name"],
            city=record["city"],
            neighborhood=record.get("neighborhood"),
            capacity=record.get("capacity"),
            price_per_head_usd=record.get("price_per_head_usd"),
            venue_type=record.get("venue_type"),
            amenities=record.get("amenities") or [],
            tags=record.get("tags") or [],
            description=record.get("description"),
            outside_catering=policies.get("outside_catering"),
            alcohol_allowed=policies.get("alcohol_allowed"),
            min_notice_days=policies.get("min_notice_days"),
        )
        venue_repository.create(venue)
        summary["created"] += 1

    session.commit()
    return summary


def _seed_documents(
    document_records: list[dict[str, Any]],
    venue_repository: VenueRepository,
    document_repository: DocumentRepository,
) -> dict[str, Any]:
    session = document_repository.session
    summary = {"created": 0, "skipped": 0, "errors": []}

    for record in document_records:
        external_doc_id = record.get("doc_id")
        if not external_doc_id:
            summary["errors"].append("Encountered document record without a 'doc_id'.")
            continue

        if document_repository.get_by_external_id(external_doc_id) is not None:
            summary["skipped"] += 1
            continue

        venue_external_id = record.get("venue_id")
        venue = venue_repository.get_by_external_id(venue_external_id) if venue_external_id else None
        if venue is None:
            summary["errors"].append(
                f"Could not map document '{external_doc_id}' to venue external_id '{venue_external_id}'."
            )
            continue

        document = SourceDocument(
            external_doc_id=external_doc_id,
            venue_id=venue.id,
            title=record["title"],
            document_type=_infer_document_type(record["title"]),
            content=record["content"],
        )
        document_repository.create(document)
        summary["created"] += 1

    session.commit()
    return summary


def _run_indexing(
    document_records: list[dict[str, Any]],
    document_repository: DocumentRepository,
    session,
):
    target_document_ids = []
    for record in document_records:
        external_doc_id = record.get("doc_id")
        if not external_doc_id:
            continue
        document = document_repository.get_by_external_id(external_doc_id)
        if document is not None:
            target_document_ids.append(document.id)

    indexing_service = IndexingService(
        session=session,
        document_repository=document_repository,
        chunk_repository=ChunkRepository(session),
    )
    return indexing_service.run_indexing(RunIndexingRequest(document_ids=target_document_ids))


def _infer_document_type(title: str) -> str:
    normalized_title = title.lower()
    if "faq" in normalized_title:
        return "faq"
    if "policy" in normalized_title or "policies" in normalized_title:
        return "policy"
    if "notes" in normalized_title:
        return "notes"
    return "other"


if __name__ == "__main__":
    raise SystemExit(main())
