import uuid
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_dashboard_summary(db: Session, dataset_id: uuid.UUID) -> Dict[str, Any]:
    """
    Computes primary business KPIs using database-level SQL aggregations:
    - Total Revenue = SUM(quantity * unit_price)
    - Total Orders = COUNT(DISTINCT order_id)
    - Total Units Sold = SUM(quantity)
    - Unique Customers = COUNT(DISTINCT customer_name)
    - Average Order Value = Total Revenue / Total Orders
    """
    query = text("""
        SELECT
            COALESCE(SUM(quantity * unit_price), 0) AS total_revenue,
            COUNT(DISTINCT order_id) AS total_orders,
            COALESCE(SUM(quantity), 0) AS total_units_sold,
            COUNT(DISTINCT customer_name) AS unique_customers
        FROM sales
        WHERE dataset_id = :dataset_id
    """)

    result = db.execute(query, {"dataset_id": dataset_id}).mappings().first()

    total_revenue = float(result["total_revenue"])
    total_orders = int(result["total_orders"])
    total_units_sold = int(result["total_units_sold"])
    unique_customers = int(result["unique_customers"])

    average_order_value = (
        round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    )

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_units_sold": total_units_sold,
        "unique_customers": unique_customers,
        "average_order_value": average_order_value,
    }


def get_monthly_revenue(db: Session, dataset_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Aggregates revenue and order count chronologically by month (YYYY-MM).
    """
    query = text("""
        SELECT
            TO_CHAR(order_date, 'YYYY-MM') AS month,
            COALESCE(SUM(quantity * unit_price), 0) AS revenue,
            COUNT(DISTINCT order_id) AS order_count
        FROM sales
        WHERE dataset_id = :dataset_id
        GROUP BY TO_CHAR(order_date, 'YYYY-MM')
        ORDER BY month ASC
    """)

    rows = db.execute(query, {"dataset_id": dataset_id}).mappings().all()
    return [
        {
            "month": row["month"],
            "revenue": round(float(row["revenue"]), 2),
            "order_count": int(row["order_count"]),
        }
        for row in rows
    ]


def get_category_revenue(db: Session, dataset_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Aggregates revenue and units sold by product category, sorted descending by revenue.
    """
    query = text("""
        SELECT
            category,
            COALESCE(SUM(quantity * unit_price), 0) AS revenue,
            COALESCE(SUM(quantity), 0) AS units_sold
        FROM sales
        WHERE dataset_id = :dataset_id
        GROUP BY category
        ORDER BY revenue DESC
    """)

    rows = db.execute(query, {"dataset_id": dataset_id}).mappings().all()
    return [
        {
            "category": row["category"],
            "revenue": round(float(row["revenue"]), 2),
            "units_sold": int(row["units_sold"]),
        }
        for row in rows
    ]


def get_city_revenue(db: Session, dataset_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Aggregates revenue and order count by customer city, sorted descending by revenue.
    """
    query = text("""
        SELECT
            city,
            COALESCE(SUM(quantity * unit_price), 0) AS revenue,
            COUNT(DISTINCT order_id) AS order_count
        FROM sales
        WHERE dataset_id = :dataset_id
        GROUP BY city
        ORDER BY revenue DESC
    """)

    rows = db.execute(query, {"dataset_id": dataset_id}).mappings().all()
    return [
        {
            "city": row["city"],
            "revenue": round(float(row["revenue"]), 2),
            "order_count": int(row["order_count"]),
        }
        for row in rows
    ]


def get_top_products(
    db: Session, dataset_id: uuid.UUID, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieves the top N products by total revenue.
    """
    query = text("""
        SELECT
            product_name,
            category,
            COALESCE(SUM(quantity * unit_price), 0) AS revenue,
            COALESCE(SUM(quantity), 0) AS units_sold
        FROM sales
        WHERE dataset_id = :dataset_id
        GROUP BY product_name, category
        ORDER BY revenue DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"dataset_id": dataset_id, "limit": limit}).mappings().all()
    return [
        {
            "product_name": row["product_name"],
            "category": row["category"],
            "revenue": round(float(row["revenue"]), 2),
            "units_sold": int(row["units_sold"]),
        }
        for row in rows
    ]
