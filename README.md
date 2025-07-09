# Production-Ready RAG LLM Inference Pipeline with some additonal Set-up

This project implements a production-grade Retrieval-Augmented Generation (RAG) system with document ingestion, vector search, hybrid retrieval, monitoring, and cloud deployment support.
Note: CI / CD requires additional work and cloud infrastructure code set up required. 

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- (Optional) Python 3.10+ and pip if you want to run components outside Docker

## Features

- Ingest PDF, TXT, JSON documents
- Configurable chunking (fixed, sliding, semantic)
- Local HuggingFace embeddings
- Qdrant vector DB with hybrid search and metadata filtering
- FastAPI async API with token auth, validation, and error handling
- Prometheus monitoring, structured logging, health checks
- Dockerized, cloud-ready (AWS ECS/EC2)
- Alembic migrations for metadata
- >80% test coverage
- **MongoDB for document storage/metadata, Qdrant for embeddings and search**
- **LangChain for chunking/indexing in both ingest and query**
- **LangSmith tracing and evaluation for all LLM/RAG requests**
- **/langsmith_traces endpoint and UI tab for experiment tracking**

# Environment Setu

The `.env` file for environment variables must be placed in the `docker/` directory. When running `run_local.sh` from the project root, if `docker/.env` does not exist, it will be created from the project root `.env.template` file. You must fill in your secrets in `docker/.env` before running the pipeline.

```
Running the below command will create .env file from template but the tokens need to be supplied. And the command will need to be re-run. 
Under docker/.env - fill in LANGSMITH_API_KEY and API_TOKEN (they both can be same as the langsmith api key)
```

local log checks: docker compose -f docker/docker-compose.yml logs api -f
docker compose -f docker/docker-compose.yml build api

## Quick Start
1. Run `./run_local.sh` from the project root.
2. If `docker/.env` is missing, it will be created from `.env.template` and you will be prompted to fill it in.
3. Edit `docker/.env` with your actual secrets and configuration values.
4. Re-run `./run_local.sh` to start the pipeline. 

## Directory Guide

- [alembic/](alembic/README.md): Database migrations and schema management
- [deployment/](deployment/README.md): Deployment scripts and cloud configs
- [docker/](docker/README.md): Dockerfiles and Compose for local dev (includes MongoDB, Qdrant, Prometheus, UI)
- [sample_data/](sample_data/README.md): Example files for ingestion/testing
- [src/](src/README.md): All source code and tests
- [ui/](ui/README.md): Streamlit web UI for interacting with the pipeline

Each directory contains a README with details on its files and usage. See below for a summary:

