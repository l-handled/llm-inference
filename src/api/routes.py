from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
import logging
import os

from src.processing.validation import validate_document
from src.processing.chunking import chunk_document
from src.processing.embeddings import embed_chunks
from src.storage.vector_db import (
    store_document,
    query_documents,
    list_documents,
    delete_document
)
from src.monitoring.metrics import record_metrics, prometheus_metrics
from src.config.settings import settings
from src.processing.ingest_rag import ingest_document_rag
from pymongo import MongoClient
from bson import ObjectId
from langsmith import Client as LangSmithClient

app = FastAPI(title="Production-Ready RAG LLM Inference Pipeline")

security = HTTPBearer()

# --- Auth Dependency ---
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the provided Bearer token against the configured API token.
    Raises:
        HTTPException: If the token is invalid.
    """
    if credentials.credentials != settings.LANGSMITH_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing token.")

# --- Pydantic Models ---
class IngestResponse(BaseModel):
    document_id: str
    status: str

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    similarity_threshold: float = 0.7
    filters: Optional[dict] = None
    use_hybrid: bool = True

class QueryResponse(BaseModel):
    results: List[dict]
    latency_ms: float

class DocumentListResponse(BaseModel):
    documents: List[dict]

class DeleteResponse(BaseModel):
    document_id: str
    status: str

# --- Middleware for Correlation ID ---
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """
    Middleware to add a unique correlation ID to each request for logging and tracing.
    """
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# --- Endpoints ---
import asyncio
from concurrent.futures import ThreadPoolExecutor

@app.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    chunking_strategy: Optional[str] = Form("langchain"),
    chunk_size: Optional[int] = Form(512),
    overlap: Optional[int] = Form(64),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Ingest a document, store in MongoDB, chunk/embed, upsert to Qdrant.
    Supports chunking strategies: langchain, fixed, sliding, semantic.
    """
    import time
    start_time = time.time()

    verify_token(token)
    try:
        valid_strategies = {"langchain", "fixed", "sliding", "semantic"}
        if chunking_strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"Unknown chunking strategy: {chunking_strategy}")

        doc = await file.read()
        doc_type = file.filename.split(".")[-1].lower()
        validated = validate_document(doc, doc_type)

        # Run the ingestion in a thread pool with timeout
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            mongo_id = await asyncio.wait_for(
                loop.run_in_executor(
                    executor,
                    ingest_document_rag,
                    file.filename,
                    validated,
                    metadata,
                    chunking_strategy,
                    chunk_size,
                    overlap
                ),
                timeout=300  # 5 minutes timeout
            )

        # Record successful metrics
        latency_ms = (time.time() - start_time) * 1000
        record_metrics("request_count", 1, endpoint="ingest", status="success")
        record_metrics("query_latency_ms", latency_ms, endpoint="ingest")

        return IngestResponse(document_id=mongo_id, status="success")
    except asyncio.TimeoutError:
        # Record timeout metrics
        record_metrics("error_count", 1, endpoint="ingest")
        logging.error("Ingest timed out after 5 minutes")
        raise HTTPException(status_code=408, detail="Ingest timed out after 5 minutes")
    except Exception as e:
        # Record error metrics
        record_metrics("error_count", 1, endpoint="ingest")
        logging.exception("Ingest failed")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/documents", response_model=DocumentListResponse)
async def get_documents(token: HTTPAuthorizationCredentials = Depends(security)):
    """
    List all processed documents from MongoDB.
    """
    import time
    start_time = time.time()

    verify_token(token)
    try:
        docs = list(mongo_coll.find({}, {"_id": 1, "filename": 1, "doc_metadata": 1, "upload_time": 1, "chunking_strategy": 1, "chunk_size": 1, "overlap": 1}))
        for d in docs:
            d["document_id"] = str(d.pop("_id"))
            # Convert None to empty string for doc_metadata
            if d.get("doc_metadata") is None:
                d["doc_metadata"] = ""
            # Ensure chunking info is present
            d["chunking_strategy"] = d.get("chunking_strategy", "unknown")
            d["chunk_size"] = d.get("chunk_size", None)
            d["overlap"] = d.get("overlap", None)

        # Record successful metrics
        latency_ms = (time.time() - start_time) * 1000
        record_metrics("request_count", 1, endpoint="documents", status="success")
        record_metrics("query_latency_ms", latency_ms, endpoint="documents")

        return DocumentListResponse(documents=docs)
    except Exception as e:
        # Record error metrics
        record_metrics("error_count", 1, endpoint="documents")
        logging.exception("List documents failed")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_doc(document_id: str, token: HTTPAuthorizationCredentials = Depends(security)):
    """
    Delete a document from MongoDB and its embeddings from Qdrant.
    """
    verify_token(token)
    try:
        mongo_coll.delete_one({"_id": ObjectId(document_id)})
        delete_document(document_id)
        return DeleteResponse(document_id=document_id, status="deleted")
    except Exception as e:
        logging.exception("Delete failed")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    strategy: Optional[str] = None,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Query the vector DB for relevant chunks using hybrid search.
    Returns top-k results and query latency.
    """
    import time
    start_time = time.time()

    verify_token(token)
    try:
        # Validate strategy if provided
        if strategy and strategy != "langchain":
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")

        from src.storage.vector_db import query_documents

        # Use the existing query_documents function with hybrid search
        results, latency = query_documents(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            filters=request.filters,
            use_hybrid=request.use_hybrid
        )

        # Format results for the response
        out = []
        for result in results:
            out.append({
                "document_id": result["document_id"],
                "text": result["text"],
                "score": result["score"],
                "filename": result.get("filename", ""),
                "bm25": result.get("bm25", False),
            })

        # Record successful metrics
        record_metrics("request_count", 1, endpoint="query", status="success")
        record_metrics("query_latency_ms", latency, endpoint="query")

        return QueryResponse(results=out, latency_ms=latency)
    except Exception as e:
        # Record error metrics
        record_metrics("error_count", 1, endpoint="query")
        logging.exception("Query failed")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/langsmith_traces")
async def langsmith_traces(token: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fetch recent LangSmith traces for UI display.
    """
    verify_token(token)
    try:
        client = LangSmithClient(api_key=settings.LANGSMITH_API_KEY)
        # List recent runs with proper parameters
        traces = client.list_runs(
            limit=20,
            execution_order=1,  # Only root runs
            error=False,  # Only successful runs
        )
        return {"traces": [t.dict() for t in traces]}
    except Exception as e:
        logging.exception("LangSmith traces failed")
        # Return empty traces instead of error if LangSmith is not properly configured
        return {"traces": [], "error": "LangSmith not properly configured or no traces available"}

