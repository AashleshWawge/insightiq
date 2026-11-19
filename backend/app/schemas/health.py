from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    """Schema for basic API health check."""
    status: str = Field(..., examples=["ok"])
    app: str = Field(..., examples=["InsightIQ API"])
    version: str = Field(..., examples=["0.1.0"])


class DatabaseHealthResponse(BaseModel):
    """Schema for database health check."""
    status: str = Field(..., examples=["connected"])
    database: str = Field(..., examples=["insightiq"])
    latency_ms: Optional[float] = Field(None, examples=[4.25])
    message: str = Field(..., examples=["Database connection is healthy and responsive."])
