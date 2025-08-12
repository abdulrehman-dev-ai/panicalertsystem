from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import os
import aiofiles
from datetime import datetime
import mimetypes
from pathlib import Path

from shared.database import get_db_session
from auth_service.models import get_current_user, User
from .schemas import (
    MediaFileResponse,
    MediaFileListResponse,
    MediaFileUpdate
)
from .models import MediaFile, MediaType
from shared.kafka_client import publish_media_event
from shared.config import get_settings

settings = get_settings()
router = APIRouter()

# Allowed file types and sizes
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/mpeg", "video/quicktime", "video/webm"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain"}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5MB

def get_media_type(content_type: str) -> MediaType:
    """Determine media type from content type."""
    if content_type in ALLOWED_IMAGE_TYPES:
        return MediaType.IMAGE
    elif content_type in ALLOWED_VIDEO_TYPES:
        return MediaType.VIDEO
    elif content_type in ALLOWED_AUDIO_TYPES:
        return MediaType.AUDIO
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        return MediaType.DOCUMENT
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}"
        )

def validate_file_size(file_size: int, media_type: MediaType) -> None:
    """Validate file size based on media type."""
    max_sizes = {
        MediaType.IMAGE: MAX_IMAGE_SIZE,
        MediaType.VIDEO: MAX_VIDEO_SIZE,
        MediaType.AUDIO: MAX_AUDIO_SIZE,
        MediaType.DOCUMENT: MAX_DOCUMENT_SIZE
    }
    
    max_size = max_sizes.get(media_type, MAX_FILE_SIZE)
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size for {media_type.value} is {max_size // (1024*1024)}MB"
        )

async def save_uploaded_file(file: UploadFile, user_id: UUID, media_type: MediaType) -> tuple[str, str]:
    """Save uploaded file to disk and return file path and filename."""
    # Create user-specific directory
    user_dir = Path(settings.MEDIA_ROOT) / str(user_id) / media_type.value
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(file.filename).suffix if file.filename else ""
    unique_filename = f"{timestamp}_{file.filename}" if file.filename else f"{timestamp}{file_extension}"
    
    file_path = user_dir / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return str(file_path), unique_filename

