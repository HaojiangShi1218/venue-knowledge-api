from __future__ import annotations

from uuid import UUID, uuid4

from app.api.routes.documents import get_document_service
from app.api.routes.health import get_db
from app.api.routes.venues import get_venue_service
from app.schemas.document import DocumentRead, DocumentTypeEnum, IngestionStatusEnum
from app.schemas.venue import VenueRead
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError


VENUE_ID = UUID("11111111-1111-1111-1111-111111111111")
DOCUMENT_ID = UUID("22222222-2222-2222-2222-222222222222")


class StubVenueService:
    def __init__(self, *, duplicate: bool = False) -> None:
        self.duplicate = duplicate

    def create_venue(self, payload) -> VenueRead:
        if self.duplicate:
            raise DuplicateResourceError("Venue external_id already exists")

        return VenueRead(
            id=VENUE_ID,
            external_id=payload.external_id,
            name=payload.name,
            city=payload.city,
            neighborhood=payload.neighborhood,
            capacity=payload.capacity,
            price_per_head_usd=payload.price_per_head_usd,
            venue_type=payload.venue_type,
            amenities=payload.amenities,
            tags=payload.tags,
            description=payload.description,
            outside_catering=payload.outside_catering,
            alcohol_allowed=payload.alcohol_allowed,
            min_notice_days=payload.min_notice_days,
            created_at="2026-04-20T00:00:00Z",
            updated_at="2026-04-20T00:00:00Z",
        )

    def list_venues(self, filters) -> list[VenueRead]:
        return [
            VenueRead(
                id=VENUE_ID,
                external_id="venue_001",
                name="Skyline Foundry",
                city=filters.city or "Boston",
                neighborhood=filters.neighborhood or "Seaport",
                capacity=120,
                price_per_head_usd=95,
                venue_type=filters.venue_type or "rooftop",
                amenities=["AV", "bar"],
                tags=["startup"],
                description="Industrial-style rooftop venue.",
                outside_catering=False if filters.outside_catering is None else filters.outside_catering,
                alcohol_allowed=True,
                min_notice_days=7,
                created_at="2026-04-20T00:00:00Z",
                updated_at="2026-04-20T00:00:00Z",
            )
        ]


class StubDocumentService:
    def __init__(
        self,
        *,
        missing_venue: bool = False,
        duplicate: bool = False,
        missing_document: bool = False,
    ) -> None:
        self.missing_venue = missing_venue
        self.duplicate = duplicate
        self.missing_document = missing_document

    def create_document(self, payload) -> DocumentRead:
        if self.missing_venue:
            raise ResourceNotFoundError("Venue not found")
        if self.duplicate:
            raise DuplicateResourceError("Document external_doc_id already exists")

        return DocumentRead(
            id=DOCUMENT_ID,
            external_doc_id=payload.external_doc_id,
            venue_id=payload.venue_id,
            title=payload.title,
            document_type=payload.document_type,
            content=payload.content,
            ingestion_status=IngestionStatusEnum.PENDING,
            created_at="2026-04-20T00:00:00Z",
            updated_at="2026-04-20T00:00:00Z",
        )

    def list_documents(self, filters) -> list[DocumentRead]:
        return [
            DocumentRead(
                id=DOCUMENT_ID,
                external_doc_id="doc_001",
                venue_id=filters.venue_id,
                title="Skyline Foundry FAQ",
                document_type=DocumentTypeEnum.FAQ,
                content="Skyline Foundry supports startup mixers.",
                ingestion_status=IngestionStatusEnum.PENDING
                if filters.ingestion_status is None
                else IngestionStatusEnum(filters.ingestion_status),
                created_at="2026-04-20T00:00:00Z",
                updated_at="2026-04-20T00:00:00Z",
            )
        ]

    def get_document(self, document_id) -> DocumentRead:
        if self.missing_document:
            raise ResourceNotFoundError("Document not found")

        return DocumentRead(
            id=document_id,
            external_doc_id="doc_001",
            venue_id=None,
            title="Skyline Foundry FAQ",
            document_type=DocumentTypeEnum.FAQ,
            content="Skyline Foundry supports startup mixers.",
            ingestion_status=IngestionStatusEnum.PENDING,
            created_at="2026-04-20T00:00:00Z",
            updated_at="2026-04-20T00:00:00Z",
        )


def override_db():
    return object()


def test_health_returns_ok_when_database_is_reachable(client, monkeypatch) -> None:
    from app.main import app

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("app.api.routes.health.check_database_connection", lambda db: None)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_503_when_database_is_unavailable(client, monkeypatch) -> None:
    from app.main import app
    from sqlalchemy.exc import SQLAlchemyError

    app.dependency_overrides[get_db] = override_db

    def fail(_db) -> None:
        raise SQLAlchemyError("db down")

    monkeypatch.setattr("app.api.routes.health.check_database_connection", fail)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_create_venue_returns_201(client) -> None:
    from app.main import app

    app.dependency_overrides[get_venue_service] = lambda: StubVenueService()

    response = client.post(
        "/venues",
        json={
            "external_id": "venue_001",
            "name": "Skyline Foundry",
            "city": "Boston",
            "amenities": ["AV", "bar"],
            "tags": ["startup"],
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(VENUE_ID)
    assert response.json()["external_id"] == "venue_001"


def test_create_venue_returns_409_for_duplicate_external_id(client) -> None:
    from app.main import app

    app.dependency_overrides[get_venue_service] = lambda: StubVenueService(duplicate=True)

    response = client.post(
        "/venues",
        json={
            "external_id": "venue_001",
            "name": "Skyline Foundry",
            "city": "Boston",
            "amenities": [],
            "tags": [],
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Venue external_id already exists"}


def test_list_venues_returns_items_and_count(client) -> None:
    from app.main import app

    app.dependency_overrides[get_venue_service] = lambda: StubVenueService()

    response = client.get("/venues", params={"city": "Boston", "min_capacity": 100})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["city"] == "Boston"


def test_create_document_returns_201(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_service] = lambda: StubDocumentService()

    response = client.post(
        "/documents",
        json={
            "external_doc_id": "doc_001",
            "title": "Skyline Foundry FAQ",
            "document_type": "faq",
            "content": "Skyline Foundry supports startup mixers.",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(DOCUMENT_ID)
    assert response.json()["ingestion_status"] == "pending"


def test_create_document_returns_404_when_venue_is_missing(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_service] = lambda: StubDocumentService(missing_venue=True)

    response = client.post(
        "/documents",
        json={
            "external_doc_id": "doc_002",
            "venue_id": str(uuid4()),
            "title": "Venue FAQ",
            "document_type": "faq",
            "content": "FAQ content",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Venue not found"}


def test_create_document_returns_409_for_duplicate_external_doc_id(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_service] = lambda: StubDocumentService(duplicate=True)

    response = client.post(
        "/documents",
        json={
            "external_doc_id": "doc_001",
            "title": "Venue FAQ",
            "document_type": "faq",
            "content": "FAQ content",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Document external_doc_id already exists"}


def test_list_documents_returns_items_and_count(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_service] = lambda: StubDocumentService()

    response = client.get("/documents", params={"document_type": "faq", "ingestion_status": "pending"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["document_type"] == "faq"


def test_get_document_returns_200(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_service] = lambda: StubDocumentService()

    response = client.get(f"/documents/{DOCUMENT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(DOCUMENT_ID)


def test_get_document_returns_404_when_missing(client) -> None:
    from app.main import app

    app.dependency_overrides[get_document_service] = lambda: StubDocumentService(missing_document=True)

    response = client.get(f"/documents/{DOCUMENT_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}
