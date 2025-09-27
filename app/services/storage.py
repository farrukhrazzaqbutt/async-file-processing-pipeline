import hashlib
import uuid
from datetime import timedelta
from typing import Dict, Any
from app.config import settings

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    # Create dummy classes for testing
    class Minio:
        def __init__(self, *args, **kwargs):
            pass
    class S3Error(Exception):
        pass


class StorageService:
    def __init__(self):
        if MINIO_AVAILABLE:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            self.bucket_name = settings.minio_bucket_name
            self._ensure_bucket_exists()
        else:
            # For testing or when MinIO is not available
            self.client = None
            self.bucket_name = settings.minio_bucket_name
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        if not MINIO_AVAILABLE or not self.client:
            return
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise Exception(f"Failed to create bucket: {e}")
    
    def generate_presigned_upload_url(
        self, 
        filename: str, 
        content_type: str, 
        size: int
    ) -> Dict[str, Any]:
        """Generate a presigned URL for direct upload to MinIO"""
        if not MINIO_AVAILABLE or not self.client:
            # Return mock data for testing
            file_id = str(uuid.uuid4())
            storage_key = f"uploads/{file_id}/{filename}"
            return {
                "upload_url": "https://mock-minio.example.com/upload",
                "fields": {"key": storage_key},
                "storage_key": storage_key
            }
        
        # Generate unique storage key
        file_id = str(uuid.uuid4())
        storage_key = f"uploads/{file_id}/{filename}"
        
        # Generate presigned POST URL
        try:
            policy = self.client.get_presigned_post_policy(
                bucket_name=self.bucket_name,
                object_name=storage_key,
                expires=timedelta(hours=1)
            )
            
            # Add content type and size constraints
            policy.add_condition("content-type", content_type)
            policy.add_condition("content-length-range", 1, size)
            
            # Generate presigned URL
            presigned_url = self.client.presigned_post_policy(policy)
            
            return {
                "upload_url": presigned_url["url"],
                "fields": presigned_url["fields"],
                "storage_key": storage_key
            }
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def get_file_info(self, storage_key: str) -> Dict[str, Any]:
        """Get file information from MinIO"""
        if not MINIO_AVAILABLE or not self.client:
            # Return mock data for testing
            return {
                "size": 1024,
                "etag": "mock-etag",
                "last_modified": "2023-01-01T00:00:00Z",
                "content_type": "text/plain"
            }
        
        try:
            stat = self.client.stat_object(self.bucket_name, storage_key)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type
            }
        except S3Error as e:
            raise Exception(f"Failed to get file info: {e}")
    
    def download_file(self, storage_key: str) -> bytes:
        """Download file content from MinIO"""
        if not MINIO_AVAILABLE or not self.client:
            # Return mock data for testing
            return b"mock file content"
        
        try:
            response = self.client.get_object(self.bucket_name, storage_key)
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to download file: {e}")
        finally:
            response.close()
            response.release_conn()
    
    def delete_file(self, storage_key: str) -> bool:
        """Delete file from MinIO"""
        if not MINIO_AVAILABLE or not self.client:
            # Return mock success for testing
            return True
        
        try:
            self.client.remove_object(self.bucket_name, storage_key)
            return True
        except S3Error as e:
            raise Exception(f"Failed to delete file: {e}")
    
    def calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum of data"""
        return hashlib.sha256(data).hexdigest()


# Global instance
storage_service = StorageService()
