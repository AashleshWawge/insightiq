import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AITestRequest(BaseModel):
    """Schema for test AI prompt request."""
    prompt: Optional[str] = Field(
        default="In two sentences, explain the difference between WHERE and HAVING in SQL.",
        description="A prompt to test Groq response generation.",
    )


class AITestResponse(BaseModel):
    """Schema for test AI response."""
    status: str
    model: str
    latency_ms: float
    prompt: str
    response: str


class GenerateQueryRequest(BaseModel):
    """Schema for generating SQL from natural language."""
    dataset_id: uuid.UUID = Field(..., description="ID of the dataset being queried")
    question: str = Field(..., min_length=3, description="Natural language business question")


class GenerateQueryResponse(BaseModel):
    """Schema for generated SQL and explanation."""
    dataset_id: uuid.UUID
    question: str
    sql: Optional[str] = Field(None, description="Generated PostgreSQL query")
    explanation: str = Field(..., description="Plain-English explanation of the query or refusal")
    chart_type: Optional[str] = Field(None, description="Suggested visualization: bar, line, pie, or table")
    can_answer: bool = Field(True, description="Whether the question can be answered from the schema")
    latency_ms: float = Field(..., description="Generation time in milliseconds")


class ExecuteQueryRequest(BaseModel):
    """Schema for executing a validated SQL query."""
    dataset_id: uuid.UUID = Field(..., description="Dataset ID to isolate and execute against")
    sql: str = Field(..., min_length=5, description="SQL query approved by the user for execution")
    question: Optional[str] = Field(None, description="Original natural-language question for history tracking")


class ExecuteQueryResponse(BaseModel):
    """Schema for query execution results."""
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_status: str
    execution_time_ms: float
    history_id: Optional[int] = None
    error_message: Optional[str] = None


class ExplainResultsRequest(BaseModel):
    """Schema for AI result explanation and chart recommendation."""
    question: str = Field(..., description="The user's original business question")
    columns: List[str] = Field(..., description="List of returned column names")
    sample_rows: List[Dict[str, Any]] = Field(..., description="Sample of returned data rows (up to 10)")
    total_row_count: int = Field(..., description="Total number of rows returned by PostgreSQL")


class ExplainResultsResponse(BaseModel):
    """Schema for AI explanation and dynamic chart recommendation."""
    explanation: str = Field(..., description="Plain-English explanation based strictly on returned data")
    recommended_chart: str = Field(..., description="Recommended chart type: bar, line, pie, or table")
    latency_ms: float
