# Source Code Directory

This directory contains all source code for the RAG pipeline.

- `api/`: FastAPI app, API endpoints, and middleware for authentication and logging.
- `processing/`: Document validation, chunking, and embedding logic.
- `storage/`: Vector DB (Qdrant) logic, SQLAlchemy models, and Alembic integration.
- `monitoring/`: Prometheus metrics and monitoring utilities.
- `tests/`: Unit, integration, and performance/stress tests for all major features.
- `config.py`: Pydantic-based configuration management and environment validation.

## Usage

- See each subdirectory for more details on its role.
- The main README provides a full architecture overview and API documentation. 