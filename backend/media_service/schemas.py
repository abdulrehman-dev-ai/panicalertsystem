from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class MediaType(str, Enum):
    """Enumeration for media types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"

class MediaStatus(str, Enum):
    """Enumeration for media statuses."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    AVAILABLE = "available"
    FAILED = "failed"
    DELETED = "deleted"

class MediaVisibility(str, Enum):
    """Enumeration for media visibility."""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"

class MediaUploadResponse(BaseModel):
    """Response schema for media upload."""
    id: UUID
    filename: str
    original_filename: str
    media_type: MediaType
    file_size: int
    mime_type: str
    status: MediaStatus
    upload_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MediaFileResponse(BaseModel):
    """Response schema for media file."""
    id: UUID
    user_id: UUID
    filename: str
    original_filename: str
    media_type: MediaType
    file_size: int
    mime_type: str
    status: MediaStatus
    visibility: MediaVisibility
    description: Optional[str] = None
    tags: List[str] = []
    is_emergency_related: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    download_count: int = 0
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class MediaFileUpdate(BaseModel):
    """Schema for updating media file metadata."""
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_emergency_related: Optional[bool] = None
    visibility: Optional[MediaVisibility] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError('Description cannot be longer than 1000 characters')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError('Maximum 20 tags allowed')
            
            validated_tags = []
            for tag in v:
                tag = tag.strip().lower()
                if len(tag) == 0:
                    continue
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
                if tag not in validated_tags:
                    validated_tags.append(tag)
            
            return validated_tags
        return v

