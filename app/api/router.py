from fastapi import APIRouter

from app.api.routes import documents, health, indexing, queries, venues

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(venues.router)
api_router.include_router(documents.router)
api_router.include_router(indexing.router)
api_router.include_router(queries.router)
