from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, JSON, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import uuid
import enum

class AlertType(enum.Enum):
    """Alert type enumeration."""
    PANIC = "panic"
    MEDICAL = "medical"
    FIRE = "fire"
    POLICE = "police"
    GEOFENCE = "geofence"
    TEST = "test"
    CUSTOM = "custom"

class AlertStatus(enum.Enum):
    """Alert status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    FALSE_ALARM = "false_alarm"

class AlertPriority(enum.Enum):
    """Alert priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Alert(Base):
    """Alert model for storing emergency alerts and incidents."""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Reference to user service
    
    # Alert classification
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    priority = Column(Enum(AlertPriority), default=AlertPriority.HIGH, nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.PENDING, nullable=False, index=True)
    
    # Alert content
    title = Column(String(200), nullable=False)
    message = Column(Text)
    
    # Location information
    latitude = Column(Float)
    longitude = Column(Float)
    accuracy = Column(Float)  # Location accuracy in meters
    address = Column(Text)
    
    # Timing information
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Response information
    acknowledged_by = Column(UUID(as_uuid=True))  # User or agent who acknowledged
    resolved_by = Column(UUID(as_uuid=True))     # User or agent who resolved
    resolution_notes = Column(Text)
    
    # Test alert information
    is_test = Column(Boolean, default=False, nullable=False, index=True)
    test_type = Column(String(50))  # 'manual', 'scheduled', 'system'
    
    # Escalation information
    escalation_level = Column(Integer, default=0, nullable=False)
    escalated_at = Column(DateTime(timezone=True))
    auto_escalate = Column(Boolean, default=True, nullable=False)
    
    # Device and context information
    device_id = Column(String(255))
    battery_level = Column(Integer)
    network_type = Column(String(20))  # 'wifi', 'cellular', 'offline'
    
    # Additional metadata
    metadata = Column(JSON)  # Additional context data
    tags = Column(JSON)      # Tags for categorization
    
    # External references
    external_incident_id = Column(String(100))  # Reference to external emergency services
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    timeline_events = relationship("AlertTimelineEvent", back_populates="alert", cascade="all, delete-orphan")
    notifications = relationship("AlertNotification", back_populates="alert", cascade="all, delete-orphan")
    media_files = relationship("AlertMediaFile", back_populates="alert", cascade="all, delete-orphan")
    escalations = relationship("AlertEscalation", back_populates="alert", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_alert_user_status', 'user_id', 'status'),
        Index('idx_alert_type_priority', 'alert_type', 'priority'),
        Index('idx_alert_triggered_at', 'triggered_at'),
        Index('idx_alert_location', 'latitude', 'longitude'),
        Index('idx_alert_test', 'is_test', 'triggered_at'),
        Index('idx_alert_escalation', 'escalation_level', 'escalated_at'),
    )
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type.value}, status={self.status.value}, user_id={self.user_id})>"

