import os
import json
import logging
import time
from pymongo import MongoClient
from bson import ObjectId
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langsmith import traceable  # Added import
import datetime
from src.config.settings import settings
from urllib.parse import urlparse
from src.monitoring.metrics import record_metrics
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB client for document storage
MONGODB_URI = settings.MONGODB_URI
MONGO_DB = "rag_db"
MONGO_COLL = "documents"
mongo_client = MongoClient(MONGODB_URI)
mongo_coll = mongo_client[MONGO_DB][MONGO_COLL]

# Qdrant client for vector storage
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = "documents"
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=90.0)

@traceable(name="ingest_document_rag")
def ingest_document_rag(filename, doc_content, doc_metadata, strategy="langchain"):
    """
    Store document in MongoDB, chunk/embed, upsert to Qdrant. Returns mongo_id.
    Currently only supports LangChain strategy.
    
    Args:
        filename: Name of the file being ingested
        doc_content: Content of the document
        doc_metadata: Metadata for the document
        strategy: Processing strategy - currently only "langchain" is supported
    """
    logger.info(f"Starting ingestion for {filename} with strategy: {strategy}")
    
    # Currently only LangChain strategy is supported
    if strategy != "langchain":
        logger.warning(f"Strategy '{strategy}' is not supported. Using LangChain instead.")
        strategy = "langchain"
    
    # Store in MongoDB
    doc = {
        "filename": filename,
        "doc_metadata": doc_metadata,
        "upload_time": datetime.datetime.utcnow(),
        "size": len(str(doc_content)),
    }
    try:
        mongo_id = mongo_coll.insert_one(doc).inserted_id
    except Exception as e:
        logger.error(f"Failed to store document in MongoDB: {str(e)}")
        raise RuntimeError(f"Failed to store document in MongoDB: {str(e)}")

    # Chunking and Embedding with LangChain
    logger.info(f"Processing with LangChain")
    # Handle both string and dict content
    if isinstance(doc_content, dict):
        text = json.dumps(doc_content)
    else:
        text = str(doc_content)
    
    logger.info(f"Text length: {len(text)} characters")
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    chunks = splitter.split_text(text)
    logger.info(f"Created {len(chunks)} chunks")
    
    # Record chunk size metrics
    for chunk in chunks:
        record_metrics("chunk_size", len(chunk))
    
    logger.info("Loading HuggingFace embeddings model...")
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info("Generating embeddings...")
    embedding_start = time.time()
    embeddings = embedder.embed_documents(chunks)
    embedding_time = time.time() - embedding_start
    record_metrics("embedding_time", embedding_time)
    logger.info(f"Generated {len(embeddings)} embeddings in {embedding_time:.2f}s")
    
    # Upsert to Qdrant
    qdrant = qdrant_client
    points = []
    doc_metadata_dict = json.loads(doc_metadata) if isinstance(doc_metadata, str) else doc_metadata
    for i, (emb, chunk) in enumerate(zip(embeddings, chunks)):
        payload = {
            "mongo_id": str(mongo_id),
            "filename": filename,
            "chunk_index": i,
            "text": chunk,  # Add text content for BM25 search
            "doc_metadata": doc_metadata_dict,
        }
        # Flatten category for filtering
        if doc_metadata_dict and isinstance(doc_metadata_dict, dict) and "category" in doc_metadata_dict:
            payload["doc_metadata_category"] = doc_metadata_dict["category"]
        points.append(PointStruct(id=str(uuid.uuid4()), vector=emb, payload=payload))
    logger.info(f"Prepared {len(points)} points for Qdrant")
    try:
        qdrant_start = time.time()
        qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
        qdrant_time = time.time() - qdrant_start
        record_metrics("qdrant_latency", qdrant_time, operation="upsert")
        logger.info(f"Successfully upserted to Qdrant in {qdrant_time:.2f}s")
    except Exception as e:
        if not qdrant_client.collection_exists(collection_name=QDRANT_COLLECTION):
            logger.info(f"Creating Qdrant collection {QDRANT_COLLECTION}")
            qdrant_client.recreate_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
            )
            qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
            logger.info("Successfully created collection and upserted to Qdrant")
        else:
            logger.error(f"Failed to upsert to Qdrant: {str(e)}")
            raise RuntimeError(f"Failed to upsert to Qdrant: {str(e)}")

    logger.info(f"Successfully ingested document {filename} with mongo_id {mongo_id}")
    return str(mongo_id)