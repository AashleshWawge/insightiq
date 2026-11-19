import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class QueryHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: uuid.UUID
    question: str
    generated_sql: Optional[str] = None
    status: str
    row_count: int
    created_at: datetime
