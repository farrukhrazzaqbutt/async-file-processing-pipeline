"""
Test configuration that doesn't require external dependencies
"""
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./test.db"
    
    # Redis (not used in tests)
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "test-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # MinIO (mocked in tests)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "test"
    minio_secret_key: str = "test"
    minio_bucket_name: str = "test-bucket"
    minio_secure: bool = False
    
    # Celery (not used in tests)
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Webhook
    webhook_max_retries: int = 5
    webhook_retry_delay: int = 60
    webhook_timeout: int = 30
    
    class Config:
        env_file = ".env"


test_settings = TestSettings()
