import time
import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.limiter import limiter
from app.models.dataset import Dataset
from app.models.query_history import QueryHistory
from app.schemas.ai import (
    AITestRequest,
    AITestResponse,
    GenerateQueryRequest,
    GenerateQueryResponse,
    ExecuteQueryRequest,
    ExecuteQueryResponse,
    ExplainResultsRequest,
    ExplainResultsResponse,
)
from app.services.ai_service import generate_text
from app.services.text_to_sql import generate_sql_from_question
from app.services.sql_validator import validate_and_sanitize_sql
from app.services.result_explainer import explain_query_results

router = APIRouter(prefix="/ai", tags=["AI"])


def _serialize_cell(value: Any) -> Any:
    """Helper to ensure all database values serialize cleanly to JSON."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


@router.post("/test", response_model=AITestResponse)
@limiter.limit("5/minute")
def test_ai_connection(
    request: Request,
    payload: AITestRequest = AITestRequest(),
):
    """
    Test endpoint to verify Groq API connectivity, latency, and model responses.
    """
    prompt = payload.prompt or "In two sentences, explain what SQL SELECT does."
    system_prompt = (
        "You are an expert full-stack developer and AI mentor for InsightIQ. "
        "Keep your response concise, educational, and accurate."
    )

    try:
        result = generate_text(prompt=prompt, system_prompt=system_prompt)
        return AITestResponse(
            status="success",
            model=result["model"],
            latency_ms=result["latency_ms"],
            prompt=prompt,
            response=result["text"],
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(val_err),
        )
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(run_err),
        )


@router.post("/generate-query", response_model=GenerateQueryResponse)
@limiter.limit("5/minute")
def generate_query_endpoint(
    request: Request,
    payload: GenerateQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Converts a natural language question into a safe PostgreSQL query and plain-English explanation.
    Does NOT execute the query. The user must review the SQL before execution.
    """
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{payload.dataset_id}' not found.",
        )

    try:
        result = generate_sql_from_question(
            question=payload.question,
            dataset_id=payload.dataset_id,
        )
        return GenerateQueryResponse(**result)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SQL query: {str(err)}",
        )


@router.post("/execute-query", response_model=ExecuteQueryResponse)
@limiter.limit("10/minute")
def execute_query_endpoint(
    request: Request,
    payload: ExecuteQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Validates and safely executes an approved SQL query against PostgreSQL:
    1. Verifies dataset exists.
    2. Enforces SQLGlot AST security (single statement, SELECT only, sales table only, no dangerous functions).
    3. Enforces dataset isolation filter.
    4. Enforces database engine read-only transaction and 5-second timeout.
    5. Records the query in query_history.
    6. Returns rows, columns, and execution timing.
    """
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{payload.dataset_id}' not found.",
        )

    try:
        sanitized_sql = validate_and_sanitize_sql(
            raw_sql=payload.sql,
            dataset_id=payload.dataset_id,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Validation Rejected: {str(val_err)}",
        )

    start_time = time.perf_counter()
    history_entry = None
    try:
        db.execute(text("SET TRANSACTION READ ONLY;"))
        db.execute(text("SET LOCAL statement_timeout = 5000;"))

        result = db.execute(text(sanitized_sql), {"dataset_id": payload.dataset_id})
        columns = list(result.keys())
        raw_rows = result.mappings().fetchall()

        rows: List[Dict[str, Any]] = [
            {col: _serialize_cell(row[col]) for col in columns}
            for row in raw_rows
        ]

        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        db.rollback()

        # Save to Query History
        try:
            history_entry = QueryHistory(
                dataset_id=payload.dataset_id,
                question=payload.question or "Manual or Approved Query",
                generated_sql=sanitized_sql,
                status="executed",
                row_count=len(rows),
            )
            db.add(history_entry)
            db.commit()
            db.refresh(history_entry)
        except Exception:
            db.rollback()

        return ExecuteQueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_status="success",
            execution_time_ms=execution_time_ms,
            history_id=history_entry.id if history_entry else None,
        )
    except SQLAlchemyError as err:
        db.rollback()
        err_msg = str(err.orig) if hasattr(err, "orig") else str(err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database query execution error: {err_msg}",
        )
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected execution error: {str(err)}",
        )


@router.post("/explain-results", response_model=ExplainResultsResponse)
@limiter.limit("5/minute")
def explain_results_endpoint(
    request: Request,
    payload: ExplainResultsRequest,
):
    """
    Sends returned result rows to Groq to produce a plain-English explanation
    and a dynamic visualization recommendation (bar, line, pie, or table).
    """
    try:
        result = explain_query_results(
            question=payload.question,
            columns=payload.columns,
            sample_rows=payload.sample_rows,
            total_row_count=payload.total_row_count,
        )
        return ExplainResultsResponse(**result)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain query results: {str(err)}",
        )
