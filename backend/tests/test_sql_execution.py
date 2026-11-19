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


def test_execute_valid_query():
    """Verify that a valid read-only query executes and returns rows and columns."""
    dataset_id = _get_dataset_id()
    sql = "SELECT product_name, SUM(quantity * unit_price) AS revenue FROM sales GROUP BY product_name ORDER BY revenue DESC LIMIT 3"

    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": dataset_id, "sql": sql},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["execution_status"] == "success"
    assert "product_name" in data["columns"]
    assert "revenue" in data["columns"]
    assert len(data["rows"]) == 3
    assert data["row_count"] == 3
    assert data["execution_time_ms"] > 0
    print("\nExecuted Query Results:", data["rows"])


def test_reject_drop_table():
    """Verify that a DROP TABLE attempt is blocked by SQLGlot validation."""
    dataset_id = _get_dataset_id()
    sql = "DROP TABLE sales"

    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": dataset_id, "sql": sql},
    )

    assert response.status_code == 400
    assert "Security Validation Rejected" in response.json()["detail"]


def test_reject_multi_statement():
    """Verify that multiple SQL statements are blocked."""
    dataset_id = _get_dataset_id()
    sql = "SELECT * FROM sales; DROP TABLE sales;"

    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": dataset_id, "sql": sql},
    )

    assert response.status_code == 400
    assert "Multiple SQL statements" in response.json()["detail"]


def test_reject_update():
    """Verify that UPDATE statements are blocked."""
    dataset_id = _get_dataset_id()
    sql = "UPDATE sales SET quantity = 999"

    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": dataset_id, "sql": sql},
    )

    assert response.status_code == 400
    assert "Only read-only SELECT" in response.json()["detail"]


def test_reject_unauthorized_table():
    """Verify that accessing system catalogs or non-sales tables is blocked."""
    dataset_id = _get_dataset_id()
    sql = "SELECT * FROM pg_catalog.pg_user"

    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": dataset_id, "sql": sql},
    )

    assert response.status_code == 400
    assert "Unauthorized table access" in response.json()["detail"]


def test_reject_dangerous_function():
    """Verify that calling sleep or restricted functions is blocked."""
    dataset_id = _get_dataset_id()
    sql = "SELECT pg_sleep(5) FROM sales"

    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": dataset_id, "sql": sql},
    )

    assert response.status_code == 400
    assert "Dangerous or restricted functions" in response.json()["detail"]


def test_execute_query_404_dataset():
    """Verify that querying a non-existent dataset returns 404."""
    random_uuid = str(uuid.uuid4())
    response = client.post(
        "/api/ai/execute-query",
        json={"dataset_id": random_uuid, "sql": "SELECT * FROM sales"},
    )
    assert response.status_code == 404
