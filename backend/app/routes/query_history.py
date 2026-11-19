import io
import csv
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.query_history import QueryHistory
from app.schemas.query_history import QueryHistoryResponse
from app.services.sql_validator import validate_and_sanitize_sql

router = APIRouter(prefix="/query-history", tags=["Query History"])


@router.get("", response_model=List[QueryHistoryResponse])
def get_query_history(
    dataset_id: Optional[uuid.UUID] = Query(None, description="Filter history by dataset"),
    limit: int = Query(50, ge=1, le=100, description="Max history items to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve past questions and executed queries, sorted by newest first.
    """
    query = db.query(QueryHistory)
    if dataset_id:
        query = query.filter(QueryHistory.dataset_id == dataset_id)
    history_items = query.order_by(QueryHistory.created_at.desc()).limit(limit).all()
    return history_items


@router.get("/{history_id}", response_model=QueryHistoryResponse)
def get_query_history_item(history_id: int, db: Session = Depends(get_db)):
    """
    Retrieve details for a single query history record.
    """
    item = db.query(QueryHistory).filter(QueryHistory.id == history_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query history item not found.",
        )
    return item


@router.delete("/{history_id}", status_code=status.HTTP_200_OK)
def delete_query_history_item(history_id: int, db: Session = Depends(get_db)):
    """
    Delete a single query history record.
    """
    item = db.query(QueryHistory).filter(QueryHistory.id == history_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query history item not found.",
        )
    db.delete(item)
    db.commit()
    return {"message": "Query history item deleted successfully."}


@router.get("/{history_id}/export")
def export_query_results_csv(history_id: int, db: Session = Depends(get_db)):
    """
    Safely re-executes the saved SQL query and exports its results as a downloadable CSV.
    """
    item = db.query(QueryHistory).filter(QueryHistory.id == history_id).first()
    if not item or not item.generated_sql:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query history item not found or contains no executable SQL.",
        )

    # Re-validate SQL
    sanitized_sql = validate_and_sanitize_sql(item.generated_sql, item.dataset_id)

    try:
        db.execute(text("SET TRANSACTION READ ONLY;"))
        db.execute(text("SET LOCAL statement_timeout = 5000;"))
        result = db.execute(text(sanitized_sql), {"dataset_id": item.dataset_id})
        columns = list(result.keys())
        rows = result.fetchall()
        db.rollback()

        # Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(list(row))

        csv_content = output.getvalue()
        output.close()

        filename = f"insightiq_query_{history_id}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export query results: {str(e)}",
        )
