import asyncio
from celery import current_task
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db import engine
from app.models import Job, Upload
from app.services.processing import processing_service
from app.services.webhook import webhook_service
from app.workers.celery_app import celery_app
from app.utils.metrics import (
    jobs_completed_total, jobs_failed_total, 
    processing_time_histogram, webhook_delivery_attempts
)
import time

# Create a new session factory for Celery workers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True, name="process_file_job")
def process_file_job(self, job_id: int):
    """Process a file job in the background"""
    db = SessionLocal()
    
    try:
        # Get the job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Update task progress
        current_task.update_state(
            state="PROGRESS",
            meta={"job_id": job_id, "status": "processing"}
        )
        
        # Process the job with timing
        start_time = time.time()
        result = processing_service.process_job(job, db)
        processing_time = time.time() - start_time
        
        # Update metrics
        jobs_completed_total.labels(kind=job.kind).inc()
        processing_time_histogram.labels(kind=job.kind).observe(processing_time)
        
        # Send webhooks
        webhook_results = asyncio.run(webhook_service.send_webhooks_for_job(job, db))
        
        # Update webhook metrics
        for i, success in enumerate(webhook_results):
            webhook_delivery_attempts.labels(
                endpoint_id=f"endpoint_{i}",
                status="delivered" if success else "failed"
            ).inc()
        
        return {
            "job_id": job_id,
            "status": "completed",
            "result": result,
            "processing_time": processing_time
        }
        
    except Exception as e:
        # Update job status to failed
        if 'job' in locals():
            job.status = "failed"
            job.result_json = {"error": str(e)}
            db.commit()
            
            # Update metrics
            jobs_failed_total.labels(kind=job.kind, reason="processing_error").inc()
        
        # Update task state
        current_task.update_state(
            state="FAILURE",
            meta={"job_id": job_id, "error": str(e)}
        )
        
        raise e
    
    finally:
        db.close()


@celery_app.task(name="send_test_webhook")
def send_test_webhook(endpoint_id: int):
    """Send a test webhook to verify endpoint configuration"""
    db = SessionLocal()
    
    try:
        from app.models import WebhookEndpoint
        endpoint = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.id == endpoint_id
        ).first()
        
        if not endpoint:
            raise ValueError(f"Webhook endpoint {endpoint_id} not found")
        
        # Send test webhook
        success = asyncio.run(webhook_service.send_test_webhook(endpoint, db))
        
        return {
            "endpoint_id": endpoint_id,
            "success": success
        }
        
    except Exception as e:
        raise e
    
    finally:
        db.close()