class AlertTimelineEvent(Base):
    """Alert timeline event model for tracking alert progression."""
    __tablename__ = "alert_timeline_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Actor information
    actor_id = Column(UUID(as_uuid=True))  # User or agent who performed the action
    actor_type = Column(String(20))        # 'user', 'agent', 'system'
    
    # Event metadata
    metadata = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    alert = relationship("Alert", back_populates="timeline_events")
    
    # Indexes
    __table_args__ = (
        Index('idx_timeline_alert_timestamp', 'alert_id', 'timestamp'),
        Index('idx_timeline_event_type', 'event_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AlertTimelineEvent(id={self.id}, alert_id={self.alert_id}, type={self.event_type})>"

class AlertNotification(Base):
    """Alert notification model for tracking sent notifications."""
    __tablename__ = "alert_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(20), nullable=False, index=True)  # 'sms', 'email', 'push', 'call'
    recipient_type = Column(String(20), nullable=False)  # 'user', 'emergency_contact', 'authority'
    recipient_id = Column(UUID(as_uuid=True))  # ID of the recipient
    recipient_identifier = Column(String(255), nullable=False)  # Phone, email, etc.
    
    # Message content
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    
    # Delivery status
    status = Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'sent', 'delivered', 'failed'
    delivery_attempts = Column(Integer, default=0, nullable=False)
    
    # Response tracking
    response_received = Column(Boolean, default=False, nullable=False)
    response_content = Column(Text)
    response_timestamp = Column(DateTime(timezone=True))
    
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
    alert = relationship("Alert", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_alert_type', 'alert_id', 'notification_type'),
        Index('idx_notification_status', 'status', 'created_at'),
        Index('idx_notification_recipient', 'recipient_type', 'recipient_id'),
        Index('idx_notification_delivery', 'delivery_attempts', 'status'),
    )
    
    def __repr__(self):
        return f"<AlertNotification(id={self.id}, alert_id={self.alert_id}, type={self.notification_type}, status={self.status})>"

class AlertMediaFile(Base):
    """Alert media file model for storing media associated with alerts."""
    __tablename__ = "alert_media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False, index=True)  # 'image', 'video', 'audio', 'document'
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Storage information
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500))
    thumbnail_url = Column(String(500))
    
    # File metadata
    duration = Column(Float)  # For audio/video files
    dimensions = Column(JSON) # For images/videos: {"width": 1920, "height": 1080}
    
    # Processing status
    processing_status = Column(String(20), default='pending', nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    processing_error = Column(Text)
    
    # Security
    is_encrypted = Column(Boolean, default=False, nullable=False)
    encryption_key_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    alert = relationship("Alert", back_populates="media_files")
    
    # Indexes
    __table_args__ = (
        Index('idx_media_alert_type', 'alert_id', 'file_type'),
        Index('idx_media_processing', 'processing_status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AlertMediaFile(id={self.id}, alert_id={self.alert_id}, file_name={self.file_name})>"

class AlertEscalation(Base):
    """Alert escalation model for tracking escalation rules and actions."""
    __tablename__ = "alert_escalations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Escalation details
    escalation_level = Column(Integer, nullable=False, index=True)
    escalation_type = Column(String(50), nullable=False)  # 'time_based', 'manual', 'no_response'
    
    # Trigger conditions
    trigger_delay_minutes = Column(Integer)  # Minutes after alert creation
    trigger_condition = Column(String(100))  # Condition that triggered escalation
    
    # Actions taken
    actions_taken = Column(JSON, nullable=False)  # List of escalation actions
    
    # Status
    status = Column(String(20), default='pending', nullable=False)  # 'pending', 'executed', 'cancelled'
    
    # Execution details
    executed_by = Column(UUID(as_uuid=True))  # System or user who executed
    execution_notes = Column(Text)
    
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    alert = relationship("Alert", back_populates="escalations")
    
    # Indexes
    __table_args__ = (
        Index('idx_escalation_alert_level', 'alert_id', 'escalation_level'),
        Index('idx_escalation_scheduled', 'scheduled_at', 'status'),
        Index('idx_escalation_status', 'status', 'scheduled_at'),
    )
    
    def __repr__(self):
        return f"<AlertEscalation(id={self.id}, alert_id={self.alert_id}, level={self.escalation_level})>"

class AlertTemplate(Base):
    """Alert template model for predefined alert configurations."""
    __tablename__ = "alert_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Template information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    priority = Column(Enum(AlertPriority), nullable=False)
    
    # Template content
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text)
    
    # Configuration
    auto_escalate = Column(Boolean, default=True, nullable=False)
    escalation_rules = Column(JSON)  # Escalation configuration
    notification_rules = Column(JSON)  # Notification configuration
    
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
        Index('idx_template_type_active', 'alert_type', 'is_active'),
        Index('idx_template_usage', 'usage_count', 'last_used'),
    )
    
    def __repr__(self):
        return f"<AlertTemplate(id={self.id}, name={self.name}, type={self.alert_type.value})>"

class AlertMetrics(Base):
    """Alert metrics model for storing aggregated alert statistics."""
    __tablename__ = "alert_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Metric period
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly', 'monthly'
    
    # User or system metrics
    user_id = Column(UUID(as_uuid=True), index=True)  # NULL for system-wide metrics
    
    # Alert counts by type
    panic_alerts = Column(Integer, default=0, nullable=False)
    medical_alerts = Column(Integer, default=0, nullable=False)
    fire_alerts = Column(Integer, default=0, nullable=False)
    police_alerts = Column(Integer, default=0, nullable=False)
    geofence_alerts = Column(Integer, default=0, nullable=False)
    test_alerts = Column(Integer, default=0, nullable=False)
    custom_alerts = Column(Integer, default=0, nullable=False)
    
    # Alert counts by status
    pending_alerts = Column(Integer, default=0, nullable=False)
    active_alerts = Column(Integer, default=0, nullable=False)
    acknowledged_alerts = Column(Integer, default=0, nullable=False)
    resolved_alerts = Column(Integer, default=0, nullable=False)
    cancelled_alerts = Column(Integer, default=0, nullable=False)
    false_alarms = Column(Integer, default=0, nullable=False)
    
    # Response time metrics (in seconds)
    avg_acknowledgment_time = Column(Float)
    avg_resolution_time = Column(Float)
    
    # Escalation metrics
    escalated_alerts = Column(Integer, default=0, nullable=False)
    avg_escalation_time = Column(Float)
    
    # Additional metrics
    total_alerts = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_date_type', 'metric_date', 'metric_type'),
        Index('idx_metrics_user_date', 'user_id', 'metric_date'),
        Index('idx_metrics_type_user', 'metric_type', 'user_id'),
    )
    
    def __repr__(self):
        return f"<AlertMetrics(id={self.id}, date={self.metric_date}, type={self.metric_type}, user_id={self.user_id})>"