"""
Validation module for document type checking and parsing.
"""
import json
import io
from PyPDF2 import PdfReader

def validate_document(doc_bytes: bytes, doc_type: str):
    """
    Validate and parse a document based on its type.
    Args:
        doc_bytes (bytes): The raw document bytes.
        doc_type (str): The type of document (txt, json, pdf).
    Returns:
        str or dict: Parsed document content.
    Raises:
        ValueError: If the document type is unsupported.
    """
    if doc_type == "txt":
        return doc_bytes.decode("utf-8")
    elif doc_type == "json":
        return json.loads(doc_bytes.decode("utf-8"))
    elif doc_type == "pdf":
        reader = PdfReader(io.BytesIO(doc_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    else:
        raise ValueError(f"Unsupported document type: {doc_type}") 