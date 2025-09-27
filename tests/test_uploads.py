import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@patch('app.services.storage.storage_service')
def test_initiate_upload(mock_storage_service, client: TestClient, auth_headers):
    """Test initiating file upload"""
    mock_storage_service.generate_presigned_upload_url.return_value = {
        "upload_url": "https://minio.example.com/upload",
        "fields": {"key": "uploads/test-file.txt"},
        "storage_key": "uploads/test-file.txt"
    }
    
    upload_data = {
        "filename": "test-file.txt",
        "content_type": "text/plain",
        "size": 1024
    }
    
    response = client.post("/uploads/initiate", json=upload_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert "upload_url" in data
    assert "fields" in data


def test_initiate_upload_unauthorized(client: TestClient):
    """Test initiating upload without authentication"""
    upload_data = {
        "filename": "test-file.txt",
        "content_type": "text/plain",
        "size": 1024
    }
    
    response = client.post("/uploads/initiate", json=upload_data)
    assert response.status_code == 403


@patch('app.services.storage.storage_service')
def test_complete_upload(mock_storage_service, client: TestClient, auth_headers, db_session):
    """Test completing file upload"""
    from app.models import Upload, User
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    
    upload = Upload(
        user_id=user.id,
        storage_key="uploads/test-file.txt",
        bytes=1024,
        status="pending"
    )
    db_session.add(upload)
    db_session.commit()
    
    mock_storage_service.get_file_info.return_value = {
        "size": 1024,
        "etag": "test-etag",
        "last_modified": "2023-01-01T00:00:00Z",
        "content_type": "text/plain"
    }
    
    response = client.post(f"/uploads/{upload.id}/complete", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "Upload completed successfully" in data["message"]


def test_get_upload(client: TestClient, auth_headers, db_session):
    """Test getting upload information"""
    from app.models import Upload, User
    # Get the user from auth_headers (already created by the fixture)
    user = db_session.query(User).filter(User.username == "testuser").first()
    
    upload = Upload(
        user_id=user.id,
        storage_key="uploads/test-file.txt",
        bytes=1024,
        status="completed"
    )
    db_session.add(upload)
    db_session.commit()
    
    response = client.get(f"/uploads/{upload.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == upload.id
    assert data["storage_key"] == upload.storage_key
    assert data["bytes"] == upload.bytes
