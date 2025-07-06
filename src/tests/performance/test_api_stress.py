import threading
import time
from fastapi.testclient import TestClient
from src.api.routes import app

client = TestClient(app)

NUM_THREADS = 10
NUM_REQUESTS_PER_THREAD = 10

def ingest_document(idx):
    response = client.post(
        "/ingest",
        files={"file": (f"stress_{idx}.txt", f"Stress test document {idx}".encode())},
        headers={"Authorization": "Bearer changeme"},
    )
    assert response.status_code == 201
    return response.json()["document_id"]

def query_document():
    response = client.post(
        "/query",
        json={"query": "Stress", "top_k": 1},
        headers={"Authorization": "Bearer changeme"},
    )
    assert response.status_code == 200

def stress_ingest():
    for i in range(NUM_REQUESTS_PER_THREAD):
        ingest_document(i)

def stress_query():
    for _ in range(NUM_REQUESTS_PER_THREAD):
        query_document()

def test_stress_ingest_and_query(monkeypatch):
    monkeypatch.setattr("src.api.routes.verify_token", lambda x: None)
    start = time.time()
    threads = []
    # Ingest stress
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=stress_ingest)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    ingest_time = time.time() - start
    print(f"Ingested {NUM_THREADS * NUM_REQUESTS_PER_THREAD} docs in {ingest_time:.2f} seconds.")
    # Query stress
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=stress_query)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    query_time = time.time() - start - ingest_time
    print(f"Queried {NUM_THREADS * NUM_REQUESTS_PER_THREAD} times in {query_time:.2f} seconds.")
    assert ingest_time < 60  # Should be reasonably fast
    assert query_time < 60 