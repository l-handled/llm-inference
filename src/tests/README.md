# Testing Documentation

This directory contains comprehensive tests for the RAG LLM Inference Pipeline, organized into three categories: unit tests, integration tests, and performance tests.

## Test Structure

```
src/tests/
├── unit/                    # Unit tests for individual components
├── integration/             # End-to-end workflow tests
├── performance/             # Load and stress testing
└── README.md               # This file
```

## Unit Tests (`unit/`)

Unit tests focus on testing individual functions and components in isolation.

### `test_validation.py`
Tests the document validation and parsing functionality:
- **`test_validate_txt()`**: Verifies text file parsing and UTF-8 encoding
- **`test_validate_json()`**: Tests JSON file validation and structure parsing
- **`test_validate_pdf()`**: Tests PDF text extraction (with mocked PdfReader)
- **`test_validate_unsupported()`**: Ensures unsupported file types are properly rejected

### `test_chunking.py`
Tests the text chunking functionality:
- **`test_chunk_document()`**: Verifies basic chunking with configurable chunk size
- **Tests chunk overlap handling**: Ensures proper text continuity between chunks
- **Tests edge cases**: Handles small documents and boundary conditions

### `test_chunking_edge_cases.py`
Tests boundary conditions and edge cases in chunking:
- **Empty document handling**: Tests behavior with zero-length content
- **Single character documents**: Verifies chunking with minimal content
- **Large document processing**: Tests performance with very large texts
- **Special characters**: Ensures proper handling of Unicode and special characters
- **Encoding edge cases**: Tests various text encodings and formats

### `test_embeddings.py`
Tests embedding generation functionality:
- **Model loading**: Verifies HuggingFace model initialization
- **Vector generation**: Tests consistency of embedding vectors
- **Batch processing**: Tests embedding multiple chunks efficiently
- **Vector dimensions**: Ensures correct embedding dimensions (384 for all-MiniLM-L6-v2)

### `test_sqlalchemy_model.py`
Tests database model definitions:
- **Model validation**: Tests DocumentMetadata model field constraints
- **Default values**: Verifies automatic timestamp and UUID generation
- **Schema compliance**: Ensures database schema matches model definitions
- **Field types**: Tests proper data type handling for all fields

## Integration Tests (`integration/`)

Integration tests verify that multiple components work together correctly in end-to-end workflows.

### `test_ingest_query.py`
Tests the complete document ingestion and query workflow:
- **Document ingestion with LangChain**: Tests full pipeline using LangChain strategy
- **Document ingestion with LlamaIndex**: Tests full pipeline using LlamaIndex strategy
- **Query processing**: Verifies semantic search and RAG generation
- **MongoDB integration**: Tests document storage and retrieval from MongoDB
- **Qdrant integration**: Verifies vector storage and search functionality
- **LangSmith traces**: Tests trace collection and retrieval endpoint
- **Strategy comparison**: Compares results between LangChain and LlamaIndex approaches

### `test_documents_api.py`
Tests document management API endpoints:
- **Document listing**: Tests GET `/documents` endpoint with MongoDB data
- **Document deletion**: Tests DELETE `/documents/{id}` with cascade to Qdrant
- **API response validation**: Verifies correct JSON response formats
- **Error handling**: Tests behavior with missing or invalid document IDs
- **Metadata preservation**: Ensures document metadata is properly stored and retrieved

### `test_error_handling.py`
Tests error scenarios and edge cases:
- **Invalid file types**: Tests rejection of unsupported file formats
- **Authentication failures**: Tests API token validation
- **Database connection errors**: Tests behavior when MongoDB/Qdrant are unavailable
- **Malformed requests**: Tests handling of invalid request formats
- **Large file handling**: Tests behavior with files exceeding size limits
- **Encoding errors**: Tests handling of corrupted or invalid file encodings

### `test_metadata_filtering.py`
Tests metadata handling and filtering functionality:
- **JSON metadata parsing**: Tests storage and retrieval of user-provided metadata
- **Qdrant metadata filtering**: Tests vector search with metadata constraints
- **Search result relevance**: Verifies that metadata filtering improves search accuracy
- **Metadata validation**: Tests handling of invalid or malformed metadata
- **Filter combinations**: Tests complex filtering with multiple metadata fields

## Performance Tests (`performance/`)

Performance tests validate system performance under load and stress conditions.

### `test_api_stress.py`
Load testing and stress testing for the API:
- **Concurrent ingestion**: Tests 10 threads × 10 requests for document ingestion
- **Concurrent querying**: Tests 10 threads × 10 requests for query processing
- **Performance benchmarks**: Measures response times and throughput
- **Resource monitoring**: Tracks CPU and memory usage during stress tests
- **Timeout validation**: Ensures system remains responsive under load
- **Error rate monitoring**: Tracks error rates during concurrent operations

### `test_ingest_performance.py`
Performance testing for document ingestion:
- **Large document processing**: Tests with documents containing 10,000+ words
- **Chunking performance**: Measures time to split large documents into chunks
- **Embedding generation**: Tests time to generate embeddings for large document sets
- **Memory usage**: Monitors memory consumption during processing
- **Performance regression detection**: Ensures performance doesn't degrade over time
- **Scalability testing**: Tests performance with increasing document sizes

## Test Coverage

The test suite provides comprehensive coverage:

- **Unit Tests**: >80% code coverage for core functions
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Load testing and benchmarking
- **Error Handling**: Comprehensive error scenario coverage
- **Authentication**: Token validation and security testing
- **Database Operations**: MongoDB and Qdrant integration testing
- **API Endpoints**: All REST endpoints tested with various scenarios

## Running Tests

### Prerequisites
```bash
pip install pytest pytest-cov
```

### Basic Test Execution
```bash
# Run all tests
pytest src/tests/

# Run specific test categories
pytest src/tests/unit/
pytest src/tests/integration/
pytest src/tests/performance/

# Run with coverage report
pytest --cov=src --cov-report=html src/tests/

# Run specific test file
pytest src/tests/unit/test_validation.py

# Run tests with verbose output
pytest -v src/tests/
```

### Test Configuration
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto src/tests/

# Run tests with detailed failure information
pytest --tb=long src/tests/

# Run tests and stop on first failure
pytest -x src/tests/

# Run tests matching a pattern
pytest -k "validation" src/tests/
```

### Continuous Integration
Tests are automatically run in CI/CD pipelines:
- Unit tests run on every commit
- Integration tests run on pull requests
- Performance tests run on main branch merges
- Coverage reports are generated and tracked

## Test Data

Test data is located in the `sample_data/` directory:
- `sample.txt`, `sample2.txt`, `sample3.txt`: Text files for testing
- `sample.json`, `sample2.json`, `sample3.json`: JSON files for testing
- `sample.pdf`, `sample2.pdf`, `sample3.pdf`: PDF files for testing

## Mocking and Test Isolation

Tests use mocking to isolate components:
- **Database connections**: MongoDB and Qdrant clients are mocked in unit tests
- **External APIs**: LangSmith API calls are mocked
- **File operations**: PDF reading is mocked for consistent testing
- **Authentication**: Token verification is bypassed in integration tests

## Best Practices

1. **Test Isolation**: Each test is independent and doesn't rely on other tests
2. **Clean State**: Tests clean up after themselves to avoid interference
3. **Meaningful Assertions**: Tests verify specific behaviors, not just success/failure
4. **Error Testing**: Tests include both success and error scenarios
5. **Performance Monitoring**: Performance tests include timing and resource usage validation
6. **Documentation**: Test names and comments clearly describe what is being tested 