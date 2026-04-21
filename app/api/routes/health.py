from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import check_database_connection, get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        check_database_connection(db)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "ok"}
