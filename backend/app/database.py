from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.config import DATABASE_URL

# The Engine is the starting point for any SQLAlchemy application.
# It maintains a pool of database connections that can be reused.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Automatically check if a connection is still alive before using it
    pool_size=5,         # Keep up to 5 connections in the pool
    max_overflow=10,     # Allow up to 10 additional connections during traffic spikes
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
