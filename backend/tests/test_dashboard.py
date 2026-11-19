import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_or_create_dataset_id() -> str:
    """Retrieve an existing dataset ID or upload sample dataset if none exist."""
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    if datasets:
        return datasets[0]["id"]

    # Upload sample CSV if not present
    from pathlib import Path
    import io
    csv_path = Path(__file__).resolve().parent.parent.parent / "sample_data" / "sales_sample.csv"
    with open(csv_path, "rb") as f:
        up_res = client.post(
            "/api/datasets/upload",
            files={"file": ("sales_sample.csv", io.BytesIO(f.read()), "text/csv")},
        )
    assert up_res.status_code == 201
    return up_res.json()["dataset_id"]


def test_dashboard_summary():
    dataset_id = _get_or_create_dataset_id()
    res = client.get(f"/api/dashboard/{dataset_id}/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] > 0
    assert data["total_orders"] > 0
    assert data["total_units_sold"] > 0
    assert data["unique_customers"] > 0
    assert data["average_order_value"] > 0


def test_dashboard_monthly_revenue():
    dataset_id = _get_or_create_dataset_id()
    res = client.get(f"/api/dashboard/{dataset_id}/monthly-revenue")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) > 0
    first = items[0]
    assert "month" in first
    assert "revenue" in first
    assert "order_count" in first
    assert first["revenue"] >= 0


def test_dashboard_category_revenue():
    dataset_id = _get_or_create_dataset_id()
    res = client.get(f"/api/dashboard/{dataset_id}/category-revenue")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) > 0
    # Verify sorted descending by revenue
    revenues = [item["revenue"] for item in items]
    assert revenues == sorted(revenues, reverse=True)


def test_dashboard_city_revenue():
    dataset_id = _get_or_create_dataset_id()
    res = client.get(f"/api/dashboard/{dataset_id}/city-revenue")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) > 0
    assert "city" in items[0]


def test_dashboard_top_products():
    dataset_id = _get_or_create_dataset_id()
    res = client.get(f"/api/dashboard/{dataset_id}/top-products?limit=5")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) <= 5
    assert len(items) > 0
    # Verify sorted descending by revenue
    revenues = [item["revenue"] for item in items]
    assert revenues == sorted(revenues, reverse=True)


def test_dashboard_404_nonexistent_dataset():
    random_uuid = str(uuid.uuid4())
    res = client.get(f"/api/dashboard/{random_uuid}/summary")
    assert res.status_code == 404