@app.get("/healthz")
async def health_check():
    """
    Comprehensive health check endpoint.
    """
    import datetime
    import os

    health_status = {
        "status": "ok",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime": "running",
        "dependencies": {},
        "system": {}
    }

    # Check MongoDB connection
    try:
        mongo_client.admin.command('ping')
        health_status["dependencies"]["mongodb"] = {
            "status": "healthy",
            "response_time": "~5ms"
        }
    except Exception as e:
        health_status["dependencies"]["mongodb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check Qdrant connection
    try:
        from qdrant_client import QdrantClient
        QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
        QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=90.0)
        collections = qdrant_client.get_collections()
        health_status["dependencies"]["qdrant"] = {
            "status": "healthy",
            "collections": len(collections.collections)
        }
    except Exception as e:
        health_status["dependencies"]["qdrant"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check LangSmith connection
    try:
        if settings.LANGSMITH_API_KEY:
            client = LangSmithClient(api_key=settings.LANGSMITH_API_KEY)
            client.list_runs(limit=1)
            health_status["dependencies"]["langsmith"] = {
                "status": "healthy",
                "configured": True
            }
        else:
            health_status["dependencies"]["langsmith"] = {
                "status": "not_configured",
                "configured": False
            }
    except Exception as e:
        health_status["dependencies"]["langsmith"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # System metrics (basic version without psutil for now)
    health_status["system"] = {
        "note": "Basic health check - system metrics require psutil package",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    return health_status

@app.get("/documents/{document_id}/embeddings")
async def get_document_embeddings(document_id: str, token: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get vector embeddings for a specific document from Qdrant.
    """
    logging.info(f"DEBUG: Function called with document_id: {document_id}")
    verify_token(token)
    logging.info(f"DEBUG: Token verified for document_id: {document_id}")
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
        QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=90.0)

        # Create filter to get all chunks for this document
        qdrant_filter = Filter(must=[FieldCondition(key="mongo_id", match=MatchValue(value=document_id))])

        # Debug logging
        logging.info(f"Searching for document_id: {document_id}")
        logging.info(f"Using filter: {qdrant_filter}")

        # Get all points for this document
        try:
            scroll_result = qdrant_client.scroll(
                collection_name="documents",
                scroll_filter=qdrant_filter,
                limit=1000,
                with_payload=True,
                with_vectors=True
            )
            points = scroll_result[0]
            logging.info(f"DEBUG: Scroll result length: {len(points)}")
            logging.info(f"Found {len(points)} points for document {document_id}")
        except Exception as e:
            logging.error(f"Qdrant scroll failed: {e}")
            raise HTTPException(status_code=500, detail=f"Qdrant query failed: {str(e)}")

        if not points:
            raise HTTPException(status_code=404, detail="Document not found or no embeddings available")

        # Format the response
        embeddings_data = []
        for i, point in enumerate(points):
            embedding_data = {
                "chunk_index": point.payload.get("chunk_index", i),
                "text": point.payload.get("text", ""),
                "vector_dimensions": len(point.vector) if point.vector else 0,
                "vector_preview": point.vector[:10] if point.vector else [],  # First 10 dimensions
                "score": None,  # Will be calculated if needed
                "metadata": {
                    "filename": point.payload.get("filename", ""),
                    "doc_metadata": point.payload.get("doc_metadata", "")
                }
            }
            embeddings_data.append(embedding_data)

        return {
            "document_id": document_id,
            "total_chunks": len(embeddings_data),
            "embedding_dimensions": len(points[0].vector) if points and points[0].vector else 0,
            "chunks": embeddings_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Failed to get document embeddings")
        raise HTTPException(status_code=500, detail=f"Failed to get embeddings: {str(e)}")

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint for monitoring.
    """
    return prometheus_metrics()

# MongoDB client for document CRUD endpoints
MONGODB_URI = settings.MONGODB_URI
MONGO_DB = "rag_db"
MONGO_COLL = "documents"
mongo_client = MongoClient(MONGODB_URI)
mongo_coll = mongo_client[MONGO_DB][MONGO_COLL] 