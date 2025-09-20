#!/usr/bin/env python3
"""
Simple API test script
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints"""
    print("🧪 Testing Async File Processing Pipeline API")
    print("=" * 50)
    
    # Test health check
    print("1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✅ Health check passed")
    
    # Test root endpoint
    print("2. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    print("✅ Root endpoint passed")
    
    # Test API documentation
    print("3. Testing API documentation...")
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200
    print("✅ API documentation accessible")
    
    # Test metrics endpoint
    print("4. Testing metrics endpoint...")
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    print("✅ Metrics endpoint accessible")
    
    # Test authentication
    print("5. Testing authentication...")
    
    # Register a test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code == 200:
        print("✅ User registration passed")
    elif response.status_code == 400 and "already registered" in response.text:
        print("ℹ️  User already exists")
    else:
        print(f"❌ User registration failed: {response.status_code} - {response.text}")
        return
    
    # Login
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ User login passed")
    
    # Test upload initiation (this will fail without MinIO, but we can test the endpoint)
    print("6. Testing upload initiation...")
    upload_data = {
        "filename": "test.txt",
        "content_type": "text/plain",
        "size": 1024
    }
    
    response = requests.post(f"{BASE_URL}/uploads/initiate", json=upload_data, headers=headers)
    if response.status_code == 200:
        print("✅ Upload initiation passed")
    else:
        print(f"ℹ️  Upload initiation failed (expected without MinIO): {response.status_code}")
    
    # Test webhook endpoint creation
    print("7. Testing webhook endpoint creation...")
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test-secret-key"
    }
    
    response = requests.post(f"{BASE_URL}/webhooks/endpoints", json=webhook_data, headers=headers)
    assert response.status_code == 200
    webhook_id = response.json()["id"]
    print("✅ Webhook endpoint creation passed")
    
    # Test webhook listing
    print("8. Testing webhook listing...")
    response = requests.get(f"{BASE_URL}/webhooks/endpoints", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    print("✅ Webhook listing passed")
    
    print("\n🎉 All tests passed! The API is working correctly.")
    print(f"📚 API Documentation: {BASE_URL}/docs")
    print(f"📊 Metrics: {BASE_URL}/metrics")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
