import json
import hashlib
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Job, Upload
from app.schemas import JobKind
from app.services.storage import storage_service


class ProcessingService:
    def __init__(self):
        self.processors = {
            JobKind.TEXT_EXTRACT: self._extract_text,
            JobKind.THUMBNAIL: self._generate_thumbnail,
            JobKind.METADATA: self._extract_metadata,
        }
    
    def process_job(self, job: Job, db: Session) -> Dict[str, Any]:
        """Process a job based on its kind"""
        try:
            # Update job status to processing
            job.status = "processing"
            db.commit()
            
            # Get the processor for this job kind
            processor = self.processors.get(job.kind)
            if not processor:
                raise ValueError(f"Unknown job kind: {job.kind}")
            
            # Download file from storage
            file_data = storage_service.download_file(job.upload.storage_key)
            
            # Process the file
            result = processor(file_data, job.upload.storage_key)
            
            # Update job with result
            job.status = "completed"
            job.result_json = result
            job.attempts += 1
            db.commit()
            
            return result
            
        except Exception as e:
            # Mark job as failed
            job.status = "failed"
            job.attempts += 1
            job.result_json = {"error": str(e)}
            db.commit()
            raise e
    
    def _extract_text(self, file_data: bytes, storage_key: str) -> Dict[str, Any]:
        """Extract text from various file types"""
        # This is a simplified implementation
        # In a real application, you'd use libraries like:
        # - PyPDF2 for PDFs
        # - python-docx for Word documents
        # - Pillow for images with OCR
        
        file_extension = storage_key.split('.')[-1].lower()
        
        if file_extension == 'txt':
            text = file_data.decode('utf-8', errors='ignore')
        elif file_extension == 'md':
            text = file_data.decode('utf-8', errors='ignore')
        else:
            # For other file types, return a placeholder
            text = f"Text extraction not implemented for .{file_extension} files"
        
        return {
            "text": text,
            "length": len(text),
            "file_type": file_extension,
            "extraction_method": "basic"
        }
    
    def _generate_thumbnail(self, file_data: bytes, storage_key: str) -> Dict[str, Any]:
        """Generate thumbnail for images"""
        # This is a simplified implementation
        # In a real application, you'd use Pillow to generate actual thumbnails
        
        file_extension = storage_key.split('.')[-1].lower()
        
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            # Calculate a simple hash as a placeholder for thumbnail
            thumbnail_hash = hashlib.md5(file_data).hexdigest()
            
            return {
                "thumbnail_url": f"/thumbnails/{thumbnail_hash}.jpg",
                "thumbnail_size": "150x150",
                "file_type": file_extension,
                "generation_method": "placeholder"
            }
        else:
            return {
                "error": f"Thumbnail generation not supported for .{file_extension} files",
                "file_type": file_extension
            }
    
    def _extract_metadata(self, file_data: bytes, storage_key: str) -> Dict[str, Any]:
        """Extract metadata from files"""
        file_extension = storage_key.split('.')[-1].lower()
        file_size = len(file_data)
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        metadata = {
            "file_name": storage_key.split('/')[-1],
            "file_size": file_size,
            "file_hash": file_hash,
            "file_extension": file_extension,
            "storage_key": storage_key
        }
        
        # Add file-specific metadata
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            metadata.update({
                "type": "image",
                "mime_type": f"image/{file_extension}"
            })
        elif file_extension == 'pdf':
            metadata.update({
                "type": "document",
                "mime_type": "application/pdf"
            })
        elif file_extension in ['txt', 'md']:
            metadata.update({
                "type": "text",
                "mime_type": f"text/{file_extension}"
            })
        else:
            metadata.update({
                "type": "unknown",
                "mime_type": "application/octet-stream"
            })
        
        return metadata


# Global instance
processing_service = ProcessingService()
