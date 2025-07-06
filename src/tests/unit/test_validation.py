import pytest
from src.processing.validation import validate_document

def test_validate_txt():
    content = b"Hello, world!"
    assert validate_document(content, "txt") == "Hello, world!"

def test_validate_json():
    content = b'{"foo": "bar"}'
    assert validate_document(content, "json") == {"foo": "bar"}

def test_validate_pdf(monkeypatch):
    # Patch PdfReader to simulate PDF extraction
    class DummyPage:
        def extract_text(self):
            return "PDF text"
    class DummyReader:
        pages = [DummyPage()]
    monkeypatch.setattr("src.processing.validation.PdfReader", lambda x: DummyReader())
    content = b"%PDF-1.4..."
    assert validate_document(content, "pdf") == "PDF text"

def test_validate_unsupported():
    with pytest.raises(ValueError):
        validate_document(b"irrelevant", "docx") 