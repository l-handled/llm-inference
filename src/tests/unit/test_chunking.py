from src.processing.chunking import chunk_document

def test_fixed_chunking():
    text = "a" * 1000
    chunks = chunk_document(text, "txt", strategy="fixed", chunk_size=100)
    assert len(chunks) == 10
    assert all(len(c) == 100 for c in chunks[:-1]) 