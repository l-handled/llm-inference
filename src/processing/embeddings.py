"""
Embeddings module for generating vector representations of text chunks using sentence-transformers.
"""
from sentence_transformers import SentenceTransformer
from typing import List

_model = None

def get_model() -> SentenceTransformer:
    """
    Load or return a cached instance of the sentence-transformers model.
    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks.
    Args:
        chunks (List[str]): List of text strings to embed.
    Returns:
        List[List[float]]: List of embedding vectors.
    """
    model = get_model()
    return model.encode(chunks, show_progress_bar=True).tolist() 