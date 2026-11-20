from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.config import DATABASE_URL

# The Engine maintains a small pool of database connections to support Neon scale-to-zero.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Check if connection is alive before using it
    pool_size=2,         # Keep connections low to prevent holding idle connections against Neon
    max_overflow=3,      # Allow modest overflow during concurrent requests
    pool_recycle=300,    # Recycle connections after 5 minutes so Neon compute can scale to zero
)

# SessionLocal is a class factory for creating new Session objects.
# autocommit=False ensures transactions are explicitly controlled.
# autoflush=False prevents automatic flushing of changes before queries.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models. Models in Phase 2 will inherit from this.
Base = declarative_base()


def get_db() -> Generator:
    """
    FastAPI dependency that provides a database session for each request.
    Using 'yield' ensures that the session is closed after the request finishes,
    even if an error occurs during processing.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
