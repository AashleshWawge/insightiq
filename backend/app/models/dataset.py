import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Dataset(Base):
    """
    Represents an uploaded dataset.
    All sales records and query histories imported from or executed on a file are linked to this dataset.
    """
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="ready", nullable=False)  # uploaded, processing, ready, failed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Cascade delete ensures that deleting a dataset also removes all associated sales and history
    sales = relationship("Sale", back_populates="dataset", cascade="all, delete-orphan")
    query_histories = relationship("QueryHistory", back_populates="dataset", cascade="all, delete-orphan")
