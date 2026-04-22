# TeloHive Venue Knowledge Assistant API

A backend-first FastAPI application that ingests structured venue data and unstructured venue documents, prepares them for retrieval, and answers venue-related questions using grounded supporting excerpts.

## Problem Summary

Internal TeloHive users need to search venue knowledge across:
- structured venue records
- venue policies
- FAQ content
- operational notes
- booking-related information

This project implements a backend API that:
- stores venue metadata and source documents
- chunks and normalizes document content for retrieval
- answers natural-language venue questions
- returns supporting source excerpts
- persists query history for inspection

The implementation intentionally prioritizes clean backend architecture, explainability, testing, and maintainability over flashy AI features.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose
- Pytest

## Architecture Overview

The backend follows a layered structure:

- **API layer**: request/response handling and route definitions
- **Service layer**: business workflows such as ingestion, indexing, retrieval, and querying
- **Repository layer**: database access
- **Persistence layer**: SQLAlchemy models and Alembic migrations

### Core entities

- `venues`
- `source_documents`
- `document_chunks`
- `query_logs`
- `query_sources`

## Features

### Foundation
- FastAPI app bootstrapped with Docker Compose
- PostgreSQL persistence
- SQLAlchemy ORM models
- Alembic migrations
- venue/document create and read endpoints

### Indexing
- deterministic character-based chunking
- normalized lexical content generation
- indexing endpoint
- chunk inspection endpoint

### Baseline retrieval and answering
- rule-based query parsing
- candidate venue/chunk selection
- lexical/rule-based scoring
- cautious grounded answer generation
- confidence scoring
- query persistence and inspection

## Retrieval Design

This implementation uses a **baseline lexical/rule-based retrieval approach**.

### Current baseline signals
The current relevance and confidence logic uses only:

1. exact/normalized keyword matches  
2. phrase matches  
3. structured metadata matches  
4. number of matched query constraints  
5. agreement between structured and document evidence  

### Why this approach
I chose to first build a transparent and explainable retrieval baseline before introducing semantic search. This keeps the system easy to defend and test.

### Current answer behavior
The system returns:
- `answer`
- `confidence_score`
- `sources`

Answers are built from retrieved evidence only. When support is weak or partial, the system returns a cautious answer instead of overclaiming.

## Data Model

### Venue fields
Structured venue records include fields such as:
- external id
- name
- city
- neighborhood
- capacity
- price per head
- venue type
- description
- amenities
- tags
- outside catering
- alcohol allowed
- minimum notice days

### Source document fields
Documents include:
- external doc id
- linked venue id
- title
- document type
- content
- ingestion status

### Chunk fields
Indexed chunks store:
- linked document id
- linked venue id
- chunk index
- original content
- normalized content
- document title
- document type

## Local Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <repo-name>
```

### 2. Create env file
```bash
cp .env.example .env
```

### 3. Start services
```bash
docker compose up --build
```

### 4. Apply migrations
If migrations are not already applied automatically:
```bash
docker compose exec api alembic upgrade head
```

### 5. Wipe and recreate the DB
```bash
docker compose down -v
docker compose up --build
```

## Sample Data

Sample data lives in:
- `sample_data/venues.json`
- `sample_data/venue_docs.json`

### Seed sample data

Assuming Docker Compose is already running the database:

```bash
python3 scripts/seed_sample_data.py
python3 scripts/seed_sample_data.py --index
```


## Running Indexing

Index all pending documents:
```bash
curl -X POST http://localhost:8000/indexing/run
```

Index selected documents:
```bash
curl -X POST http://localhost:8000/indexing/run \
  -H "Content-Type: application/json" \
  -d '{"document_ids":["YOUR-DOC-UUID"]}'
```

## Running the API

FastAPI docs:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Running Tests

```bash
pytest -q
```

## API Endpoint Summary

### Health
- `GET /health`

### Venues
- `POST /venues`
- `GET /venues`

### Documents
- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`

### Indexing
- `POST /indexing/run`
- `GET /documents/{document_id}/chunks`

### Queries
- `POST /queries`
- `GET /queries/{query_id}`

## Example API Usage

Note: a Postman collection for the main API flow is included in `postman/`.

### Create a venue
```bash
curl -X POST http://localhost:8000/venues \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "venue_001",
    "name": "Skyline Foundry",
    "city": "Boston",
    "neighborhood": "Seaport",
    "capacity": 120,
    "price_per_head_usd": 95,
    "venue_type": "rooftop",
    "amenities": ["AV", "bar", "wifi", "private_room"],
    "tags": ["startup", "networking", "demo_day", "industrial"],
    "description": "Industrial-style rooftop venue suitable for startup mixers, product launches, and private evening events.",
    "outside_catering": false,
    "alcohol_allowed": true,
    "min_notice_days": 7
  }'
```

### Create a document
```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "external_doc_id": "doc_001",
    "venue_id": "YOUR-VENUE-UUID",
    "title": "Skyline Foundry FAQ",
    "document_type": "faq",
    "content": "Skyline Foundry supports startup mixers, networking events, and demo days. Outside catering is not allowed. Built-in AV support includes wireless microphones, projector output, and a presentation monitor."
  }'
```

### Ask a question
```bash
curl -X POST http://localhost:8000/queries \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which venues allow outside catering?"
  }'
```

## Design Decisions and Tradeoffs

### Why lexical/rule-based retrieval first
I intentionally started with a transparent baseline instead of jumping directly to embeddings or LLM-based answering. This made the retrieval logic easier to test, reason about, and defend.

### Why character-based chunking
For the baseline, deterministic character-based chunking was sufficient and simpler to implement than token-aware chunking.

### Why no auth
Authentication was not required for the take-home, so I kept the scope focused on backend retrieval quality and API design.

### Why no full CRUD
I intentionally limited the API to the flows most relevant to the task:
- create/read venues
- create/read documents
- indexing
- querying
- query inspection

## Known Limitations

- retrieval is lexical/rule-based, not semantic
- query parsing is intentionally narrow and tuned to the current domain/sample data
- answer wording is deterministic and conservative rather than LLM-generated
- no update/delete endpoints for venues or documents
- no file upload/OCR pipeline
- no auth or multi-user support
- no deployment target beyond local Docker setup

## What I Would Improve With 1–2 More Days

- add semantic or hybrid retrieval using embeddings
- improve query parsing coverage and synonym handling
- improve answer synthesis when one candidate is the strongest available match
- add update/delete endpoints with safe re-indexing behavior
- add a cleaner seed/import workflow and more varied sample documents
- add richer observability or score-breakdown inspection

## Manual Validation

A manual query pack used for baseline validation is included here:

- `docs/MANUAL_QUERY_PACK_BASELINE.md`

It covers:
- direct policy queries
- feature queries
- capacity-constrained queries
- multi-constraint partial-match queries
- low-evidence fallback cases

## Submission Notes

This project is intentionally scoped around:
- backend architecture
- schema design
- indexing and retrieval preparation
- explainable baseline ranking
- cautious grounded answers
- testing and documentation

I prioritized correctness, clarity, and defendability over feature breadth.
