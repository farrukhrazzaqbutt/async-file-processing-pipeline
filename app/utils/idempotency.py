import hashlib
import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models import Job


class IdempotencyKey:
    """Helper class for generating and validating idempotency keys"""
    
    @staticmethod
    def generate(user_id: int, operation: str, **kwargs) -> str:
        """Generate an idempotency key for an operation"""
        data = {
            "user_id": user_id,
            "operation": operation,
            **kwargs
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @staticmethod
    def validate_job_creation(
        db: Session, 
        user_id: int, 
        upload_id: int, 
        kind: str,
        idempotency_key: Optional[str] = None
    ) -> Optional[Job]:
        """Check if a job with the same parameters already exists"""
        if not idempotency_key:
            return None
        
        # Look for existing job with same parameters
        existing_job = db.query(Job).join(Job.upload).filter(
            Job.upload.has(user_id=user_id),
            Job.upload_id == upload_id,
            Job.kind == kind
        ).first()
        
        return existing_job