@router.post("/upload", response_model=MediaFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_emergency_related: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Upload a media file."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Get content type
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not determine file type"
            )
        
        # Determine media type
        media_type = get_media_type(content_type)
        
        # Read file content to get size
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        validate_file_size(file_size, media_type)
        
        # Reset file pointer
        await file.seek(0)
        
        # Check user's storage quota (100MB per user)
        user_storage_result = await db.execute(
            select(func.sum(MediaFile.file_size)).where(
                MediaFile.user_id == current_user.id
            )
        )
        current_storage = user_storage_result.scalar() or 0
        
        if current_storage + file_size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Storage quota exceeded. Maximum 100MB per user."
            )
        
        # Save file to disk
        file_path, stored_filename = await save_uploaded_file(file, current_user.id, media_type)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Create media file record
        media_file = MediaFile(
            user_id=current_user.id,
            filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            media_type=media_type,
            content_type=content_type,
            file_size=file_size,
            description=description,
            tags=tag_list,
            is_emergency_related=is_emergency_related,
            metadata={
                'upload_timestamp': datetime.utcnow().isoformat(),
                'original_filename': file.filename,
                'upload_ip': None  # Could be added from request
            }
        )
        
        db.add(media_file)
        await db.commit()
        await db.refresh(media_file)
        
        # Publish media upload event
        await publish_media_event({
            "event_type": "media_uploaded",
            "media_id": str(media_file.id),
            "user_id": str(current_user.id),
            "filename": media_file.filename,
            "media_type": media_file.media_type.value,
            "file_size": media_file.file_size,
            "is_emergency_related": media_file.is_emergency_related,
            "timestamp": media_file.created_at.isoformat()
        })
        
        return MediaFileResponse(
            id=media_file.id,
            filename=media_file.filename,
            media_type=media_file.media_type,
            content_type=media_file.content_type,
            file_size=media_file.file_size,
            description=media_file.description,
            tags=media_file.tags,
            is_emergency_related=media_file.is_emergency_related,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at,
            metadata=media_file.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/", response_model=MediaFileListResponse)
async def get_user_media_files(
    skip: int = 0,
    limit: int = 20,
    media_type_filter: Optional[MediaType] = None,
    emergency_only: bool = False,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's media files with pagination and filtering."""
    try:
        # Build query
        query = select(MediaFile).where(MediaFile.user_id == current_user.id)
        
        if media_type_filter:
            query = query.where(MediaFile.media_type == media_type_filter)
        if emergency_only:
            query = query.where(MediaFile.is_emergency_related == True)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                MediaFile.filename.ilike(search_term) |
                MediaFile.description.ilike(search_term)
            )
        
        # Get total count
        count_query = select(func.count(MediaFile.id)).where(MediaFile.user_id == current_user.id)
        if media_type_filter:
            count_query = count_query.where(MediaFile.media_type == media_type_filter)
        if emergency_only:
            count_query = count_query.where(MediaFile.is_emergency_related == True)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                MediaFile.filename.ilike(search_term) |
                MediaFile.description.ilike(search_term)
            )
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get files with pagination
        query = query.order_by(MediaFile.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        media_files = result.scalars().all()
        
        file_responses = [
            MediaFileResponse(
                id=media_file.id,
                filename=media_file.filename,
                media_type=media_file.media_type,
                content_type=media_file.content_type,
                file_size=media_file.file_size,
                description=media_file.description,
                tags=media_file.tags,
                is_emergency_related=media_file.is_emergency_related,
                created_at=media_file.created_at,
                updated_at=media_file.updated_at,
                metadata=media_file.metadata
            )
            for media_file in media_files
        ]
        
        return MediaFileListResponse(
            files=file_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve media files: {str(e)}"
        )

@router.get("/{file_id}", response_model=MediaFileResponse)
async def get_media_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific media file by ID."""
    try:
        result = await db.execute(
            select(MediaFile).where(
                MediaFile.id == file_id,
                MediaFile.user_id == current_user.id
            )
        )
        media_file = result.scalar_one_or_none()
        
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        return MediaFileResponse(
            id=media_file.id,
            filename=media_file.filename,
            media_type=media_file.media_type,
            content_type=media_file.content_type,
            file_size=media_file.file_size,
            description=media_file.description,
            tags=media_file.tags,
            is_emergency_related=media_file.is_emergency_related,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at,
            metadata=media_file.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve media file: {str(e)}"
        )

@router.get("/{file_id}/download")
async def download_media_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Download a media file."""
    try:
        result = await db.execute(
            select(MediaFile).where(
                MediaFile.id == file_id,
                MediaFile.user_id == current_user.id
            )
        )
        media_file = result.scalar_one_or_none()
        
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check if file exists on disk
        if not os.path.exists(media_file.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        # Publish media download event
        await publish_media_event({
            "event_type": "media_downloaded",
            "media_id": str(media_file.id),
            "user_id": str(current_user.id),
            "filename": media_file.filename,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return FileResponse(
            path=media_file.file_path,
            filename=media_file.filename,
            media_type=media_file.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.put("/{file_id}", response_model=MediaFileResponse)
async def update_media_file(
    file_id: UUID,
    file_data: MediaFileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update media file metadata."""
    try:
        result = await db.execute(
            select(MediaFile).where(
                MediaFile.id == file_id,
                MediaFile.user_id == current_user.id
            )
        )
        media_file = result.scalar_one_or_none()
        
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Update fields
        if file_data.description is not None:
            media_file.description = file_data.description
        if file_data.tags is not None:
            media_file.tags = file_data.tags
        if file_data.is_emergency_related is not None:
            media_file.is_emergency_related = file_data.is_emergency_related
        
        await db.commit()
        await db.refresh(media_file)
        
        # Publish media update event
        await publish_media_event({
            "event_type": "media_updated",
            "media_id": str(media_file.id),
            "user_id": str(current_user.id),
            "updated_fields": file_data.dict(exclude_unset=True),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return MediaFileResponse(
            id=media_file.id,
            filename=media_file.filename,
            media_type=media_file.media_type,
            content_type=media_file.content_type,
            file_size=media_file.file_size,
            description=media_file.description,
            tags=media_file.tags,
            is_emergency_related=media_file.is_emergency_related,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at,
            metadata=media_file.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update media file: {str(e)}"
        )

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a media file."""
    try:
        result = await db.execute(
            select(MediaFile).where(
                MediaFile.id == file_id,
                MediaFile.user_id == current_user.id
            )
        )
        media_file = result.scalar_one_or_none()
        
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Delete file from disk
        if os.path.exists(media_file.file_path):
            os.remove(media_file.file_path)
        
        # Delete database record
        await db.delete(media_file)
        await db.commit()
        
        # Publish media delete event
        await publish_media_event({
            "event_type": "media_deleted",
            "media_id": str(file_id),
            "user_id": str(current_user.id),
            "filename": media_file.filename,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete media file: {str(e)}"
        )

@router.get("/storage/usage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's storage usage statistics."""
    try:
        # Get total storage used
        total_result = await db.execute(
            select(func.sum(MediaFile.file_size)).where(
                MediaFile.user_id == current_user.id
            )
        )
        total_used = total_result.scalar() or 0
        
        # Get file count by type
        type_stats = {}
        for media_type in MediaType:
            count_result = await db.execute(
                select(func.count(MediaFile.id)).where(
                    MediaFile.user_id == current_user.id,
                    MediaFile.media_type == media_type
                )
            )
            size_result = await db.execute(
                select(func.sum(MediaFile.file_size)).where(
                    MediaFile.user_id == current_user.id,
                    MediaFile.media_type == media_type
                )
            )
            type_stats[media_type.value] = {
                "count": count_result.scalar() or 0,
                "size_bytes": size_result.scalar() or 0
            }
        
        return {
            "total_used_bytes": total_used,
            "total_limit_bytes": 100 * 1024 * 1024,  # 100MB
            "usage_percentage": (total_used / (100 * 1024 * 1024)) * 100,
            "remaining_bytes": (100 * 1024 * 1024) - total_used,
            "by_type": type_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve storage usage: {str(e)}"
        )

# Import required SQLAlchemy functions
from sqlalchemy import select, func