class MediaListResponse(BaseModel):
    """Response schema for media file list."""
    files: List[MediaFileResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
    total_size_bytes: int

class MediaSearchRequest(BaseModel):
    """Schema for searching media files."""
    query: Optional[str] = None
    media_type: Optional[MediaType] = None
    is_emergency_related: Optional[bool] = None
    tags: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    limit: int = 20
    skip: int = 0
    sort_by: str = 'created_at'
    sort_order: str = 'desc'
    
    @validator('limit')
    def validate_limit(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_sorts = ['created_at', 'updated_at', 'filename', 'file_size', 'download_count']
        if v not in valid_sorts:
            raise ValueError(f'Sort by must be one of: {valid_sorts}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be either "asc" or "desc"')
        return v
    
    @validator('radius_km')
    def validate_radius(cls, v):
        if v is not None and (v <= 0 or v > 1000):
            raise ValueError('Radius must be between 0 and 1000 km')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v

class MediaStorageUsageResponse(BaseModel):
    """Response schema for media storage usage."""
    total_used_bytes: int
    total_limit_bytes: int
    percentage_used: float
    remaining_bytes: int
    file_count: int
    breakdown_by_type: Dict[str, Dict[str, Any]]
    largest_files: List[Dict[str, Any]] = []
    oldest_files: List[Dict[str, Any]] = []
    
class MediaAnalyticsRequest(BaseModel):
    """Schema for media analytics request."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    media_types: Optional[List[MediaType]] = None
    group_by: str = 'day'  # 'hour', 'day', 'week', 'month'
    
    @validator('group_by')
    def validate_group_by(cls, v):
        valid_groups = ['hour', 'day', 'week', 'month']
        if v not in valid_groups:
            raise ValueError(f'Group by must be one of: {valid_groups}')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v

class MediaAnalyticsResponse(BaseModel):
    """Response schema for media analytics."""
    total_uploads: int
    total_downloads: int
    total_storage_used: int
    uploads_by_period: List[Dict[str, Any]] = []
    downloads_by_period: List[Dict[str, Any]] = []
    storage_by_period: List[Dict[str, Any]] = []
    uploads_by_type: Dict[str, int]
    downloads_by_type: Dict[str, int]
    most_downloaded_files: List[Dict[str, Any]] = []
    average_file_size: float
    peak_upload_hour: Optional[int] = None
    peak_download_hour: Optional[int] = None

class MediaBulkAction(BaseModel):
    """Schema for bulk media actions."""
    file_ids: List[UUID]
    action: str  # 'delete', 'update_tags', 'update_visibility', 'mark_emergency'
    parameters: Optional[Dict[str, Any]] = None
    
    @validator('file_ids')
    def validate_file_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one file ID is required')
        if len(v) > 100:
            raise ValueError('Cannot perform bulk action on more than 100 files')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['delete', 'update_tags', 'update_visibility', 'mark_emergency', 'unmark_emergency']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v

class MediaBulkActionResponse(BaseModel):
    """Response schema for bulk media actions."""
    successful_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []
    processed_file_ids: List[UUID]

class MediaExportRequest(BaseModel):
    """Schema for exporting media files."""
    format: str = 'zip'  # 'zip', 'tar', 'json_metadata'
    filters: Optional[MediaSearchRequest] = None
    include_metadata: bool = True
    include_thumbnails: bool = False
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['zip', 'tar', 'json_metadata']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {valid_formats}')
        return v

class MediaExportResponse(BaseModel):
    """Response schema for media export."""
    export_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    file_count: Optional[int] = None
    progress_percentage: Optional[float] = None

class MediaShareRequest(BaseModel):
    """Schema for sharing media files."""
    file_ids: List[UUID]
    share_with: List[str]  # Email addresses or user IDs
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    allow_download: bool = True
    require_authentication: bool = True
    
    @validator('file_ids')
    def validate_file_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one file ID is required')
        if len(v) > 50:
            raise ValueError('Cannot share more than 50 files at once')
        return v
    
    @validator('share_with')
    def validate_share_with(cls, v):
        if len(v) == 0:
            raise ValueError('At least one recipient is required')
        if len(v) > 20:
            raise ValueError('Cannot share with more than 20 recipients')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Message cannot be longer than 500 characters')
        return v

class MediaShareResponse(BaseModel):
    """Response schema for media sharing."""
    share_id: UUID
    share_url: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    access_count: int = 0
    
    class Config:
        from_attributes = True

class MediaProcessingJob(BaseModel):
    """Schema for media processing jobs."""
    file_id: UUID
    job_type: str  # 'thumbnail', 'compress', 'convert', 'extract_metadata'
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 5  # 1-10, higher is more priority
    
    @validator('job_type')
    def validate_job_type(cls, v):
        valid_types = ['thumbnail', 'compress', 'convert', 'extract_metadata', 'virus_scan']
        if v not in valid_types:
            raise ValueError(f'Job type must be one of: {valid_types}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Priority must be between 1 and 10')
        return v

class MediaProcessingJobResponse(BaseModel):
    """Response schema for media processing job."""
    id: UUID
    file_id: UUID
    job_type: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress_percentage: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MediaMetadata(BaseModel):
    """Schema for media metadata."""
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    bitrate: Optional[int] = None
    frame_rate: Optional[float] = None
    codec: Optional[str] = None
    color_space: Optional[str] = None
    orientation: Optional[int] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    date_taken: Optional[datetime] = None
    
class MediaMetadataResponse(BaseModel):
    """Response schema for media metadata."""
    file_id: UUID
    metadata: MediaMetadata
    extracted_at: datetime
    
    class Config:
        from_attributes = True

class MediaVirusScannResult(BaseModel):
    """Schema for virus scan results."""
    file_id: UUID
    is_clean: bool
    threats_found: List[str] = []
    scan_engine: str
    scan_version: str
    scanned_at: datetime
    
    class Config:
        from_attributes = True

class MediaAccessLog(BaseModel):
    """Schema for media access logs."""
    file_id: UUID
    user_id: Optional[UUID] = None
    action: str  # 'view', 'download', 'share', 'delete'
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class MediaAccessLogResponse(BaseModel):
    """Response schema for media access logs."""
    logs: List[MediaAccessLog]
    total: int
    skip: int
    limit: int

class MediaQuotaInfo(BaseModel):
    """Schema for media quota information."""
    user_id: UUID
    total_quota_bytes: int
    used_quota_bytes: int
    remaining_quota_bytes: int
    percentage_used: float
    file_count: int
    max_file_size_bytes: int
    max_files_per_day: int
    files_uploaded_today: int
    quota_reset_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MediaCompressionSettings(BaseModel):
    """Schema for media compression settings."""
    quality: int = 80  # 1-100
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    format: Optional[str] = None  # 'jpeg', 'png', 'webp'
    preserve_metadata: bool = False
    
    @validator('quality')
    def validate_quality(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('Quality must be between 1 and 100')
        return v
    
    @validator('format')
    def validate_format(cls, v):
        if v is not None:
            valid_formats = ['jpeg', 'jpg', 'png', 'webp', 'gif']
            if v.lower() not in valid_formats:
                raise ValueError(f'Format must be one of: {valid_formats}')
        return v

class MediaWatermarkSettings(BaseModel):
    """Schema for media watermark settings."""
    text: Optional[str] = None
    image_url: Optional[str] = None
    position: str = 'bottom_right'  # 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'
    opacity: float = 0.5
    size_percentage: int = 10
    
    @validator('position')
    def validate_position(cls, v):
        valid_positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center']
        if v not in valid_positions:
            raise ValueError(f'Position must be one of: {valid_positions}')
        return v
    
    @validator('opacity')
    def validate_opacity(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Opacity must be between 0.0 and 1.0')
        return v
    
    @validator('size_percentage')
    def validate_size_percentage(cls, v):
        if not 1 <= v <= 50:
            raise ValueError('Size percentage must be between 1 and 50')
        return v

class MediaBackupSettings(BaseModel):
    """Schema for media backup settings."""
    enabled: bool = True
    backup_location: str  # 's3', 'google_drive', 'dropbox', 'local'
    backup_frequency: str = 'daily'  # 'hourly', 'daily', 'weekly'
    retention_days: int = 30
    compress_backups: bool = True
    encrypt_backups: bool = True
    
    @validator('backup_location')
    def validate_backup_location(cls, v):
        valid_locations = ['s3', 'google_drive', 'dropbox', 'local', 'azure']
        if v not in valid_locations:
            raise ValueError(f'Backup location must be one of: {valid_locations}')
        return v
    
    @validator('backup_frequency')
    def validate_backup_frequency(cls, v):
        valid_frequencies = ['hourly', 'daily', 'weekly', 'monthly']
        if v not in valid_frequencies:
            raise ValueError(f'Backup frequency must be one of: {valid_frequencies}')
        return v
    
    @validator('retention_days')
    def validate_retention_days(cls, v):
        if not 1 <= v <= 365:
            raise ValueError('Retention days must be between 1 and 365')
        return v