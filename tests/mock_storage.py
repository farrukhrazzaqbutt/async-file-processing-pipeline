"""
Mock storage service for testing
"""
from typing import Dict, Any


class MockStorageService:
    def __init__(self):
        pass
    
    def generate_presigned_upload_url(
        self, 
        filename: str, 
        content_type: str, 
        size: int
    ) -> Dict[str, Any]:
        """Mock presigned upload URL generation"""
        return {
            "upload_url": "https://mock-minio.example.com/upload",
            "fields": {"key": f"uploads/mock-{filename}"},
            "storage_key": f"uploads/mock-{filename}"
        }
    
    def get_file_info(self, storage_key: str) -> Dict[str, Any]:
        """Mock file info retrieval"""
        return {
            "size": 1024,
            "etag": "mock-etag",
            "last_modified": "2023-01-01T00:00:00Z",
            "content_type": "text/plain"
        }
    
    def download_file(self, storage_key: str) -> bytes:
        """Mock file download"""
        return b"mock file content"
    
    def delete_file(self, storage_key: str) -> bool:
        """Mock file deletion"""
        return True
    
    def calculate_checksum(self, data: bytes) -> str:
        """Mock checksum calculation"""
        return "mock-checksum"


# Mock instance
mock_storage_service = MockStorageService()
