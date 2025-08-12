from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, JSON, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import uuid
import enum

class GeofenceType(enum.Enum):
    """Geofence type enumeration."""
    SAFE_ZONE = "safe_zone"
    RESTRICTED_ZONE = "restricted_zone"
    WORK_ZONE = "work_zone"
    HOME_ZONE = "home_zone"
    SCHOOL_ZONE = "school_zone"
    EMERGENCY_ZONE = "emergency_zone"
    CUSTOM = "custom"

class GeofenceStatus(enum.Enum):
    """Geofence status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    EXPIRED = "expired"

class GeofenceShape(enum.Enum):
    """Geofence shape enumeration."""
    CIRCLE = "circle"
    POLYGON = "polygon"
    RECTANGLE = "rectangle"

class GeofenceEventType(enum.Enum):
    """Geofence event type enumeration."""
    ENTER = "enter"
    EXIT = "exit"
    DWELL = "dwell"
    BREACH = "breach"

class Geofence(Base):
    """Geofence model for storing geofence definitions."""
    __tablename__ = "geofences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Reference to user service
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(Text)
    geofence_type = Column(Enum(GeofenceType), nullable=False, index=True)
    status = Column(Enum(GeofenceStatus), default=GeofenceStatus.ACTIVE, nullable=False, index=True)
    
    # Geometry
    shape = Column(Enum(GeofenceShape), nullable=False)
    coordinates = Column(JSON, nullable=False)  # Coordinates based on shape
    radius = Column(Float)  # For circle geofences (in meters)
    
    # Center point (for indexing and quick distance calculations)
    center_latitude = Column(Float, nullable=False, index=True)
    center_longitude = Column(Float, nullable=False, index=True)
    
    # Address information
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Behavior settings
    trigger_on_enter = Column(Boolean, default=True, nullable=False)
    trigger_on_exit = Column(Boolean, default=True, nullable=False)
    trigger_on_dwell = Column(Boolean, default=False, nullable=False)
    dwell_time_minutes = Column(Integer, default=5)  # Minutes to trigger dwell event
    
    # Notification settings
    notify_user = Column(Boolean, default=True, nullable=False)
    notify_emergency_contacts = Column(Boolean, default=False, nullable=False)
    notification_message = Column(Text)
    
    # Schedule settings
    is_scheduled = Column(Boolean, default=False, nullable=False)
    schedule_config = Column(JSON)  # Schedule configuration
    
    # Validity period
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    
    # Monitoring settings
    monitoring_enabled = Column(Boolean, default=True, nullable=False)
    sensitivity_level = Column(String(20), default='medium')  # 'low', 'medium', 'high'
    
    # Statistics
    total_entries = Column(Integer, default=0, nullable=False)
    total_exits = Column(Integer, default=0, nullable=False)
    total_dwells = Column(Integer, default=0, nullable=False)
    last_triggered = Column(DateTime(timezone=True))
    
    # Metadata
    tags = Column(JSON)  # Tags for categorization
    metadata = Column(JSON)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    events = relationship("GeofenceEvent", back_populates="geofence", cascade="all, delete-orphan")
    notifications = relationship("GeofenceNotification", back_populates="geofence", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_geofence_user_status', 'user_id', 'status'),
        Index('idx_geofence_type_status', 'geofence_type', 'status'),
        Index('idx_geofence_center', 'center_latitude', 'center_longitude'),
        Index('idx_geofence_validity', 'valid_from', 'valid_until'),
        Index('idx_geofence_monitoring', 'monitoring_enabled', 'status'),
    )
    
    def __repr__(self):
        return f"<Geofence(id={self.id}, name={self.name}, type={self.geofence_type.value}, user_id={self.user_id})>"

class GeofenceEvent(Base):
    """Geofence event model for storing geofence trigger events."""
    __tablename__ = "geofence_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    geofence_id = Column(UUID(as_uuid=True), ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event details
    event_type = Column(Enum(GeofenceEventType), nullable=False, index=True)
    
    # Location information
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)  # Location accuracy in meters
    
    # Distance from geofence boundary
    distance_from_boundary = Column(Float)  # Distance in meters (negative = inside, positive = outside)
    
    # Device information
    device_id = Column(String(255))
    battery_level = Column(Integer)
    network_type = Column(String(20))  # 'wifi', 'cellular', 'offline'
    
    # Timing information
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    dwell_duration_minutes = Column(Integer)  # For dwell events
    
    # Processing information
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)
    
    # Notification status
    notifications_sent = Column(Boolean, default=False, nullable=False)
    notification_count = Column(Integer, default=0, nullable=False)
    
    # Additional context
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    geofence = relationship("Geofence", back_populates="events")
    notifications = relationship("GeofenceNotification", back_populates="event", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_geofence_type', 'geofence_id', 'event_type'),
        Index('idx_event_user_timestamp', 'user_id', 'event_timestamp'),
        Index('idx_event_timestamp', 'event_timestamp'),
        Index('idx_event_processed', 'processed', 'created_at'),
        Index('idx_event_location', 'latitude', 'longitude'),
    )
    
    def __repr__(self):
        return f"<GeofenceEvent(id={self.id}, geofence_id={self.geofence_id}, type={self.event_type.value})>"

class GeofenceNotification(Base):
    """Geofence notification model for tracking sent notifications."""
    __tablename__ = "geofence_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    geofence_id = Column(UUID(as_uuid=True), ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("geofence_events.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(20), nullable=False, index=True)  # 'sms', 'email', 'push', 'call'
    recipient_type = Column(String(20), nullable=False)  # 'user', 'emergency_contact'
    recipient_id = Column(UUID(as_uuid=True))  # ID of the recipient
    recipient_identifier = Column(String(255), nullable=False)  # Phone, email, etc.
    
    # Message content
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    
    # Delivery status
    status = Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'sent', 'delivered', 'failed'
    delivery_attempts = Column(Integer, default=0, nullable=False)
    
    # External references
    external_message_id = Column(String(255))  # Provider's message ID
    provider = Column(String(50))              # 'twilio', 'sendgrid', 'fcm', etc.
    
    # Error information
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Relationships
    geofence = relationship("Geofence", back_populates="notifications")
    event = relationship("GeofenceEvent", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_geofence_type', 'geofence_id', 'notification_type'),
        Index('idx_notification_event_status', 'event_id', 'status'),
        Index('idx_notification_status', 'status', 'created_at'),
        Index('idx_notification_recipient', 'recipient_type', 'recipient_id'),
    )
    
    def __repr__(self):
        return f"<GeofenceNotification(id={self.id}, geofence_id={self.geofence_id}, type={self.notification_type})>"

class GeofenceTemplate(Base):
    """Geofence template model for predefined geofence configurations."""
    __tablename__ = "geofence_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Template information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)  # 'safety', 'work', 'family', 'custom'
    geofence_type = Column(Enum(GeofenceType), nullable=False, index=True)
    
    # Default configuration
    default_shape = Column(Enum(GeofenceShape), nullable=False)
    default_radius = Column(Float)  # Default radius for circle templates
    default_settings = Column(JSON, nullable=False)  # Default geofence settings
    
    # Template metadata
    icon = Column(String(100))  # Icon identifier
    color = Column(String(7))   # Hex color code
    tags = Column(JSON)         # Template tags
    
    # Availability
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_template = Column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_template_category_active', 'category', 'is_active'),
        Index('idx_template_type_active', 'geofence_type', 'is_active'),
        Index('idx_template_usage', 'usage_count', 'last_used'),
    )
    
    def __repr__(self):
        return f"<GeofenceTemplate(id={self.id}, name={self.name}, category={self.category})>"

class GeofenceAnalytics(Base):
    """Geofence analytics model for storing aggregated geofence statistics."""
    __tablename__ = "geofence_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Analytics period
    analytics_date = Column(DateTime(timezone=True), nullable=False, index=True)
    analytics_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly', 'monthly'
    
    # Scope
    user_id = Column(UUID(as_uuid=True), index=True)  # NULL for system-wide analytics
    geofence_id = Column(UUID(as_uuid=True), index=True)  # NULL for user-wide analytics
    
    # Event counts
    total_events = Column(Integer, default=0, nullable=False)
    enter_events = Column(Integer, default=0, nullable=False)
    exit_events = Column(Integer, default=0, nullable=False)
    dwell_events = Column(Integer, default=0, nullable=False)
    breach_events = Column(Integer, default=0, nullable=False)
    
    # Timing analytics
    avg_dwell_time_minutes = Column(Float)
    max_dwell_time_minutes = Column(Float)
    total_time_inside_minutes = Column(Float)
    
    # Frequency analytics
    unique_entries = Column(Integer, default=0, nullable=False)
    most_active_hour = Column(Integer)  # Hour of day (0-23)
    most_active_day = Column(Integer)   # Day of week (0-6)
    
    # Notification analytics
    notifications_sent = Column(Integer, default=0, nullable=False)
    notification_success_rate = Column(Float)
    
    # Performance metrics
    avg_processing_time_ms = Column(Float)
    processing_errors = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_date_type', 'analytics_date', 'analytics_type'),
        Index('idx_analytics_user_date', 'user_id', 'analytics_date'),
        Index('idx_analytics_geofence_date', 'geofence_id', 'analytics_date'),
    )
    
    def __repr__(self):
        return f"<GeofenceAnalytics(id={self.id}, date={self.analytics_date}, type={self.analytics_type})>"

class GeofenceImportJob(Base):
    """Geofence import job model for tracking bulk geofence imports."""
    __tablename__ = "geofence_import_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Job information
    job_name = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_format = Column(String(20), nullable=False)  # 'csv', 'json', 'kml', 'gpx'
    
    # Processing status
    status = Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'processing', 'completed', 'failed'
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # Results
    total_records = Column(Integer, default=0, nullable=False)
    processed_records = Column(Integer, default=0, nullable=False)
    successful_imports = Column(Integer, default=0, nullable=False)
    failed_imports = Column(Integer, default=0, nullable=False)
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)  # Detailed error information
    
    # File paths
    input_file_path = Column(String(500), nullable=False)
    error_file_path = Column(String(500))  # Path to error report file
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_import_user_status', 'user_id', 'status'),
        Index('idx_import_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<GeofenceImportJob(id={self.id}, name={self.job_name}, status={self.status})>"

class GeofenceShare(Base):
    """Geofence share model for sharing geofences between users."""
    __tablename__ = "geofence_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    geofence_id = Column(UUID(as_uuid=True), ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    shared_with_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Share permissions
    can_view = Column(Boolean, default=True, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_share = Column(Boolean, default=False, nullable=False)
    
    # Share status
    status = Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'accepted', 'declined', 'revoked'
    
    # Share metadata
    share_message = Column(Text)
    share_expiry = Column(DateTime(timezone=True))
    
    # Response tracking
    responded_at = Column(DateTime(timezone=True))
    response_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    geofence = relationship("Geofence")
    
    # Indexes
    __table_args__ = (
        Index('idx_share_geofence_status', 'geofence_id', 'status'),
        Index('idx_share_owner_shared', 'owner_user_id', 'shared_with_user_id'),
        Index('idx_share_shared_with', 'shared_with_user_id', 'status'),
        Index('idx_share_expiry', 'share_expiry', 'status'),
    )
    
    def __repr__(self):
        return f"<GeofenceShare(id={self.id}, geofence_id={self.geofence_id}, status={self.status})>"