from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_test_endpoint():
    """Verify that the /api/ai/test endpoint successfully communicates with Groq."""
    response = client.post(
        "/api/ai/test",
        json={"prompt": "In one short sentence, define what a database index is."},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert "model" in data
    assert data["latency_ms"] > 0
    assert len(data["response"]) > 0
    print("\nGroq AI Response:", data["response"])