- **alembic/**: Alembic migration scripts and config for managing relational DB schema.
- **deployment/**: Scripts for local/cloud deployment, AWS configs, and secrets templates.
- **docker/**: Dockerfile for the API, docker-compose for local orchestration.
- **sample_data/**: Example TXT, JSON, and PDF files for ingestion and testing.
- **src/**: All Python source code, including API, processing, storage, monitoring, and tests.
- **ui/**: Streamlit-based web UI for document upload, querying, document management, and metrics visualization.

## Stack Overview

- **LangChain**: Orchestrates the RAG pipeline, including chunking, embedding, and retrieval.
- **MongoDB**: Stores all original documents and their metadata. Used for listing, deleting, and managing documents in the UI and API.
- **Qdrant**: Stores all embeddings and chunk vectors for semantic/hybrid search.
- **Prometheus**: Collects and exposes metrics from the API for monitoring and visualization in the UI.

## Experimentation

- All LLM and RAG requests are traced and evaluated with LangSmith for easy debugging and benchmarking.
- Prometheus metrics and LangSmith traces are available in the UI for monitoring and evaluation.

## LangSmith Integration

- The pipeline uses LangSmith for tracing, logging, and evaluating all LLM and RAG requests.
- Set your LangSmith API key via the `LANGSMITH_API_KEY` environment variable (see `docker-compose.yml`).
- Tracing is enabled with `LANGCHAIN_TRACING_V2=true`.
- You can change the key for local or cloud deployments as needed.

---

## Architecture Diagram

```mermaid
graph TD
    A[User/API Client] -->|POST /ingest| B[FastAPI App]
    A -->|POST /query| B
    B -->|Document Validation & Chunking| C[Processing]
    C -->|Embeddings| D[Sentence Transformers]
    D -->|Vectors| E[Qdrant Vector DB]
    B -->|Hybrid Search| E
    E -->|Results| B
    B -->|RAG Generation| F[LLM/Prompt]
    F -->|Response| A
    B -->|Metrics| G[Prometheus]
    B -->|Logs| H[Structured Logging]
    B -->|Health| I[Health Checks]
```

---

## Architecture Decisions

> **Note:**
> The provided cloud deployment template is intended as a reference and is not been fully functional for cloud deployment. Deploying to the cloud will require additional infrastructure setup, including:
> - Ingress configuration / https / certificates
> - VPC and networking
> - Load balancer
> - Connections to external data stores such as MongoDB and Qdrant / Persistent data store volumes
>
> - But.......running just     ./run_local.sh will be enough to get a taste of end to end LLM inference  

- **FastAPI**: Chosen for async, type-safe, production-ready Python APIs.
- **Qdrant**: Open-source, high-performance vector DB with hybrid search and easy local/cloud deployment.
- **Sentence Transformers**: Local embedding for cost and privacy; can swap for OpenAI API if needed.
- **Docker Compose**: Local orchestration of API, Qdrant, and Prometheus for dev/prod parity.
- **Prometheus**: Industry-standard monitoring and metrics.
- **GitHub Actions**: CI/CD for build, test, and deploy on merge to main.
- **AWS ECS/ECR**: Cloud deployment for scalability and managed infrastructure.
- **Pydantic**: For request/response validation and config management.
- **Alembic/SQLAlchemy**: For relational metadata and migrations if needed.
- **Managed AWS Kubernetes (EKS) was not selected**: While EKS is powerful, it was not chosen due to the additional networking and operational complexity required to set up and manage Kubernetes clusters, VPCs, and service networking. ECS provides a simpler, production-ready managed container orchestration solution for this use case.
- **LangChain**: Used for orchestrating the RAG pipeline, including document ingestion, chunking, embedding, and retrieval. Makes it easy to swap chunking, retrieval, and LLMs.
- **LangSmith**: Used for tracing, logging, and evaluating all LLM and RAG requests. Provides a dashboard for debugging, benchmarking, and improving the pipeline.
- **MongoDB**: Used for storing original documents and their metadata (filename, upload time, etc). Enables robust document management, listing, and metadata queries. Qdrant remains the vector DB for embeddings and semantic search.

---

## API Documentation

### Endpoints

- `POST /ingest` - Upload and process documents with LangChain
- `POST /query` - Semantic search with RAG generation using LangChain
- `GET /documents` - List processed documents with metadata (from MongoDB)
- `DELETE /documents/{id}` - Remove documents and embeddings
- `GET /langsmith_traces` - List recent LangSmith traces for observability
- `GET /healthz` - Health check

### Example: Ingest Document

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Authorization: Bearer changeme" \
  -F "file=@sample_data/sample.txt" \
  -F "doc_metadata={\"author\": \"John Doe\", \"category\": \"research\"}"
```

### Example: Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 3}'
```

### Example: List Documents

```bash
curl -X GET "http://localhost:8000/documents" -H "Authorization: Bearer changeme"
```

### Example: Delete Document

```bash
curl -X DELETE "http://localhost:8000/documents/{document_id}" -H "Authorization: Bearer changeme"
```

### Example: LangSmith Traces

```bash
curl -X GET "http://localhost:8000/langsmith_traces" -H "Authorization: Bearer changeme"
```

---

## Document Upload Pipeline: MongoDB, LangChain, Qdrant, LangSmith Integration

### Overview
The document upload pipeline implements a sophisticated RAG system that combines multiple technologies for robust document processing, storage, and retrieval:

### 1. Document Upload & Validation
- **Supported Formats**: PDF, TXT, JSON files
- **Validation**: File type checking, content parsing, and error handling
- **Processing**: Automatic text extraction from PDFs, JSON parsing, and UTF-8 encoding

### 2. MongoDB Document Storage
- **Purpose**: Stores original documents and metadata for document management
- **Schema**: 
  - `filename`: Original file name
  - `doc_metadata`: Optional JSON metadata from user
  - `upload_time`: UTC timestamp of upload
  - `size`: Document size in bytes
- **Benefits**: 
  - Document listing and management via UI/API
  - Metadata filtering and search
  - Document deletion with cascade to vector DB
  - Audit trail and versioning support

### 3. Chunking & Embedding with LangChain
- **Chunking**: `RecursiveCharacterTextSplitter` with configurable chunk size (512) and overlap (64)
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2` model for local processing
- **Vector Storage**: Direct Qdrant upsert with chunk metadata
- **Benefits**: Production-ready, well-tested, and highly configurable

### 4. Qdrant Vector Database
- **Purpose**: Stores document embeddings and enables semantic search
- **Features**:
  - Hybrid search (vector similarity + BM25 keyword search)
  - Metadata filtering by filename, document ID, chunk index
  - Cosine distance similarity for semantic matching
  - Automatic collection creation and management
- **Schema**: Each chunk stored as a point with:
  - `vector`: 384-dimensional embedding
  - `payload`: Metadata including MongoDB ID, filename, chunk index

### 5. LangChain Integration
- **Orchestration**: Manages the complete RAG pipeline
- **Components**: Text splitting, embedding generation, vector storage
- **Flexibility**: Easy swapping of chunking strategies, embedding models, and vector stores
- **Benefits**: Production-ready, well-tested, extensive ecosystem

### 6. LangSmith Tracing & Evaluation
- **Tracing**: All LLM and RAG requests are automatically traced
- **Evaluation**: Performance metrics and quality assessment
- **Observability**: Debug pipeline issues, benchmark performance, improve results
- **Integration**: 
  - `@traceable` decorators on key functions
  - Automatic trace collection and storage
  - `/langsmith_traces` endpoint for trace retrieval
  - UI integration for trace visualization

### 7. Prometheus Metrics Tracking
- **Request Metrics**: Count, latency, and error rates by endpoint
- **Processing Metrics**: Chunk size, embedding generation time
- **Database Metrics**: Qdrant operation latency
- **Real-time Monitoring**: Available via `/metrics` endpoint and UI dashboard
- **Key Metrics**:
  - `request_count`: Total API requests by endpoint and status
  - `request_latency_seconds`: API response times
  - `error_count`: Error tracking by endpoint
  - `average_chunk_size`: Average document chunk size
  - `embedding_time_seconds`: Time to generate embeddings
  - `qdrant_latency_seconds`: Vector database operation times

### Pipeline Flow Diagram
```mermaid
graph TD
    A[Document Upload] --> B[Validation & Parsing]
    B --> C[Store in MongoDB]
    C --> D{Strategy Selection}
    D -->|LangChain| E[LangChain Chunking]
    E --> G[Generate Embeddings]
    G --> H[Store in Qdrant]
    H --> I[LangSmith Tracing]
    I --> J[Prometheus Metrics]
    J --> K[Return Document ID]
```

---

## Testing Documentation

### Test Structure Overview
The project includes comprehensive testing across three categories:

### Unit Tests (`src/tests/unit/`)
- **`test_validation.py`**: Tests document validation and parsing
  - Text file parsing and encoding
  - JSON file validation and structure
  - PDF text extraction (mocked)
  - Unsupported file type rejection
- **`test_chunking.py`**: Tests text chunking functionality
  - Fixed-size chunking
  - Overlap handling
  - Edge cases with small/large documents
- **`test_chunking_edge_cases.py`**: Tests chunking boundary conditions
  - Empty documents
  - Single character documents
  - Very large documents
  - Special characters and encoding
- **`test_embeddings.py`**: Tests embedding generation
  - HuggingFace model loading
  - Vector generation consistency
  - Batch processing
- **`test_sqlalchemy_model.py`**: Tests database models
  - Document metadata model validation
  - Field constraints and defaults
  - Database schema compliance

### Integration Tests (`src/tests/integration/`)
- **`test_ingest_query.py`**: End-to-end ingest and query workflow
  - Document ingestion with LangChain
  - Query processing and response validation
  - MongoDB document listing and verification
  - LangSmith traces endpoint testing
- **`test_documents_api.py`**: Document management API testing
  - Document listing from MongoDB
  - Document deletion with cascade to Qdrant
  - API response format validation
  - Error handling for missing documents
- **`test_error_handling.py`**: Error scenario testing
  - Invalid file types and formats
  - Authentication failures
  - Database connection errors
  - Malformed requests
- **`test_metadata_filtering.py`**: Metadata and filtering tests
  - JSON metadata parsing and storage
  - Qdrant metadata filtering
  - Search result relevance with metadata

### Performance Tests (`src/tests/performance/`)
- **`test_api_stress.py`**: Load testing and stress testing
  - Concurrent document ingestion (10 threads × 10 requests)
  - Concurrent query processing
  - Performance benchmarks and timing validation
  - Resource usage monitoring
- **`test_ingest_performance.py`**: Ingestion performance testing
  - Large document processing (10,000+ words)
  - Chunking and embedding generation time
  - Memory usage optimization
  - Performance regression detection

### Test Coverage
- **Unit Tests**: >80% code coverage for core functions
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Load testing and benchmarking
- **Error Handling**: Comprehensive error scenario coverage

### Running Tests
```bash
# Run all tests
pytest src/tests/

# Run specific test categories
pytest src/tests/unit/
pytest src/tests/integration/
pytest src/tests/performance/

# Run with coverage
pytest --cov=src src/tests/

# Run specific test file
pytest src/tests/unit/test_validation.py
```

---

## Performance Benchmarks (Template)

| Operation                | Test Data         | Time (ms) | CPU (%) | Memory (MB) |
|--------------------------|-------------------|-----------|---------|-------------|
| Ingest 1MB PDF           | sample.pdf        |           |         |             |
| Ingest 10KB TXT          | sample.txt        |           |         |             |
| Query (top_k=3)          | "What is RAG?"   |           |         |             |
| Batch Ingest (3 files)   | sample*.txt/json |           |         |             |

*Fill in after running locally or in the cloud. Use `docker stats` or Prometheus for resource usage.*

---

## Deployment Guide: Step-by-Step AWS ECS/ECR

### 1. Prerequisites
- AWS account with ECS/ECR permissions
- AWS CLI configured locally (with your profile)
- Docker installed

### 2. Build and Push Docker Image

```bash
./deployment/deploy_aws.sh
```
- This builds, tags, and pushes your image to ECR using your local AWS profile.

### 3. Set Up AWS ECS
- Create an ECS cluster (Fargate or EC2)
- Create a new Task Definition:
  - Add container for API: use your ECR image
  - Add container for Qdrant: use `qdrant/qdrant:latest`
  - Set environment variables (API_TOKEN, QDRANT_HOST, QDRANT_PORT)
- Create a Service from the Task Definition
- Expose ports 8000 (API) and 6333 (Qdrant) as needed

### 4. Set Up Secrets
- Use AWS Secrets Manager for API tokens and sensitive config
- Reference secrets in your ECS Task Definition

### 5. Monitor and Test
- Use ECS console to monitor logs and health
- Test your API using the public endpoint

### 6. CI/CD
- On merge to `main`, GitHub Actions will build, test, and deploy automatically
- See `.github/workflows/deploy.yml`

---

## Testing

```bash
pytest --cov=src
```

---

## Project Structure

See the repository tree for details. All code is in `src/`.

## Setup, API, and deployment instructions will be added as the implementation progresses.

---

## Database Migrations (Alembic & SQLAlchemy)

This project uses Alembic and SQLAlchemy for relational metadata (e.g., document metadata).

### When is this required?
- **Local development:**
  - If you want to use the relational metadata features (e.g., storing document metadata in SQLite/Postgres), you must run the migrations locally.
  - If you only use Qdrant and do not use the relational DB, you can skip this step.
- **AWS/cloud deployment:**
  - If you deploy with a relational DB (e.g., RDS Postgres, Aurora, etc.), you must run the migrations in your cloud environment before starting the app.
  - If you only use Qdrant, you can skip this step.

### How to set up and run migrations

1. **Install Alembic (if not already):**
   ```bash
   pip install alembic
   ```
2. **Configure your database URL:**
   - By default, `alembic.ini` uses SQLite (`sqlite:///./db.sqlite3`).
   - For Postgres, set: `sqlalchemy.url = postgresql://user:password@host:port/dbname`
3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```
   - This will create the `document_metadata` table in your database.
4. **(Optional) Create new migrations after model changes:**
   ```bash
   alembic revision --autogenerate -m "describe your change"
   alembic upgrade head
   ```

---

## Web UI (21.co Streamlit App)

A modern, user-friendly web UI is provided in the `ui/` directory for interacting with the RAG pipeline.

**Features:**
- 21.co branding and clean design
- Upload and ingest documents (PDF, TXT, JSON)
- Query the RAG system (vector, hybrid, filters)
- List and delete processed documents
- View Prometheus metrics and charts (request count, error rate, latency)

**How to run:**

- **With Docker Compose (recommended):**
  - The UI is started automatically at [http://localhost:8501](http://localhost:8501)
- **Standalone:**
  ```bash
  cd ui
  pip install -r requirements.txt
  streamlit run app.py
  ```
  - Set `API_URL` and `API_TOKEN` in `.streamlit/secrets.toml` or edit in `app.py`.
- **With Docker:**
  ```bash
  cd ui
  docker build -t rag-ui .
  docker run -p 8501:8501 --env API_URL=http://host.docker.internal:8000 --env API_TOKEN=changeme rag-ui
  ```

See [ui/README.md](ui/README.md) for more details and customization options.

