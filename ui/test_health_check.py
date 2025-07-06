#!/usr/bin/env python3
"""
Simple test script to verify the health check functionality
"""

import requests
import time
import sys

def test_health_check():
    """Test the health check functionality"""
    
    # Test configuration
    API_URL = "http://localhost:8000"
    QDRANT_URL = "http://localhost:6333"
    
    print("🔍 Testing service health checks...")
    print(f"API URL: {API_URL}")
    print(f"Qdrant URL: {QDRANT_URL}")
    print("-" * 50)
    
    # Test API health endpoint
    print("Testing API health endpoint...")
    try:
        response = requests.get(f"{API_URL}/healthz", timeout=90)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
            
            # Check dependencies
            dependencies = data.get('dependencies', {})
            for service, status in dependencies.items():
                service_status = status.get('status', 'unknown')
                print(f"   {service}: {service_status}")
        else:
            print(f"❌ API health check failed with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API health check failed: {e}")
    
    print("-" * 50)
    
    # Test Qdrant collections endpoint
    print("Testing Qdrant collections endpoint...")
    try:
        response = requests.get(f"{QDRANT_URL}/collections", timeout=90)
        if response.status_code == 200:
            print("✅ Qdrant is healthy")
        else:
            print(f"❌ Qdrant collections check failed with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Qdrant collections check failed: {e}")
    
    print("-" * 50)
    
    # Test collections endpoint
    print("Testing Qdrant collections endpoint...")
    try:
        response = requests.get(f"{QDRANT_URL}/collections", timeout=90)
        if response.status_code == 200:
            data = response.json()
            collections = data.get('collections', [])
            print(f"✅ Qdrant collections endpoint working")
            print(f"   Number of collections: {len(collections)}")
            for collection in collections:
                print(f"   - {collection.get('name', 'unknown')}")
        else:
            print(f"❌ Qdrant collections check failed with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Qdrant collections check failed: {e}")

if __name__ == "__main__":
    test_health_check() 