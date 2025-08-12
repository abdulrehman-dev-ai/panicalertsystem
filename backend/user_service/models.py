from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import uuid

class User(Base):
    """User model for storing user account information."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True))
    
    # Authentication
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255))
    backup_codes = Column(JSON)
    
    # Profile information
    avatar_url = Column(String(500))
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    
    # Location
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    current_address = Column(Text)
    location_updated_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_phone_active', 'phone_number', 'is_active'),
        Index('idx_user_location', 'current_latitude', 'current_longitude'),
        Index('idx_user_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"

class EmergencyContact(Base):
    """Emergency contact model for storing user's emergency contacts."""
    __tablename__ = "emergency_contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255))
    relationship = Column(String(50), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Additional information
    address = Column(Text)
    notes = Column(Text)
    
    # Notification preferences
    notify_on_panic = Column(Boolean, default=True, nullable=False)
    notify_on_geofence = Column(Boolean, default=True, nullable=False)
    notification_method = Column(String(20), default='both')  # 'sms', 'call', 'both'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="emergency_contacts")
    
    # Indexes
    __table_args__ = (
        Index('idx_emergency_contact_user_primary', 'user_id', 'is_primary'),
        Index('idx_emergency_contact_phone', 'phone_number'),
    )
    
    def __repr__(self):
        return f"<EmergencyContact(id={self.id}, name={self.name}, relationship={self.relationship})>"

class UserPreferences(Base):
    """User preferences model for storing user's application preferences."""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Privacy settings
    silent_mode = Column(Boolean, default=False, nullable=False)
    auto_location_sharing = Column(Boolean, default=True, nullable=False)
    location_sharing_accuracy = Column(String(20), default='precise')  # 'precise', 'approximate'
    
    # Notification preferences
    emergency_contacts_notification = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    sms_notifications = Column(Boolean, default=True, nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    
    # Alert preferences
    panic_button_confirmation = Column(Boolean, default=True, nullable=False)
    auto_emergency_call = Column(Boolean, default=False, nullable=False)
    emergency_call_delay_seconds = Column(Integer, default=30)
    
    # Geofencing preferences
    geofence_notifications = Column(Boolean, default=True, nullable=False)
    geofence_sound_alerts = Column(Boolean, default=True, nullable=False)
    
    # Media preferences
    auto_backup_media = Column(Boolean, default=True, nullable=False)
    compress_media_uploads = Column(Boolean, default=True, nullable=False)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5))  # Format: "HH:MM"
    quiet_hours_end = Column(String(5))    # Format: "HH:MM"
    
    # Data retention
    data_retention_days = Column(Integer, default=365, nullable=False)
    auto_delete_old_alerts = Column(Boolean, default=False, nullable=False)
    
    # Advanced settings
    analytics_participation = Column(Boolean, default=True, nullable=False)
    crash_reporting = Column(Boolean, default=True, nullable=False)
    beta_features = Column(Boolean, default=False, nullable=False)
    
    # Custom settings (JSON)
    custom_settings = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"

class UserDevice(Base):
    """User device model for storing information about user's devices."""
    __tablename__ = "user_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    device_id = Column(String(255), nullable=False, index=True)
    device_name = Column(String(100))
    device_type = Column(String(20), nullable=False)  # 'mobile', 'web', 'tablet', 'desktop'
    platform = Column(String(20), nullable=False)     # 'ios', 'android', 'web', 'windows', 'macos', 'linux'
    
    # App information
    app_version = Column(String(20))
    os_version = Column(String(50))
    
    # Push notification token
    push_token = Column(String(500))
    push_token_updated_at = Column(DateTime(timezone=True))
    
    # Device status
    is_active = Column(Boolean, default=True, nullable=False)
    is_trusted = Column(Boolean, default=False, nullable=False)
    
    # Location permissions
    location_permission = Column(String(20))  # 'granted', 'denied', 'prompt'
    background_location_permission = Column(String(20))
    
    # Activity tracking
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_ip_address = Column(String(45))
    last_user_agent = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="devices")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_device_unique', 'user_id', 'device_id', unique=True),
        Index('idx_user_device_active', 'user_id', 'is_active'),
        Index('idx_device_push_token', 'push_token'),
        Index('idx_device_last_seen', 'last_seen'),
    )
    
    def __repr__(self):
        return f"<UserDevice(id={self.id}, device_id={self.device_id}, platform={self.platform})>"

class UserSession(Base):
    """User session model for tracking active user sessions."""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("user_devices.id", ondelete="CASCADE"), index=True)
    
    # Session information
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location = Column(String(100))  # City, Country
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    device = relationship("UserDevice")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_last_activity', 'last_activity'),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

class APIKey(Base):
    """API key model for storing user API keys."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # First few characters for identification
    
    # Permissions
    permissions = Column(JSON, nullable=False)  # List of permissions
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True))
    last_ip_address = Column(String(45))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_user_active', 'user_id', 'is_active'),
        Index('idx_api_key_expires', 'expires_at'),
        Index('idx_api_key_last_used', 'last_used'),
    )
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"

class UserActivity(Base):
    """User activity model for tracking user actions and events."""
    __tablename__ = "user_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    activity_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Context information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_id = Column(String(255))
    
    # Additional metadata
    metadata = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_user_type', 'user_id', 'activity_type'),
        Index('idx_activity_timestamp', 'timestamp'),
        Index('idx_activity_type_timestamp', 'activity_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, type={self.activity_type}, user_id={self.user_id})>"

class UserLocation(Base):
    """User location model for storing location history."""
    __tablename__ = "user_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)  # Accuracy in meters
    altitude = Column(Float)
    speed = Column(Float)     # Speed in m/s
    heading = Column(Float)   # Heading in degrees
    
    # Address information
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Metadata
    source = Column(String(20), default='app')  # 'app', 'gps', 'network', 'passive'
    battery_level = Column(Integer)  # Battery level when location was recorded
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_location_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_location_coordinates', 'latitude', 'longitude'),
        Index('idx_location_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<UserLocation(id={self.id}, user_id={self.user_id}, lat={self.latitude}, lng={self.longitude})>"