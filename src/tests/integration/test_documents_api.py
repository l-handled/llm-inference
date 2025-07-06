import pytest
from fastapi.testclient import TestClient
from src.api.routes import app
from src.config.settings import settings

client = TestClient(app)

def test_list_and_delete_documents(monkeypatch):
    # Use the actual API token from settings
    test_token = settings.LANGSMITH_API_KEY
    headers = {"Authorization": f"Bearer {test_token}"}
    # Ingest a document with langchain
    response = client.post(
        "/ingest",
        files={"file": ("test.txt", b"Delete test document.")},
        data={"strategy": "langchain"},
        headers=headers,
    )
    assert response.status_code == 201
    doc_id = response.json()["document_id"]
    # Ingest a document with langchain (llamaindex no longer supported)
    response2 = client.post(
        "/ingest",
        files={"file": ("test2.txt", b"Delete test document 2.")},
        data={"strategy": "langchain"},
        headers=headers,
    )
    assert response2.status_code == 201
    doc_id2 = response2.json()["document_id"]
    # List documents
    list_response = client.get("/documents", headers=headers)
    assert list_response.status_code == 200
    docs = list_response.json()["documents"]
    assert any(d["document_id"] == doc_id for d in docs)
    assert any(d["document_id"] == doc_id2 for d in docs)
    # Delete both documents
    del_response = client.delete(f"/documents/{doc_id}", headers=headers)
    assert del_response.status_code == 200
    assert del_response.json()["status"] == "deleted"
    del_response2 = client.delete(f"/documents/{doc_id2}", headers=headers)
    assert del_response2.status_code == 200
    assert del_response2.json()["status"] == "deleted" 