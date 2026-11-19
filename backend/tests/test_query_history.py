from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_dataset_id() -> str:
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) > 0
    return datasets[0]["id"]


def test_query_history_workflow():
    dataset_id = _get_dataset_id()

    # 1. Execute a query with a question
    exec_res = client.post(
        "/api/ai/execute-query",
        json={
            "dataset_id": dataset_id,
            "sql": "SELECT product_name, SUM(quantity * unit_price) AS revenue FROM sales GROUP BY product_name ORDER BY revenue DESC LIMIT 3",
            "question": "What are the top 3 products by revenue?",
        },
    )
    assert exec_res.status_code == 200
    history_id = exec_res.json().get("history_id")
    assert history_id is not None

    # 2. Verify query appears in GET /api/query-history
    history_list = client.get(f"/api/query-history?dataset_id={dataset_id}")
    assert history_list.status_code == 200
    items = history_list.json()
    assert any(h["id"] == history_id for h in items)

    # 3. Verify single item fetch
    single_item = client.get(f"/api/query-history/{history_id}")
    assert single_item.status_code == 200
    assert single_item.json()["question"] == "What are the top 3 products by revenue?"

    # 4. Verify CSV export
    csv_res = client.get(f"/api/query-history/{history_id}/export")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "product_name,revenue" in csv_res.text
    print("\nExported CSV preview:\n", csv_res.text)

    # 5. Delete item
    del_res = client.delete(f"/api/query-history/{history_id}")
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    after_del = client.get(f"/api/query-history/{history_id}")
    assert after_del.status_code == 404
