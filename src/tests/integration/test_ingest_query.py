import pytest
from fastapi.testclient import TestClient
from src.api.routes import app
from src.config.settings import settings

client = TestClient(app)

def test_ingest_and_query(monkeypatch):
    # Use the actual API token from settings
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    # Ingest a document
    response = client.post(
        "/ingest",
        files={"file": ("test.txt", b"Integration test document.")},
        data={},
        headers=headers,
    )
    assert response.status_code == 201
    doc_id = response.json()["document_id"]
    
    # Query the document
    query_response = client.post(
        "/query",
        json={"query": "Integration", "top_k": 1},
        headers=headers,
    )
    assert query_response.status_code == 200
    assert "results" in query_response.json()
    
    # List documents (MongoDB)
    list_response = client.get("/documents", headers=headers)
    assert list_response.status_code == 200
    docs = list_response.json()["documents"]
    assert any(d["document_id"] == doc_id for d in docs)
    
    # LangSmith traces endpoint
    traces_response = client.get("/langsmith_traces", headers=headers)
    assert traces_response.status_code in (200, 400)  # 400 if LangSmith not configured 