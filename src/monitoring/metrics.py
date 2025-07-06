from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter("request_count", "Total API requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("request_latency_seconds", "API request latency", ["endpoint"])
ERROR_COUNT = Counter("error_count", "Total API errors", ["endpoint"])
CHUNK_SIZE = Gauge("average_chunk_size", "Average chunk size in characters")
EMBEDDING_TIME = Histogram("embedding_time_seconds", "Embedding generation time")
QDRANT_LATENCY = Histogram("qdrant_latency_seconds", "Qdrant operation latency", ["operation"])

# For updating chunk size metric
_chunk_size_sum = 0
_chunk_count = 0

def record_metrics(metric_name, value, endpoint=None, status=None, operation=None):
    if metric_name == "query_latency_ms":
        REQUEST_LATENCY.labels(endpoint=endpoint or "query").observe(value / 1000.0)
    elif metric_name == "request_count":
        REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()
    elif metric_name == "error_count":
        ERROR_COUNT.labels(endpoint=endpoint).inc()
    elif metric_name == "chunk_size":
        global _chunk_size_sum, _chunk_count
        _chunk_size_sum += value
        _chunk_count += 1
        CHUNK_SIZE.set(_chunk_size_sum / _chunk_count)
    elif metric_name == "embedding_time":
        EMBEDDING_TIME.observe(value)
    elif metric_name == "qdrant_latency":
        QDRANT_LATENCY.labels(operation=operation).observe(value)


def prometheus_metrics():
    return Response(generate_latest(), media_type="text/plain") 