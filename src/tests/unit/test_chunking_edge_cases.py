import pytest
from src.processing.chunking import chunk_document

def test_empty_document():
    assert chunk_document("", "txt") == []

def test_very_short_document():
    assert chunk_document("abc", "txt", chunk_size=10) == ["abc"]

def test_very_long_document():
    text = "a" * 5000
    chunks = chunk_document(text, "txt", chunk_size=1000)
    assert len(chunks) == 5
    assert all(len(c) == 1000 for c in chunks[:-1])
    assert len(chunks[-1]) == 1000

def test_non_string_input():
    with pytest.raises(Exception):
        chunk_document(None, "txt") 