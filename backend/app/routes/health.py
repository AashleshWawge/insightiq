import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.schemas.health import HealthResponse, DatabaseHealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def get_backend_health():
    """
    Check if the FastAPI backend service is running and responsive.
    """
    return HealthResponse(
        status="ok",
        app="InsightIQ API",
        version="0.1.0",
    )


@router.get("/database", response_model=DatabaseHealthResponse)
def get_database_health(db: Session = Depends(get_db)):
    """
    Check PostgreSQL connectivity by executing a lightweight ping query ('SELECT 1').
    Measures latency in milliseconds and handles errors safely.
    """
    start_time = time.perf_counter()
    try:
        # Execute lightweight ping query
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return DatabaseHealthResponse(
            status="connected",
            database="insightiq",
            latency_ms=latency_ms,
            message="Database connection is healthy and responsive.",
        )
    except SQLAlchemyError as err:
        # Avoid leaking database credentials in error messages
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to establish a connection to PostgreSQL. Please check database status and configuration.",
        )
