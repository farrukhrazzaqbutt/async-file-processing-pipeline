from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://app:app@localhost:5432/app"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "uploads"
    minio_secure: bool = False
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Webhook
    webhook_max_retries: int = 5
    webhook_retry_delay: int = 60  # seconds
    webhook_timeout: int = 30  # seconds
    
    class Config:
        env_file = ".env"


settings = Settings()
