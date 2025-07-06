# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-core.txt requirements-ai.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-core.txt -r requirements-ai.txt && \
    pip uninstall -y llama-index && \
    pip install --no-cache-dir "llama-index>=0.10.0"

# Runtime stage
FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

EXPOSE 8000

# Run batch ingestion before starting the API
CMD ["/bin/sh", "-c", "PYTHONPATH=/app python3 src/processing/batch_ingest_sample_data.py && uvicorn src.api.routes:app --host 0.0.0.0 --port 8000"]