from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class QueryHistory(Base):
    """
    Stores history of user questions, generated SQL, execution status, and returned row counts.
    Linked to specific datasets to maintain dataset isolation.
    """
    __tablename__ = "query_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=True)
    status = Column(String(50), default="generated", nullable=False)  # generated, executed, failed
    row_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    dataset = relationship("Dataset", back_populates="query_histories")
