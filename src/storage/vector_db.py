"""
Vector DB module for storing, querying, and deleting document embeddings in Qdrant.
Implements hybrid search (vector + BM25 keyword).
"""
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
import uuid
import os
from typing import List, Tuple, Dict, Any
from rank_bm25 import BM25Okapi
from tenacity import retry, stop_after_attempt, wait_exponential
import time
from src.config.settings import settings
from urllib.parse import urlparse

# Get Qdrant connection details from environment
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION_NAME = "documents"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=90.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
def store_document(filename, embeddings, chunks, metadata=None):
    """
    Store document chunks and their embeddings in Qdrant.
    Args:
        filename (str): Name of the document file.
        embeddings (List[List[float]]): Embedding vectors.
        chunks (List[str]): Text chunks.
        metadata (str, optional): Additional metadata.
    Returns:
        str: Document ID.
    """
    doc_id = str(uuid.uuid4())
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={
                "document_id": doc_id,
                "chunk_index": i,
                "text": chunk,
                "filename": filename,
                "doc_metadata": metadata,
            },
        )
        for i, (emb, chunk) in enumerate(zip(embeddings, chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return doc_id

def query_documents(query, top_k=5, similarity_threshold=0.7, filters=None, use_hybrid=True):
    """
    Query Qdrant for similar document chunks using vector search and BM25 keyword search.
    Args:
        query (str): The search query.
        top_k (int): Number of results to return.
        similarity_threshold (float): Minimum similarity score.
        filters (dict, optional): Metadata filters.
        use_hybrid (bool): Whether to use hybrid search (vector + BM25).
    Returns:
        Tuple[List[dict], float]: List of results and query latency (ms).
    """
    try:
        start = time.time()
        search_filter = None
        if filters:
            conditions = []
            for k, v in filters.items():
                conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
            search_filter = Filter(must=conditions)
        
        # Get embeddings model
        try:
            from src.processing.embeddings import get_model
            query_vec = get_model().encode([query])[0]
        except Exception as e:
            # Fallback to simple text search if embeddings fail
            print(f"Embedding generation failed: {e}")
            return [], 0.0
        
        # Vector search
        try:
            vector_results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vec,
                limit=top_k,
                score_threshold=similarity_threshold,
                query_filter=search_filter,
                with_payload=True,
            )
        except Exception as e:
            print(f"Vector search failed: {e}")
            vector_results = []
        
        # BM25 keyword search (hybrid)
        if use_hybrid:
            try:
                # Get points for BM25 with filter if provided
                if search_filter:
                    points = client.scroll(collection_name=COLLECTION_NAME, scroll_filter=search_filter, limit=1000)[0]
                else:
                    points = client.scroll(collection_name=COLLECTION_NAME, limit=1000)[0]
                if points:
                    corpus = [p.payload.get("text", "") for p in points if p.payload.get("text")]
                    if corpus:
                        bm25 = BM25Okapi([doc.split() for doc in corpus])
                        bm25_scores = bm25.get_scores(query.split())
                        # Get top_k BM25 results
                        bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
                        bm25_results = [
                            {
                                "document_id": points[i].payload.get("document_id") or points[i].payload.get("mongo_id", ""),
                                "chunk_index": points[i].payload.get("chunk_index", 0),
                                "text": points[i].payload.get("text", ""),
                                "score": float(bm25_scores[i]),
                                "filename": points[i].payload.get("filename", ""),
                                "doc_metadata": points[i].payload.get("doc_metadata", ""),
                                "doc_metadata_category": points[i].payload.get("doc_metadata_category", ""),
                                "bm25": True
                            }
                            for i in bm25_indices if bm25_scores[i] > 0 and i < len(points)
                        ]
                    else:
                        bm25_results = []
                else:
                    bm25_results = []
            except Exception as e:
                print(f"BM25 search failed: {e}")
                bm25_results = []
            
            # Combine and deduplicate results (prefer vector score if present)
            combined = {}
            for r in vector_results:
                try:
                    doc_id = r.payload.get("document_id") or r.payload.get("mongo_id", "")
                    key = f"{doc_id}_{r.payload.get('chunk_index', 0)}"
                    combined[key] = {
                        "document_id": doc_id,
                        "chunk_index": r.payload.get("chunk_index", 0),
                        "text": r.payload.get("text", ""),
                        "score": r.score,
                        "filename": r.payload.get("filename", ""),
                        "doc_metadata": r.payload.get("doc_metadata", ""),
                        "doc_metadata_category": r.payload.get("doc_metadata_category", ""),
                        "bm25": False
                    }
                except Exception as e:
                    print(f"Error processing vector result: {e}")
                    continue
            
            for bm in bm25_results:
                try:
                    key = f"{bm['document_id']}_{bm['chunk_index']}"
                    if key not in combined:
                        combined[key] = bm
                except Exception as e:
                    print(f"Error processing BM25 result: {e}")
                    continue
            
            # Sort by score (vector first, then BM25)
            results = sorted(combined.values(), key=lambda x: x.get("score", 0), reverse=True)[:top_k]
        else:
            results = []
            for r in vector_results:
                try:
                    results.append({
                        "document_id": r.payload.get("document_id") or r.payload.get("mongo_id", ""),
                        "chunk_index": r.payload.get("chunk_index", 0),
                        "text": r.payload.get("text", ""),
                        "score": r.score,
                        "filename": r.payload.get("filename", ""),
                        "doc_metadata": r.payload.get("doc_metadata", ""),
                        "doc_metadata_category": r.payload.get("doc_metadata_category", ""),
                        "bm25": False
                    })
                except Exception as e:
                    print(f"Error processing vector result: {e}")
                    continue
        
        latency = (time.time() - start) * 1000
        return results, latency
    except Exception as e:
        print(f"Query failed with error: {e}")
        return [], 0.0

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
def list_documents():
    """
    List all unique documents stored in Qdrant.
    Returns:
        List[dict]: List of document metadata.
    """
    try:
        points = client.scroll(collection_name=COLLECTION_NAME, limit=1000)[0]
    except UnexpectedResponse as e:
        if "doesn't exist" in str(e):
            return []
        raise
    docs = {}
    for p in points:
        # Handle both old (mongo_id) and new (document_id) payload structures
        doc_id = p.payload.get("document_id") or p.payload.get("mongo_id")
        if doc_id and doc_id not in docs:
            docs[doc_id] = {
                "document_id": doc_id,
                "filename": p.payload.get("filename"),
                "doc_metadata": p.payload.get("doc_metadata"),
            }
    return list(docs.values())

def delete_document(document_id):
    """
    Delete all chunks and embeddings for a document from Qdrant.
    Args:
        document_id (str): The document ID to delete.
    """
    try:
        # Use Qdrant's Filter object instead of a raw dict
        qdrant_filter = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=qdrant_filter
        )
    except UnexpectedResponse as e:
        if "doesn't exist" in str(e):
            return
        raise 