from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_explain_results_endpoint():
    """Verify that returned data rows are explained in plain English by Groq."""
    response = client.post(
        "/api/ai/explain-results",
        json={
            "question": "Which product generated the highest revenue?",
            "columns": ["product_name", "revenue"],
            "sample_rows": [
                {"product_name": "Ergonomic Office Chair", "revenue": 612500.0},
                {"product_name": "Standing Desk Converter", "revenue": 391600.0},
                {"product_name": "Noise-Cancelling Headphones", "revenue": 307956.0},
            ],
            "total_row_count": 3,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "explanation" in data
    assert len(data["explanation"]) > 10
    assert data["recommended_chart"] in {"bar", "line", "pie", "table"}
    print("\nAI Result Explanation:", data["explanation"])
    print("AI Recommended Chart:", data["recommended_chart"])
