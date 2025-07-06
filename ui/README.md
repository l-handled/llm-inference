# 21.co RAG LLM Pipeline UI

This directory contains a Streamlit-based web UI for interacting with the RAG LLM inference pipeline.

## Features
- 21.co branding and modern look
- **Service health monitoring with loading screen** - Waits for all services to be ready before showing the UI
- Upload and ingest documents (PDF, TXT, JSON)
- Query the RAG system (vector, hybrid, filters)
- List and delete processed documents (from MongoDB)
- View Prometheus metrics and charts (request count, error rate, latency)
- View LangSmith traces and evaluation results for all LLM/RAG requests
- **Select chunking/indexing strategy (LangChain vs LlamaIndex) for both ingest and query**
- **MongoDB for document storage/metadata, Qdrant for embeddings and search**

## Prometheus Tab
- The "Metrics" tab in the UI fetches and visualizes real-time Prometheus metrics from the API.
- Metrics include request counts by endpoint/status, error rates, and request latency.
- You can use this tab to monitor API health and performance at a glance.

## New: LangSmith Traces Tab
- The "LangSmith Traces" tab in the UI shows recent traces and evaluation results for all LLM and RAG requests.
- Use this tab to debug, benchmark, and improve your pipeline.

## New: Strategy Selection
- You can select between LangChain and LlamaIndex for chunking and indexing strategies directly in the UI for both ingest and query.
- All LLM and RAG requests are traced and evaluated with LangSmith for easy debugging and benchmarking.

## Service Health Monitoring
- The UI automatically checks if all required services (API, MongoDB, Qdrant) are running and healthy
- A loading screen is shown while services are starting up, with real-time status updates
- Service status is displayed in the sidebar for ongoing monitoring
- Automatic retry mechanism with helpful troubleshooting steps if services fail to start
- Expected startup time: 30-60 seconds for all services

**Development Mode**: Add `?skip_health_check=true` to the URL to bypass the health check (useful for development)

## MongoDB & Qdrant Integration
- All uploaded documents and their metadata are stored in MongoDB.
- The "Documents" tab lists documents from MongoDB, allowing you to view, filter, and delete them.
- Qdrant is used for all embedding and semantic search operations.

## Usage

### Local
```bash
pip install -r requirements.txt
streamlit run app.py
```
- Set `API_URL` and `API_TOKEN` in `.streamlit/secrets.toml` or edit in `app.py`.

### Docker
```bash
docker build -t rag-ui .
docker run -p 8501:8501 --env API_URL=http://host.docker.internal:8000 --env API_TOKEN=changeme rag-ui
```

### Docker Compose (add to your main compose file):
```yaml
  ui:
    build: ./ui
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
      - API_TOKEN=changeme
    depends_on:
      - api
```

## Customization
- Branding and colors can be changed in `app.py`.
- Charts are auto-generated from Prometheus metrics.
- LangSmith integration can be configured with your API key and project settings.
- **Strategy selection and LangSmith Traces are available in the UI navigation.** 