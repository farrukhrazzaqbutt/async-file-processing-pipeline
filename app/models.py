from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    uploads = relationship("Upload", back_populates="user")
    webhook_endpoints = relationship("WebhookEndpoint", back_populates="user")


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    storage_key = Column(String(500), nullable=False, unique=True, index=True)
    bytes = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, failed
    checksum = Column(String(64), nullable=True)  # SHA256 checksum
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="uploads")
    jobs = relationship("Job", back_populates="upload")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    kind = Column(String(50), nullable=False)  # text_extract, thumbnail, etc.
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    attempts = Column(Integer, default=0)
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    upload = relationship("Upload", back_populates="jobs")
    webhook_deliveries = relationship("WebhookDelivery", back_populates="job")


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="webhook_endpoints")
    webhook_deliveries = relationship("WebhookDelivery", back_populates="endpoint")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, delivered, failed
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    signature = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="webhook_deliveries")
    endpoint = relationship("WebhookEndpoint", back_populates="webhook_deliveries")
