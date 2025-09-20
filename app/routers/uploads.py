from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Upload
from app.schemas import UploadInitiateRequest, UploadInitiateResponse, Upload as UploadSchema
from app.auth import get_current_active_user
from app.services.storage import storage_service
from app.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/initiate", response_model=UploadInitiateResponse)
def initiate_upload(
    request: UploadInitiateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initiate a file upload and get presigned URL"""
    try:
        # Generate presigned upload URL
        upload_data = storage_service.generate_presigned_upload_url(
            filename=request.filename,
            content_type=request.content_type,
            size=request.size
        )
        
        # Create upload record
        upload = Upload(
            user_id=current_user.id,
            storage_key=upload_data["storage_key"],
            bytes=request.size,
            status="pending"
        )
        
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        return UploadInitiateResponse(
            upload_id=upload.id,
            upload_url=upload_data["upload_url"],
            fields=upload_data["fields"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate upload: {str(e)}"
        )


@router.get("/{upload_id}", response_model=UploadSchema)
def get_upload(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get upload information"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    return upload


@router.post("/{upload_id}/complete")
def complete_upload(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark upload as completed and verify file"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    try:
        # Get file info from storage
        file_info = storage_service.get_file_info(upload.storage_key)
        
        # Update upload record
        upload.status = "completed"
        upload.bytes = file_info["size"]
        # Note: In a real implementation, you'd calculate and store the checksum
        
        db.commit()
        
        return {"message": "Upload completed successfully"}
        
    except Exception as e:
        upload.status = "failed"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete upload: {str(e)}"
        )
