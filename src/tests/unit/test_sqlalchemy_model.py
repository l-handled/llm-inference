import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.storage.models import Base, DocumentMetadata

def test_document_metadata_crud():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Create
    doc = DocumentMetadata(filename="test.txt", metadata="{\"foo\": \"bar\"}")
    session.add(doc)
    session.commit()
    # Query
    found = session.query(DocumentMetadata).filter_by(filename="test.txt").first()
    assert found is not None
    assert found.metadata == "{\"foo\": \"bar\"}"
    # Delete
    session.delete(found)
    session.commit()
    assert session.query(DocumentMetadata).count() == 0 