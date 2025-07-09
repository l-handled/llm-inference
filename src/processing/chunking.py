"""
Chunking module for splitting documents into smaller pieces for embedding and retrieval.
"""
from typing import List
import nltk
from nltk.tokenize import sent_tokenize

# Ensure punkt is downloaded (safe to call repeatedly)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

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
        if len(text) <= chunk_size:
            return [text]
        return [text[i:i+chunk_size] for i in range(0, len(text)-chunk_size+1, chunk_size-overlap)]
    elif strategy == "semantic":
        # Use sentence tokenization, then group sentences into chunks
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        for sent in sentences:
            if len(current_chunk) + len(sent) + 1 <= chunk_size:
                current_chunk += (" " if current_chunk else "") + sent
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent
        if current_chunk:
            chunks.append(current_chunk)
        return chunks
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}") 