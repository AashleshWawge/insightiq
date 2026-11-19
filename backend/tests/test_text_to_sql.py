import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_dataset_id() -> str:
    """Retrieve an existing dataset ID from PostgreSQL."""
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) > 0, "No datasets available for test."
    return datasets[0]["id"]


def test_generate_query_top_products():
    """Verify that a top products question generates a valid SELECT query."""
    dataset_id = _get_dataset_id()
    response = client.post(
        "/api/ai/generate-query",
        json={
            "dataset_id": dataset_id,
            "question": "Show the top five products by revenue",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["can_answer"] is True
    assert data["sql"] is not None
    sql_upper = data["sql"].upper()
    assert "SELECT" in sql_upper
    assert "FROM SALES" in sql_upper or "FROM  SALES" in sql_upper or "SALES" in sql_upper
    assert "SUM" in sql_upper
    assert "PRODUCT_NAME" in sql_upper
    assert len(data["explanation"]) > 10
    print("\nGenerated Top Products SQL:", data["sql"])


def test_generate_query_monthly_revenue():
    """Verify that a monthly revenue question generates an aggregated date query."""
    dataset_id = _get_dataset_id()
    response = client.post(
        "/api/ai/generate-query",
        json={
            "dataset_id": dataset_id,
            "question": "What is our monthly revenue trend?",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["can_answer"] is True
    assert data["sql"] is not None
    sql_upper = data["sql"].upper()
    assert "SELECT" in sql_upper
    assert "ORDER_DATE" in sql_upper
    assert "SUM" in sql_upper
    print("\nGenerated Monthly Revenue SQL:", data["sql"])


def test_generate_query_out_of_scope():
    """Verify that an unanswerable question returns can_answer=False and no SQL."""
    dataset_id = _get_dataset_id()
    response = client.post(
        "/api/ai/generate-query",
        json={
            "dataset_id": dataset_id,
            "question": "What is the average employee salary in HR?",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["can_answer"] is False
    assert data["sql"] is None
    assert "salary" in data["explanation"].lower() or "employee" in data["explanation"].lower()
    print("\nOut-of-scope explanation:", data["explanation"])


def test_generate_query_404_dataset():
    """Verify that a non-existent dataset ID returns 404."""
    random_uuid = str(uuid.uuid4())
    response = client.post(
        "/api/ai/generate-query",
        json={
            "dataset_id": random_uuid,
            "question": "What is total revenue?",
        },
    )
    assert response.status_code == 404
