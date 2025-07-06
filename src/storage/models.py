from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    doc_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 