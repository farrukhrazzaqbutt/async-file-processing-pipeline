import hmac
import hashlib
import json
import asyncio
from datetime import datetime
from typing import List, Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models import WebhookEndpoint, WebhookDelivery, Job
from app.schemas import WebhookPayload


class WebhookService:
    def __init__(self):
        self.timeout = settings.webhook_timeout
        self.max_retries = settings.webhook_max_retries
        self.retry_delay = settings.webhook_retry_delay
    
    def generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        expected_signature = self.generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    async def send_webhook(
        self, 
        endpoint: WebhookEndpoint, 
        payload: WebhookPayload,
        db: Session
    ) -> bool:
        """Send webhook to endpoint with retry logic"""
        payload_json = payload.model_dump_json()
        signature = self.generate_signature(payload_json, endpoint.secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Webhook-Event": payload.event_type,
            "User-Agent": "FileProcessingPipeline/1.0"
        }
        
        # Create webhook delivery record
        delivery = WebhookDelivery(
            job_id=payload.job_id,
            endpoint_id=endpoint.id,
            status="pending",
            attempts=0,
            signature=signature
        )
        db.add(delivery)
        db.commit()
        
        # Attempt delivery with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint.url,
                        content=payload_json,
                        headers=headers
                    )
                    
                    if response.status_code >= 200 and response.status_code < 300:
                        # Success
                        delivery.status = "delivered"
                        delivery.attempts = attempt
                        delivery.last_error = None
                        db.commit()
                        return True
                    else:
                        # HTTP error
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        delivery.last_error = error_msg
                        db.commit()
                        
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay * attempt)
                        else:
                            delivery.status = "failed"
                            db.commit()
                            return False
                            
            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                delivery.last_error = error_msg
                delivery.attempts = attempt
                db.commit()
                
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
                else:
                    delivery.status = "failed"
                    db.commit()
                    return False
        
        return False
    
    async def send_webhooks_for_job(
        self, 
        job: Job, 
        db: Session
    ) -> List[bool]:
        """Send webhooks to all active endpoints for a job"""
        # Get all active webhook endpoints for the job's user
        endpoints = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.user_id == job.upload.user_id,
            WebhookEndpoint.active == True
        ).all()
        
        if not endpoints:
            return []
        
        # Create webhook payload
        payload = WebhookPayload(
            job_id=job.id,
            status=job.status,
            result=job.result_json,
            timestamp=datetime.utcnow(),
            event_type="job.completed" if job.status == "completed" else "job.failed"
        )
        
        # Send webhooks concurrently
        tasks = [
            self.send_webhook(endpoint, payload, db)
            for endpoint in endpoints
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to False
        return [result if isinstance(result, bool) else False for result in results]
    
    async def send_test_webhook(
        self, 
        endpoint: WebhookEndpoint, 
        db: Session
    ) -> bool:
        """Send a test webhook to verify endpoint configuration"""
        test_payload = WebhookPayload(
            job_id=0,  # Test job ID
            status="completed",
            result={"test": True, "message": "This is a test webhook"},
            timestamp=datetime.utcnow(),
            event_type="test"
        )
        
        return await self.send_webhook(endpoint, test_payload, db)


# Global instance
webhook_service = WebhookService()
