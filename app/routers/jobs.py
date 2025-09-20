from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.models import User, Job, Upload
from app.schemas import JobCreateRequest, JobResponse, JobKind
from app.auth import get_current_active_user
from app.workers.tasks import process_file_job
from app.utils.idempotency import IdempotencyKey
from app.utils.metrics import jobs_created_total
import uuid

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse)
def create_job(
    request: JobCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None)
):
    """Create a new processing job"""
    # Check if upload exists and belongs to user
    upload = db.query(Upload).filter(
        Upload.id == request.upload_id,
        Upload.user_id == current_user.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    if upload.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload must be completed before creating jobs"
        )
    
    # Check for existing job with same idempotency key
    if idempotency_key:
        existing_job = IdempotencyKey.validate_job_creation(
            db, current_user.id, request.upload_id, request.kind, idempotency_key
        )
        
        if existing_job:
            return existing_job
    
    # Create new job
    job = Job(
        upload_id=request.upload_id,
        kind=request.kind,
        status="pending"
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Queue the job for processing
    process_file_job.delay(job.id)
    
    # Update metrics
    jobs_created_total.labels(kind=job.kind).inc()
    
    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get job status and result"""
    job = db.query(Job).join(Upload).filter(
        Job.id == job_id,
        Upload.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.get("/", response_model=list[JobResponse])
def list_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List user's jobs"""
    jobs = db.query(Job).join(Upload).filter(
        Upload.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return jobs
