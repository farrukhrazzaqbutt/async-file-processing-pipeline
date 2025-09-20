from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, WebhookEndpoint
from app.schemas import WebhookEndpointCreate, WebhookEndpoint as WebhookEndpointSchema, WebhookTestRequest
from app.auth import get_current_active_user
from app.workers.tasks import send_test_webhook
import secrets

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/endpoints", response_model=WebhookEndpointSchema)
def create_webhook_endpoint(
    request: WebhookEndpointCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new webhook endpoint"""
    # Generate a random secret if not provided
    secret = request.secret or secrets.token_urlsafe(32)
    
    webhook_endpoint = WebhookEndpoint(
        user_id=current_user.id,
        url=request.url,
        secret=secret,
        active=True
    )
    
    db.add(webhook_endpoint)
    db.commit()
    db.refresh(webhook_endpoint)
    
    return webhook_endpoint


@router.get("/endpoints", response_model=list[WebhookEndpointSchema])
def list_webhook_endpoints(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's webhook endpoints"""
    endpoints = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.user_id == current_user.id
    ).all()
    
    return endpoints


@router.get("/endpoints/{endpoint_id}", response_model=WebhookEndpointSchema)
def get_webhook_endpoint(
    endpoint_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get webhook endpoint details"""
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.user_id == current_user.id
    ).first()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found"
        )
    
    return endpoint


@router.put("/endpoints/{endpoint_id}", response_model=WebhookEndpointSchema)
def update_webhook_endpoint(
    endpoint_id: int,
    request: WebhookEndpointCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update webhook endpoint"""
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.user_id == current_user.id
    ).first()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found"
        )
    
    endpoint.url = request.url
    endpoint.secret = request.secret or endpoint.secret
    
    db.commit()
    db.refresh(endpoint)
    
    return endpoint


@router.delete("/endpoints/{endpoint_id}")
def delete_webhook_endpoint(
    endpoint_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete webhook endpoint"""
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.user_id == current_user.id
    ).first()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found"
        )
    
    db.delete(endpoint)
    db.commit()
    
    return {"message": "Webhook endpoint deleted successfully"}


@router.post("/test")
def test_webhook(
    request: WebhookTestRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a test webhook to verify endpoint configuration"""
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == request.endpoint_id,
        WebhookEndpoint.user_id == current_user.id
    ).first()
    
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found"
        )
    
    # Queue test webhook
    send_test_webhook.delay(endpoint.id)
    
    return {"message": "Test webhook queued for delivery"}
