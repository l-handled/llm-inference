import pytest
from fastapi.testclient import TestClient
from src.api.routes import app
from src.config.settings import settings

client = TestClient(app)

def test_query_with_metadata_filter(monkeypatch):
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    # Ingest two documents with different metadata and unique content
    resp1 = client.post(
        "/ingest",
        files={"file": ("meta1.txt", b"UniqueMeta1TestContent")},
        data={"metadata": "{\"category\": \"A\"}"},
        headers=headers,
    )
    resp2 = client.post(
        "/ingest",
        files={"file": ("meta2.txt", b"UniqueMeta2TestContent")},
        data={"metadata": "{\"category\": \"B\"}"},
        headers=headers,
    )
    assert resp1.status_code == 201 and resp2.status_code == 201
    # Query with metadata filter and unique query
    query_response = client.post(
        "/query",
        json={"query": "UniqueMeta1TestContent", "top_k": 20, "filters": {"doc_metadata_category": "A"}},
        headers=headers,
    )
    assert query_response.status_code == 200
    results = query_response.json()["results"]
    # Should only return results from category A
    assert any("meta1.txt" in r.get("filename", "") for r in results)
    assert not any("meta2.txt" in r.get("filename", "") for r in results) 