import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_create_webhook_endpoint(client: TestClient, auth_headers):
    """Test creating webhook endpoint"""
    endpoint_data = {
        "url": "https://example.com/webhook",
        "secret": "test-secret-key"
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
    assert "secret" in data  # Should be auto-generated


def test_list_webhook_endpoints(client: TestClient, auth_headers, db_session):
    """Test listing webhook endpoints"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoints
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
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
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
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
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
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
        "secret": "new-secret"
    }
    
    response = client.put(f"/webhooks/endpoints/{endpoint.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == update_data["url"]


def test_delete_webhook_endpoint(client: TestClient, auth_headers, db_session):
    """Test deleting webhook endpoint"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoint
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
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


@patch('app.workers.tasks.send_test_webhook.delay')
def test_send_test_webhook(mock_send_webhook, client: TestClient, auth_headers, db_session):
    """Test sending test webhook"""
    from app.models import WebhookEndpoint, User
    
    # Create test user and endpoint
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
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
    mock_send_webhook.assert_called_once_with(endpoint.id)
