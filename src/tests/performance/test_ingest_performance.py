import time
from src.processing.chunking import chunk_document
from src.processing.embeddings import embed_chunks

def test_ingest_performance():
    text = "This is a test. " * 10000  # Large document
    start = time.time()
    chunks = chunk_document(text, "txt", chunk_size=256)
    embeddings = embed_chunks(chunks)
    elapsed = time.time() - start
    print(f"Ingested and embedded {len(chunks)} chunks in {elapsed:.2f} seconds.")
    assert elapsed < 30  # Should be reasonably fast 