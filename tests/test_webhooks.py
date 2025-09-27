import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_create_webhook_endpoint(client: TestClient, auth_headers):
    """Test creating webhook endpoint"""
    endpoint_data = {
        "url": "https://example.com/webhook",
        "secret": "test-secret-key-123"
    }
    
    response = client.post("/webhooks/endpoints", json=endpoint_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == endpoint_data["url"]
    assert data["active"] == True
    assert "id" in data


def test_create_webhook_endpoint_without_secret(client: TestClient, auth_headers):
    """Test creating webhook endpoint without providing secret"""
    endpoint_data = {
        "url": "https://example.com/webhook"
    }
    
    response = client.post("/webhooks/endpoints", json=endpoint_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == endpoint_data["url"]
    assert data["active"] == True


def test_list_webhook_endpoints(client: TestClient, auth_headers, db_session):
    """Test listing webhook endpoints"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoints
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        # Create user if it doesn't exist
        from app.auth import get_password_hash
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123")
        )
        db_session.add(user)
        db_session.commit()
    
    endpoint1 = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook1",
        secret="secret1",
        active=True
    )
    endpoint2 = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook2",
        secret="secret2",
        active=False
    )
    db_session.add_all([endpoint1, endpoint2])
    db_session.commit()
    
    response = client.get("/webhooks/endpoints", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_webhook_endpoint(client: TestClient, auth_headers, db_session):
    """Test getting specific webhook endpoint"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoint
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        # Create user if it doesn't exist
        from app.auth import get_password_hash
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123")
        )
        db_session.add(user)
        db_session.commit()
    
    endpoint = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook",
        secret="test-secret",
        active=True
    )
    db_session.add(endpoint)
    db_session.commit()
    
    response = client.get(f"/webhooks/endpoints/{endpoint.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == endpoint.id
    assert data["url"] == endpoint.url


def test_update_webhook_endpoint(client: TestClient, auth_headers, db_session):
    """Test updating webhook endpoint"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoint
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        # Create user if it doesn't exist
        from app.auth import get_password_hash
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123")
        )
        db_session.add(user)
        db_session.commit()
    
    endpoint = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook",
        secret="test-secret",
        active=True
    )
    db_session.add(endpoint)
    db_session.commit()
    
    update_data = {
        "url": "https://example.com/webhook-updated",
        "secret": "new-secret-key-123"
    }
    
    response = client.put(f"/webhooks/endpoints/{endpoint.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == update_data["url"]


def test_delete_webhook_endpoint(client: TestClient, auth_headers, db_session):
    """Test deleting webhook endpoint"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoint
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        # Create user if it doesn't exist
        from app.auth import get_password_hash
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123")
        )
        db_session.add(user)
        db_session.commit()
    
    endpoint = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook",
        secret="test-secret",
        active=True
    )
    db_session.add(endpoint)
    db_session.commit()
    
    response = client.delete(f"/webhooks/endpoints/{endpoint.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@patch('app.routers.webhooks.send_test_webhook')
def test_send_test_webhook(mock_send_webhook, client: TestClient, auth_headers, db_session):
    """Test sending test webhook"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoint
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        # Create user if it doesn't exist
        from app.auth import get_password_hash
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123")
        )
        db_session.add(user)
        db_session.commit()
    
    endpoint = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook",
        secret="test-secret",
        active=True
    )
    db_session.add(endpoint)
    db_session.commit()
    
    test_data = {
        "endpoint_id": endpoint.id
    }
    
    response = client.post("/webhooks/test", json=test_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "Test webhook queued for delivery" in data["message"]
    
    # Verify test webhook was queued
    mock_send_webhook.delay.assert_called_once_with(endpoint.id)
