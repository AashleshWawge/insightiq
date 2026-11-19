from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns HTTP 200 with welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "InsightIQ API"


def test_api_health_endpoint():
    """Verify that backend health endpoint returns HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_database_health_endpoint():
    """Verify that database health endpoint connects to PostgreSQL."""
    response = client.get("/api/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["database"] == "insightiq"
    assert "latency_ms" in data
    assert data["latency_ms"] >= 0
