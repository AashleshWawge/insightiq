import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    MonthlyRevenueItem,
    CategoryRevenueItem,
    CityRevenueItem,
    TopProductItem,
)
from app.services.dashboard import (
    get_dashboard_summary,
    get_monthly_revenue,
    get_category_revenue,
    get_city_revenue,
    get_top_products,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _verify_dataset_exists(dataset_id: uuid.UUID, db: Session) -> Dataset:
    """Helper to verify that the requested dataset exists."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return dataset


@router.get("/{dataset_id}/summary", response_model=DashboardSummaryResponse)
def get_summary_metrics(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get high-level business KPI metrics:
    - Total Revenue
    - Total Orders
    - Total Units Sold
    - Unique Customers
    - Average Order Value
    """
    _verify_dataset_exists(dataset_id, db)
    return get_dashboard_summary(db, dataset_id)


@router.get("/{dataset_id}/monthly-revenue", response_model=List[MonthlyRevenueItem])
def get_monthly_revenue_metrics(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get chronological monthly sales revenue and order counts.
    """
    _verify_dataset_exists(dataset_id, db)
    return get_monthly_revenue(db, dataset_id)


@router.get("/{dataset_id}/category-revenue", response_model=List[CategoryRevenueItem])
def get_category_revenue_metrics(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get sales revenue and units sold grouped by product category.
    """
    _verify_dataset_exists(dataset_id, db)
    return get_category_revenue(db, dataset_id)


@router.get("/{dataset_id}/city-revenue", response_model=List[CityRevenueItem])
def get_city_revenue_metrics(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get sales revenue and order counts grouped by customer city.
    """
    _verify_dataset_exists(dataset_id, db)
    return get_city_revenue(db, dataset_id)


@router.get("/{dataset_id}/top-products", response_model=List[TopProductItem])
def get_top_products_metrics(
    dataset_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=20, description="Number of top products to return"),
    db: Session = Depends(get_db),
):
    """
    Get top selling products ranked by revenue.
    """
    _verify_dataset_exists(dataset_id, db)
    return get_top_products(db, dataset_id, limit=limit)
