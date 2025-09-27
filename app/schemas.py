from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class WebhookStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class JobKind(str, Enum):
    TEXT_EXTRACT = "text_extract"
    THUMBNAIL = "thumbnail"
    METADATA = "metadata"


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Upload schemas
class UploadInitiateRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=100)
    size: int = Field(..., gt=0)


class UploadInitiateResponse(BaseModel):
    upload_id: int
    upload_url: str
    fields: Dict[str, Any]


class Upload(BaseModel):
    id: int
    user_id: int
    storage_key: str
    bytes: int
    status: UploadStatus
    checksum: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Job schemas
class JobCreateRequest(BaseModel):
    upload_id: int
    kind: JobKind
    idempotency_key: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    upload_id: int
    kind: JobKind
    status: JobStatus
    attempts: int
    result_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Webhook schemas
class WebhookEndpointCreate(BaseModel):
    url: str = Field(..., pattern=r'^https?://')
    secret: Optional[str] = Field(None, min_length=16, max_length=255)


class WebhookEndpoint(BaseModel):
    id: int
    user_id: int
    url: str
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class WebhookTestRequest(BaseModel):
    endpoint_id: int


class WebhookPayload(BaseModel):
    job_id: int
    status: JobStatus
    result: Optional[Dict[str, Any]]
    timestamp: datetime
    event_type: str = "job.completed"


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
