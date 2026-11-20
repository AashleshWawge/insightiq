import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.models.dataset import Dataset
from app.models.sale import Sale
from app.schemas.dataset import (
    DatasetResponse,
    DatasetUploadResponse,
    DatasetPreviewResponse,
    SaleRowResponse,
)
from app.services.csv_ingestion import validate_and_ingest_csv

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest a CSV sales dataset.
    Validates headers, data types, and positive quantities/prices using Pandas.
    Saves records atomically to PostgreSQL.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are supported.",
        )

    try:
        file_bytes = await file.read()
        summary = validate_and_ingest_csv(
            file_bytes=file_bytes,
            filename=file.filename,
            db=db,
        )
        return summary
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during ingestion: {str(err)}",
        )


@router.get("", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """
    Retrieve all uploaded datasets, sorted by newest first.
    """
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve details for a single dataset by its UUID.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
    return dataset


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    dataset_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=100, description="Number of preview rows to return"),
    db: Session = Depends(get_db),
):
    """
    Preview the first N rows of an imported sales dataset.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    rows = (
        db.query(Sale)
        .filter(Sale.dataset_id == dataset_id)
        .order_by(Sale.id.asc())
        .limit(limit)
        .all()
    )

    return DatasetPreviewResponse(
        dataset_id=dataset.id,
        filename=dataset.original_filename,
        total_rows=dataset.row_count,
        preview_count=len(rows),
        rows=rows,
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK)
def delete_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a dataset and cascade-delete all its associated sales records.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    db.delete(dataset)
    db.commit()
    return {"message": f"Dataset '{dataset.name}' and all associated sales records were deleted."}
