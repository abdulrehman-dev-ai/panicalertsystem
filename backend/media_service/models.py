from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, JSON, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import uuid
import enum

class MediaType(enum.Enum):
    """Media type enumeration."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"

class MediaStatus(enum.Enum):
    """Media status enumeration."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    AVAILABLE = "available"
    FAILED = "failed"
    DELETED = "deleted"
    QUARANTINED = "quarantined"

class MediaVisibility(enum.Enum):
    """Media visibility enumeration."""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"

class MediaFile(Base):
    """Media file model for storing uploaded media files."""
    __tablename__ = "media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Reference to user service
    
    # File information
    original_filename = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False, index=True)
    file_extension = Column(String(10), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False, index=True)
    file_size = Column(Integer, nullable=False, index=True)
    
    # Media classification
    media_type = Column(Enum(MediaType), nullable=False, index=True)
    status = Column(Enum(MediaStatus), default=MediaStatus.UPLOADING, nullable=False, index=True)
    visibility = Column(Enum(MediaVisibility), default=MediaVisibility.PRIVATE, nullable=False, index=True)
    
    # Storage information
    storage_path = Column(String(500), nullable=False)
    storage_bucket = Column(String(100))
    storage_region = Column(String(50))
    cdn_url = Column(String(500))
    
    # File metadata
    width = Column(Integer)  # For images and videos
    height = Column(Integer)  # For images and videos
    duration = Column(Float)  # For audio and video files (in seconds)
    bitrate = Column(Integer)  # For audio and video files
    frame_rate = Column(Float)  # For video files
    
    # Content information
    title = Column(String(200))
    description = Column(Text)
    tags = Column(JSON)  # Array of tags
    
    # Location information (EXIF data or manual)
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String(200))
    
    # Processing information
    processing_status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processing_progress = Column(Integer, default=0)  # 0-100
    processing_error = Column(Text)
    
    # Thumbnails and previews
    thumbnail_path = Column(String(500))
    thumbnail_url = Column(String(500))
    preview_path = Column(String(500))
    preview_url = Column(String(500))
    
    # Security and compliance
    is_encrypted = Column(Boolean, default=False, nullable=False)
    encryption_key_id = Column(String(255))
    virus_scan_status = Column(String(20), default='pending')  # 'pending', 'clean', 'infected', 'failed'
    virus_scan_result = Column(JSON)
    
    # Access control
    is_public = Column(Boolean, default=False, nullable=False)
    access_token = Column(String(255), unique=True, index=True)  # For secure access
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    
    # Backup and archival
    is_backed_up = Column(Boolean, default=False, nullable=False)
    backup_path = Column(String(500))
    backup_timestamp = Column(DateTime(timezone=True))
    
    # Content moderation
    moderation_status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected', 'flagged'
    moderation_score = Column(Float)  # 0.0 to 1.0
    moderation_labels = Column(JSON)  # AI-generated content labels
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    auto_delete = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True))
    
    # Relationships
    shares = relationship("MediaShare", back_populates="media_file", cascade="all, delete-orphan")
    access_logs = relationship("MediaAccessLog", back_populates="media_file", cascade="all, delete-orphan")
    processing_jobs = relationship("MediaProcessingJob", back_populates="media_file", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_media_user_type', 'user_id', 'media_type'),
        Index('idx_media_user_status', 'user_id', 'status'),
        Index('idx_media_type_status', 'media_type', 'status'),
        Index('idx_media_created_at', 'created_at'),
        Index('idx_media_size', 'file_size'),
        Index('idx_media_location', 'latitude', 'longitude'),
        Index('idx_media_expires', 'expires_at', 'auto_delete'),
        Index('idx_media_backup', 'is_backed_up', 'backup_timestamp'),
    )
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename={self.filename}, type={self.media_type.value}, user_id={self.user_id})>"

