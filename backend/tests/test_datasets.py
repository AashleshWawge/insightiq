import io
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "sample_data" / "sales_sample.csv"


def test_upload_valid_csv():
    """Verify that uploading a valid sales CSV succeeds and creates database records."""
    assert SAMPLE_CSV_PATH.exists(), f"Sample CSV file missing at {SAMPLE_CSV_PATH}"

    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales_sample.csv", io.BytesIO(file_bytes), "text/csv")},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert "dataset_id" in data
    assert data["filename"] == "sales_sample.csv"
    assert data["total_rows"] == 180
    assert data["imported_rows"] == 180
    assert data["rejected_rows"] == 0
    assert data["status"] == "ready"

    dataset_id = data["dataset_id"]

    # Verify listing datasets includes this new dataset
    list_res = client.get("/api/datasets")
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert any(d["id"] == dataset_id for d in datasets)

    # Verify dataset details
    detail_res = client.get(f"/api/datasets/{dataset_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["row_count"] == 180
    assert detail["original_filename"] == "sales_sample.csv"

    # Verify preview endpoint returns first 5 rows
    preview_res = client.get(f"/api/datasets/{dataset_id}/preview?limit=5")
    assert preview_res.status_code == 200
    preview = preview_res.json()
    assert preview["preview_count"] == 5
    assert len(preview["rows"]) == 5
    first_row = preview["rows"][0]
    assert "order_id" in first_row
    assert "product_name" in first_row
    assert "unit_price" in first_row

    # Clean up: delete the test dataset
    del_res = client.delete(f"/api/datasets/{dataset_id}")
    assert del_res.status_code == 200

    # Verify 404 after deletion
    after_del_res = client.get(f"/api/datasets/{dataset_id}")
    assert after_del_res.status_code == 404


def test_reject_non_csv():
    """Verify that uploading a non-CSV file is rejected with 400 Bad Request."""
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("notes.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )
    assert response.status_code == 400
    assert "Only CSV files" in response.json()["detail"]


def test_reject_empty_csv():
    """Verify that uploading an empty CSV file is rejected with 400 Bad Request."""
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_reject_missing_required_headers():
    """Verify that a CSV missing required columns is rejected with a descriptive error."""
    bad_csv = "order_id,product_name\n101,Keyboard"
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("bad_headers.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Missing required columns" in detail


def test_upload_with_column_aliases():
    """Verify that CSV with synonym column headers (customer_id, unit_selling_price_inr) is accepted."""
    aliased_csv = (
        "order_id,order_date,customer_id,city,product_name,category,quantity,unit_selling_price_inr\n"
        "ORD-001,2025-01-15,CUST-01,Mumbai,Laptop Stand,Accessories,2,1499.00\n"
    )
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("aliased_sample.csv", io.BytesIO(aliased_csv.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["imported_rows"] == 1
    ds_id = data["dataset_id"]

    # Clean up
    client.delete(f"/api/datasets/{ds_id}")
