"""
Chunking module for splitting documents into smaller pieces for embedding and retrieval.
"""
from typing import List

def chunk_document(document, doc_type: str, strategy: str = "fixed", chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split a document into chunks using the specified strategy.
    Args:
        document: The document content (str or dict).
        doc_type (str): The type of document (txt, json, pdf).
        strategy (str): Chunking strategy ('fixed', 'sliding', 'semantic').
        chunk_size (int): Size of each chunk.
        overlap (int): Overlap size for sliding window.
    Returns:
        List[str]: List of text chunks.
    """
    if isinstance(document, dict):
        text = document.get("content", "")
    else:
        text = document

    if strategy == "fixed":
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    elif strategy == "sliding":
        return [text[i:i+chunk_size] for i in range(0, len(text)-chunk_size+1, chunk_size-overlap)]
    # Semantic chunking placeholder
    elif strategy == "semantic":
        # TODO: Implement semantic chunking using sentence boundaries or a model
        return [text]
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}") 