class MediaShare(Base):
    """Media share model for sharing media files between users."""
    __tablename__ = "media_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    shared_with_user_id = Column(UUID(as_uuid=True), index=True)  # NULL for public shares
    
    # Share configuration
    share_token = Column(String(255), unique=True, nullable=False, index=True)
    share_type = Column(String(20), nullable=False)  # 'user', 'public', 'link'
    
    # Permissions
    can_view = Column(Boolean, default=True, nullable=False)
    can_download = Column(Boolean, default=True, nullable=False)
    can_share = Column(Boolean, default=False, nullable=False)
    
    # Access restrictions
    max_downloads = Column(Integer)  # NULL for unlimited
    max_views = Column(Integer)      # NULL for unlimited
    password_protected = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255))
    
    # Tracking
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime(timezone=True))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    share_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    media_file = relationship("MediaFile", back_populates="shares")
    
    # Indexes
    __table_args__ = (
        Index('idx_share_media_active', 'media_file_id', 'is_active'),
        Index('idx_share_owner_shared', 'owner_user_id', 'shared_with_user_id'),
        Index('idx_share_expires', 'expires_at', 'is_active'),
        Index('idx_share_type_active', 'share_type', 'is_active'),
    )
    
    def __repr__(self):
        return f"<MediaShare(id={self.id}, media_file_id={self.media_file_id}, type={self.share_type})>"

class MediaAccessLog(Base):
    """Media access log model for tracking file access."""
    __tablename__ = "media_access_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), index=True)  # NULL for anonymous access
    
    # Access details
    access_type = Column(String(20), nullable=False, index=True)  # 'view', 'download', 'share', 'delete'
    access_method = Column(String(20), nullable=False)  # 'direct', 'share_link', 'api'
    
    # Request information
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text)
    referer = Column(String(500))
    
    # Response information
    response_status = Column(Integer, nullable=False)  # HTTP status code
    bytes_transferred = Column(Integer, default=0)
    
    # Geolocation (optional)
    country = Column(String(100))
    city = Column(String(100))
    
    # Share context (if accessed via share)
    share_id = Column(UUID(as_uuid=True), ForeignKey("media_shares.id", ondelete="SET NULL"))
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    media_file = relationship("MediaFile", back_populates="access_logs")
    share = relationship("MediaShare")
    
    # Indexes
    __table_args__ = (
        Index('idx_access_media_timestamp', 'media_file_id', 'timestamp'),
        Index('idx_access_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_access_type_timestamp', 'access_type', 'timestamp'),
        Index('idx_access_ip_timestamp', 'ip_address', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MediaAccessLog(id={self.id}, media_file_id={self.media_file_id}, type={self.access_type})>"

class MediaProcessingJob(Base):
    """Media processing job model for tracking media processing tasks."""
    __tablename__ = "media_processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Job information
    job_type = Column(String(50), nullable=False, index=True)  # 'thumbnail', 'transcode', 'compress', 'watermark'
    job_name = Column(String(100), nullable=False)
    job_parameters = Column(JSON, nullable=False)
    
    # Processing status
    status = Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'processing', 'completed', 'failed', 'cancelled'
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # Priority and scheduling
    priority = Column(Integer, default=5, nullable=False)  # 1-10, higher is more priority
    scheduled_at = Column(DateTime(timezone=True))
    
    # Processing details
    worker_id = Column(String(100))  # ID of the worker processing the job
    processing_node = Column(String(100))  # Processing server/node
    
    # Results
    output_files = Column(JSON)  # List of generated output files
    processing_time_seconds = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    media_file = relationship("MediaFile", back_populates="processing_jobs")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_media_status', 'media_file_id', 'status'),
        Index('idx_job_type_status', 'job_type', 'status'),
        Index('idx_job_priority_scheduled', 'priority', 'scheduled_at'),
        Index('idx_job_status_created', 'status', 'created_at'),
        Index('idx_job_worker', 'worker_id', 'status'),
    )
    
    def __repr__(self):
        return f"<MediaProcessingJob(id={self.id}, type={self.job_type}, status={self.status})>"

class MediaCollection(Base):
    """Media collection model for organizing media files into collections."""
    __tablename__ = "media_collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Collection information
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Collection settings
    is_public = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    tags = Column(JSON)  # Array of tags
    cover_media_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="SET NULL"))
    
    # Statistics
    media_count = Column(Integer, default=0, nullable=False)
    total_size_bytes = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    cover_media = relationship("MediaFile", foreign_keys=[cover_media_id])
    collection_items = relationship("MediaCollectionItem", back_populates="collection", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_collection_user_public', 'user_id', 'is_public'),
        Index('idx_collection_featured', 'is_featured', 'created_at'),
        Index('idx_collection_name', 'name'),
    )
    
    def __repr__(self):
        return f"<MediaCollection(id={self.id}, name={self.name}, user_id={self.user_id})>"

