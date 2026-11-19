from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, String, Date, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Sale(Base):
    """
    Represents an individual sales record imported from a CSV.
    Enforces dataset isolation by binding every row to a specific dataset_id.
    """
    __tablename__ = "sales"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(100), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    dataset = relationship("Dataset", back_populates="sales")
