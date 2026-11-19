from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    """Overall business KPIs for a given dataset."""
    total_revenue: float = Field(..., description="Total sales revenue (quantity * unit_price)")
    total_orders: int = Field(..., description="Distinct order count")
    total_units_sold: int = Field(..., description="Total quantity of products sold")
    unique_customers: int = Field(..., description="Count of distinct customers")
    average_order_value: float = Field(..., description="Average revenue per order")


class MonthlyRevenueItem(BaseModel):
    """Monthly revenue breakdown."""
    month: str = Field(..., description="Month in YYYY-MM format")
    revenue: float
    order_count: int


class CategoryRevenueItem(BaseModel):
    """Category revenue breakdown."""
    category: str
    revenue: float
    units_sold: int


class CityRevenueItem(BaseModel):
    """City revenue breakdown."""
    city: str
    revenue: float
    order_count: int


class TopProductItem(BaseModel):
    """Top selling product by revenue."""
    product_name: str
    category: str
    revenue: float
    units_sold: int
