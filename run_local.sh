#!/bin/bash

# Local RAG Pipeline Development Script
set -e

echo "🚀 Starting RAG Pipeline locally..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Check for .env file in docker/ and set up from template if missing
if [ ! -f "docker/.env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template docker/.env
        echo -e "${YELLOW}[WARNING]${NC} docker/.env file not found. Created one from .env.template. Please fill in your secrets in docker/.env before running this script again."
        exit 1
    else
        echo -e "${RED}[ERROR]${NC} .env.template not found. Please provide a docker/.env file."
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker/docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory."
    exit 1
fi

print_header "Building and starting RAG Pipeline..."

# Build and start services
cd docker

print_status "Building Docker containers..."
docker compose build --no-cache

print_status "Starting services..."
docker compose up -d

print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service health..."

# Check API
if curl -f http://localhost:8000/healthz &> /dev/null; then
    print_status "✅ API is healthy"
else
    print_warning "⚠️ API health check failed, but service might still be starting..."
fi

# Check UI
if curl -f http://localhost:8501 &> /dev/null; then
    print_status "✅ UI is accessible"
else
    print_warning "⚠️ UI accessibility check failed, but service might still be starting..."
fi

# Check MongoDB
if docker compose exec mongodb mongosh --eval "db.runCommand('ping')" &> /dev/null; then
    print_status "✅ MongoDB is running"
else
    print_warning "⚠️ MongoDB check failed"
fi

# Check Qdrant
if curl -f http://localhost:6333/collections &> /dev/null; then
    print_status "✅ Qdrant is running"
else
    print_warning "⚠️ Qdrant check failed"
fi

print_header "🎉 RAG Pipeline is now running!"

echo ""
echo "📋 Service URLs:"
echo "  🌐 UI: http://localhost:8501"
echo "  🔌 API: http://localhost:8000/docs"
echo "  📊 Prometheus: http://localhost:9090"
echo "  🗄️ MongoDB: localhost:27017"
echo "  🔍 Qdrant: http://localhost:6333"
echo ""
echo "📚 Quick Start:"
echo "  1. Open http://localhost:8501 in your browser"
echo "  2. Go to 'Ingest Document' tab to upload your first document"
echo "  3. Go to 'Query' tab to search through your documents"
echo ""
echo "🛑 To stop the services, run: cd docker && docker compose down"
echo "📝 To view logs, run: cd docker && docker compose logs -f"
echo "" 