import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@patch('app.workers.tasks.process_file_job.delay')
def test_create_job(mock_process_job, client: TestClient, auth_headers, db_session):
    """Test creating a processing job"""
    from app.models import Upload, User
    
    # Create test user and upload
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    
    upload = Upload(
        user_id=user.id,
        storage_key="uploads/test-file.txt",
        bytes=1024,
        status="completed"
    )
    db_session.add(upload)
    db_session.commit()
    
    job_data = {
        "upload_id": upload.id,
        "kind": "text_extract"
    }
    
    response = client.post("/jobs/", json=job_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["upload_id"] == upload.id
    assert data["kind"] == "text_extract"
    assert data["status"] == "pending"
    
    # Verify job was queued
    mock_process_job.assert_called_once()


def test_create_job_upload_not_found(client: TestClient, auth_headers):
    """Test creating job with non-existent upload"""
    job_data = {
        "upload_id": 999,
        "kind": "text_extract"
    }
    
    response = client.post("/jobs/", json=job_data, headers=auth_headers)
    assert response.status_code == 404


def test_create_job_upload_not_completed(client: TestClient, auth_headers, db_session):
    """Test creating job with incomplete upload"""
    from app.models import Upload, User
    
    # Create test user and upload
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    
    upload = Upload(
        user_id=user.id,
        storage_key="uploads/test-file.txt",
        bytes=1024,
        status="pending"  # Not completed
    )
    db_session.add(upload)
    db_session.commit()
    
    job_data = {
        "upload_id": upload.id,
        "kind": "text_extract"
    }
    
    response = client.post("/jobs/", json=job_data, headers=auth_headers)
    assert response.status_code == 400


def test_get_job(client: TestClient, auth_headers, db_session):
    """Test getting job information"""
    from app.models import Job, Upload, User
    
    # Create test user, upload, and job
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    
    upload = Upload(
        user_id=user.id,
        storage_key="uploads/test-file.txt",
        bytes=1024,
        status="completed"
    )
    db_session.add(upload)
    db_session.commit()
    
    job = Job(
        upload_id=upload.id,
        kind="text_extract",
        status="pending"
    )
    db_session.add(job)
    db_session.commit()
    
    response = client.get(f"/jobs/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["upload_id"] == upload.id
    assert data["kind"] == "text_extract"


def test_list_jobs(client: TestClient, auth_headers, db_session):
    """Test listing user's jobs"""
    from app.models import Job, Upload, User
    
    # Create test user, upload, and jobs
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    
    upload = Upload(
        user_id=user.id,
        storage_key="uploads/test-file.txt",
        bytes=1024,
        status="completed"
    )
    db_session.add(upload)
    db_session.commit()
    
    job1 = Job(upload_id=upload.id, kind="text_extract", status="pending")
    job2 = Job(upload_id=upload.id, kind="thumbnail", status="completed")
    db_session.add_all([job1, job2])
    db_session.commit()
    
    response = client.get("/jobs/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