class MediaCollectionItem(Base):
    """Media collection item model for linking media files to collections."""
    __tablename__ = "media_collection_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("media_collections.id", ondelete="CASCADE"), nullable=False, index=True)
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Item metadata
    sort_order = Column(Integer, default=0, nullable=False)
    caption = Column(Text)
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    collection = relationship("MediaCollection", back_populates="collection_items")
    media_file = relationship("MediaFile")
    
    # Indexes
    __table_args__ = (
        Index('idx_collection_item_unique', 'collection_id', 'media_file_id', unique=True),
        Index('idx_collection_item_order', 'collection_id', 'sort_order'),
    )
    
    def __repr__(self):
        return f"<MediaCollectionItem(id={self.id}, collection_id={self.collection_id}, media_file_id={self.media_file_id})>"

class MediaAnalytics(Base):
    """Media analytics model for storing aggregated media statistics."""
    __tablename__ = "media_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Analytics period
    analytics_date = Column(DateTime(timezone=True), nullable=False, index=True)
    analytics_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly', 'monthly'
    
    # Scope
    user_id = Column(UUID(as_uuid=True), index=True)  # NULL for system-wide analytics
    
    # Upload statistics
    total_uploads = Column(Integer, default=0, nullable=False)
    total_upload_size_bytes = Column(Integer, default=0, nullable=False)
    image_uploads = Column(Integer, default=0, nullable=False)
    video_uploads = Column(Integer, default=0, nullable=False)
    audio_uploads = Column(Integer, default=0, nullable=False)
    document_uploads = Column(Integer, default=0, nullable=False)
    
    # Access statistics
    total_views = Column(Integer, default=0, nullable=False)
    total_downloads = Column(Integer, default=0, nullable=False)
    unique_viewers = Column(Integer, default=0, nullable=False)
    
    # Storage statistics
    total_storage_used_bytes = Column(Integer, default=0, nullable=False)
    total_bandwidth_used_bytes = Column(Integer, default=0, nullable=False)
    
    # Processing statistics
    processing_jobs_completed = Column(Integer, default=0, nullable=False)
    processing_jobs_failed = Column(Integer, default=0, nullable=False)
    avg_processing_time_seconds = Column(Float)
    
    # Popular content
    most_viewed_media_id = Column(UUID(as_uuid=True))
    most_downloaded_media_id = Column(UUID(as_uuid=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_date_type', 'analytics_date', 'analytics_type'),
        Index('idx_analytics_user_date', 'user_id', 'analytics_date'),
    )
    
    def __repr__(self):
        return f"<MediaAnalytics(id={self.id}, date={self.analytics_date}, type={self.analytics_type}, user_id={self.user_id})>"

class MediaQuota(Base):
    """Media quota model for tracking user storage quotas."""
    __tablename__ = "media_quotas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Quota limits (in bytes)
    storage_quota_bytes = Column(Integer, nullable=False)
    bandwidth_quota_bytes = Column(Integer, nullable=False)  # Monthly bandwidth
    
    # Current usage (in bytes)
    storage_used_bytes = Column(Integer, default=0, nullable=False)
    bandwidth_used_bytes = Column(Integer, default=0, nullable=False)
    
    # File count limits
    max_files = Column(Integer)
    current_file_count = Column(Integer, default=0, nullable=False)
    
    # Reset periods
    bandwidth_reset_date = Column(DateTime(timezone=True), nullable=False)
    
    # Quota status
    is_exceeded = Column(Boolean, default=False, nullable=False)
    warning_sent = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_quota_exceeded', 'is_exceeded', 'updated_at'),
        Index('idx_quota_reset', 'bandwidth_reset_date'),
    )
    
    def __repr__(self):
        return f"<MediaQuota(id={self.id}, user_id={self.user_id}, storage_used={self.storage_used_bytes})>"