import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str
    original_filename: str


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    original_filename: str
    row_count: int
    status: str
    created_at: datetime


class DatasetUploadResponse(BaseModel):
    dataset_id: uuid.UUID
    filename: str
    total_rows: int
    imported_rows: int
    rejected_rows: int
    status: str


class SaleRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: str
    order_date: date
    customer_name: str
    city: str
    product_name: str
    category: str
    quantity: int
    unit_price: Decimal


class DatasetPreviewResponse(BaseModel):
    dataset_id: uuid.UUID
    filename: str
    total_rows: int
    preview_count: int
    rows: List[SaleRowResponse]
