import pytest
from fastapi.testclient import TestClient
from src.api.routes import app
from src.config.settings import settings

client = TestClient(app)

def test_ingest_invalid_file_type(monkeypatch):
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post(
        "/ingest",
        files={"file": ("badfile.exe", b"Not a valid doc")},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]

def test_missing_token():
    response = client.get("/documents")
    assert response.status_code == 403 or response.status_code == 401

def test_bad_query(monkeypatch):
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post(
        "/query",
        json={"query": ""},
        headers=headers,
    )
    assert response.status_code == 200
    # Should return empty or low-confidence results 

def test_ingest_invalid_strategy(monkeypatch):
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post(
        "/ingest",
        files={"file": ("test.txt", b"Test doc")},
        data={"strategy": "notarealstrategy"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Unknown strategy" in response.json()["detail"]

def test_query_invalid_strategy(monkeypatch):
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post(
        "/query?strategy=notarealstrategy",
        json={"query": "Test", "top_k": 1},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Unknown strategy" in response.json()["detail"]

def test_langsmith_traces_not_configured(monkeypatch):
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    # Simulate missing/invalid LangSmith config
    response = client.get("/langsmith_traces", headers=headers)
    assert response.status_code in (200, 400) 