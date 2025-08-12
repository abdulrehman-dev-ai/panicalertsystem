from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, JSON, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import uuid
import enum

class AgentType(enum.Enum):
    """Agent type enumeration."""
    EMERGENCY_RESPONDER = "emergency_responder"
    POLICE = "police"
    FIRE_DEPARTMENT = "fire_department"
    MEDICAL = "medical"
    SECURITY = "security"
    DISPATCHER = "dispatcher"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class AgentStatus(enum.Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    BUSY = "busy"
    SUSPENDED = "suspended"

class IncidentStatus(enum.Enum):
    """Incident status enumeration."""
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    TRANSFERRED = "transferred"

class Agent(Base):
    """Agent model for emergency responders and authorities."""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Basic information
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    badge_number = Column(String(50), unique=True, index=True)
    employee_id = Column(String(50), unique=True, index=True)
    
    # Professional information
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    rank = Column(String(50))
    specializations = Column(JSON)  # Array of specializations
    certifications = Column(JSON)  # Array of certifications
    
    # Contact information
    radio_call_sign = Column(String(20), unique=True, index=True)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    
    # Account status
    status = Column(Enum(AgentStatus), default=AgentStatus.INACTIVE, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_on_duty = Column(Boolean, default=False, nullable=False, index=True)
    
    # Authentication
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255))
    backup_codes = Column(JSON)
    
    # Location and availability
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    current_address = Column(Text)
    location_updated_at = Column(DateTime(timezone=True))
    
    # Duty information
    shift_start = Column(DateTime(timezone=True))
    shift_end = Column(DateTime(timezone=True))
    duty_status = Column(String(20), default='available')  # 'available', 'busy', 'unavailable'
    
    # Performance metrics
    total_incidents_handled = Column(Integer, default=0, nullable=False)
    avg_response_time_minutes = Column(Float)
    success_rate = Column(Float)
    
    # Supervisor information
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), index=True)
    
    # Profile information
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    supervisor = relationship("Agent", remote_side=[id], backref="subordinates")
    incidents = relationship("AgentIncident", back_populates="agent", cascade="all, delete-orphan")
    sessions = relationship("AgentSession", back_populates="agent", cascade="all, delete-orphan")
    activity_logs = relationship("AgentActivityLog", back_populates="agent", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_type_status', 'agent_type', 'status'),
        Index('idx_agent_department_duty', 'department', 'is_on_duty'),
        Index('idx_agent_location', 'current_latitude', 'current_longitude'),
        Index('idx_agent_duty_status', 'duty_status', 'is_on_duty'),
        Index('idx_agent_supervisor', 'supervisor_id'),
    )
    
    def __repr__(self):
        return f"<Agent(id={self.id}, badge={self.badge_number}, name={self.first_name} {self.last_name})>"

class AgentIncident(Base):
    """Agent incident model for tracking agent assignments to incidents."""
    __tablename__ = "agent_incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Reference to alert service
    
    # Assignment details
    assigned_by = Column(UUID(as_uuid=True))  # Agent who made the assignment
    assignment_reason = Column(Text)
    priority_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Status tracking
    status = Column(Enum(IncidentStatus), default=IncidentStatus.ASSIGNED, nullable=False, index=True)
    
    # Location information
    incident_latitude = Column(Float)
    incident_longitude = Column(Float)
    incident_address = Column(Text)
    
    # Response tracking
    estimated_arrival_time = Column(DateTime(timezone=True))
    actual_arrival_time = Column(DateTime(timezone=True))
    response_time_minutes = Column(Float)
    
    # Resolution information
    resolution_notes = Column(Text)
    outcome = Column(String(50))  # 'resolved', 'transferred', 'escalated', 'false_alarm'
    
    # Performance metrics
    response_quality_score = Column(Float)  # 1-10 rating
    citizen_feedback_score = Column(Float)  # 1-5 rating
    
    # Timestamps
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True))
    en_route_at = Column(DateTime(timezone=True))
    arrived_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    agent = relationship("Agent", back_populates="incidents")
    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_incident_agent_status', 'agent_id', 'status'),
        Index('idx_incident_alert_agent', 'alert_id', 'agent_id'),
        Index('idx_incident_assigned_at', 'assigned_at'),
        Index('idx_incident_priority', 'priority_level', 'assigned_at'),
        Index('idx_incident_location', 'incident_latitude', 'incident_longitude'),
    )
    
    def __repr__(self):
        return f"<AgentIncident(id={self.id}, agent_id={self.agent_id}, alert_id={self.alert_id}, status={self.status.value})>"

