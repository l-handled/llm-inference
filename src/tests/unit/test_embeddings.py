from src.processing.embeddings import embed_chunks

def test_embed_chunks():
    chunks = ["Hello world", "Test chunk"]
    embeddings = embed_chunks(chunks)
    assert len(embeddings) == 2
    assert all(isinstance(vec, list) for vec in embeddings) 