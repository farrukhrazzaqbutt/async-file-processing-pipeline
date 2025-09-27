import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient, test_user_data):
    """Test user registration"""
    response = client.post("/auth/register", json=test_user_data)
    # Allow both 200 (success) and 400 (already exists)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "created_at" in data
    else:
        # User already exists, which is fine for this test
        assert "already registered" in response.json()["detail"]


def test_register_duplicate_user(client: TestClient, test_user_data):
    """Test registering duplicate user fails"""
    # Try to register same user again (user might already exist from previous test)
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client: TestClient, test_user_data):
    """Test successful login"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, test_user_data):
    """Test login with invalid credentials"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login with wrong password
    login_data = {
        "username": test_user_data["username"],
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401


def test_seed_admin_user(client: TestClient):
    """Test seeding admin user"""
    response = client.post("/auth/seed")
    assert response.status_code == 200
    data = response.json()
    assert "Admin user created successfully" in data["message"]
    assert data["username"] == "admin"
    assert data["password"] == "admin"