class IncidentUpdate(Base):
    """Incident update model for tracking incident progress updates."""
    __tablename__ = "incident_updates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("agent_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Update information
    update_type = Column(String(50), nullable=False, index=True)  # 'status_change', 'location_update', 'note', 'media'
    description = Column(Text, nullable=False)
    
    # Location (if applicable)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Media attachments
    media_files = Column(JSON)  # Array of media file references
    
    # Metadata
    metadata = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    incident = relationship("AgentIncident", back_populates="updates")
    
    # Indexes
    __table_args__ = (
        Index('idx_update_incident_timestamp', 'incident_id', 'timestamp'),
        Index('idx_update_type_timestamp', 'update_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<IncidentUpdate(id={self.id}, incident_id={self.incident_id}, type={self.update_type})>"

class AgentSession(Base):
    """Agent session model for tracking active agent sessions."""
    __tablename__ = "agent_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session information
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(JSON)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_agent_active', 'agent_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_last_activity', 'last_activity'),
    )
    
    def __repr__(self):
        return f"<AgentSession(id={self.id}, agent_id={self.agent_id}, active={self.is_active})>"

class AgentActivityLog(Base):
    """Agent activity log model for tracking agent actions and events."""
    __tablename__ = "agent_activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity information
    activity_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Context information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Related entities
    related_incident_id = Column(UUID(as_uuid=True))
    related_alert_id = Column(UUID(as_uuid=True))
    related_user_id = Column(UUID(as_uuid=True))
    
    # Additional metadata
    metadata = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="activity_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_agent_type', 'agent_id', 'activity_type'),
        Index('idx_activity_timestamp', 'timestamp'),
        Index('idx_activity_type_timestamp', 'activity_type', 'timestamp'),
        Index('idx_activity_incident', 'related_incident_id'),
    )
    
    def __repr__(self):
        return f"<AgentActivityLog(id={self.id}, agent_id={self.agent_id}, type={self.activity_type})>"

class Department(Base):
    """Department model for organizing agents into departments."""
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Department information
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Contact information
    phone_number = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Department settings
    is_active = Column(Boolean, default=True, nullable=False)
    auto_assign_incidents = Column(Boolean, default=True, nullable=False)
    max_concurrent_incidents = Column(Integer, default=10)
    
    # Coverage area
    coverage_area = Column(JSON)  # GeoJSON polygon
    service_radius_km = Column(Float, default=50.0)
    
    # Statistics
    total_agents = Column(Integer, default=0, nullable=False)
    active_agents = Column(Integer, default=0, nullable=False)
    total_incidents_handled = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_department_active', 'is_active'),
        Index('idx_department_location', 'latitude', 'longitude'),
    )
    
    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name}, code={self.code})>"

class AgentShift(Base):
    """Agent shift model for tracking agent work schedules."""
    __tablename__ = "agent_shifts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Shift information
    shift_date = Column(DateTime(timezone=True), nullable=False, index=True)
    shift_type = Column(String(20), nullable=False)  # 'day', 'night', 'swing', 'overtime'
    
    # Timing
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default='scheduled', nullable=False)  # 'scheduled', 'active', 'completed', 'cancelled'
    
    # Break tracking
    break_start = Column(DateTime(timezone=True))
    break_end = Column(DateTime(timezone=True))
    total_break_minutes = Column(Integer, default=0)
    
    # Performance
    incidents_handled = Column(Integer, default=0, nullable=False)
    overtime_minutes = Column(Integer, default=0, nullable=False)
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    agent = relationship("Agent")
    
    # Indexes
    __table_args__ = (
        Index('idx_shift_agent_date', 'agent_id', 'shift_date'),
        Index('idx_shift_date_type', 'shift_date', 'shift_type'),
        Index('idx_shift_status', 'status', 'shift_date'),
    )
    
    def __repr__(self):
        return f"<AgentShift(id={self.id}, agent_id={self.agent_id}, date={self.shift_date}, type={self.shift_type})>"

class AgentPerformanceMetrics(Base):
    """Agent performance metrics model for storing performance data."""
    __tablename__ = "agent_performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metrics period
    metrics_date = Column(DateTime(timezone=True), nullable=False, index=True)
    metrics_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly', 'monthly', 'yearly'
    
    # Response metrics
    total_incidents = Column(Integer, default=0, nullable=False)
    avg_response_time_minutes = Column(Float)
    incidents_resolved = Column(Integer, default=0, nullable=False)
    incidents_transferred = Column(Integer, default=0, nullable=False)
    
    # Quality metrics
    avg_quality_score = Column(Float)
    citizen_satisfaction_score = Column(Float)
    supervisor_rating = Column(Float)
    
    # Time metrics
    total_duty_hours = Column(Float, default=0.0, nullable=False)
    overtime_hours = Column(Float, default=0.0, nullable=False)
    break_time_hours = Column(Float, default=0.0, nullable=False)
    
    # Efficiency metrics
    incidents_per_hour = Column(Float)
    resolution_rate = Column(Float)  # Percentage of incidents resolved
    
    # Training and development
    training_hours_completed = Column(Float, default=0.0, nullable=False)
    certifications_earned = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    agent = relationship("Agent")
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_agent_date', 'agent_id', 'metrics_date'),
        Index('idx_metrics_date_type', 'metrics_date', 'metrics_type'),
        Index('idx_metrics_performance', 'avg_quality_score', 'resolution_rate'),
    )
    
    def __repr__(self):
        return f"<AgentPerformanceMetrics(id={self.id}, agent_id={self.agent_id}, date={self.metrics_date})>"