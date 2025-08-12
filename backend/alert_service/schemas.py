from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class AlertType(str, Enum):
    """Enumeration for alert types."""
    PANIC = "panic"
    TEST = "test"
    MEDICAL = "medical"
    FIRE = "fire"
    SECURITY = "security"
    NATURAL_DISASTER = "natural_disaster"
    CUSTOM = "custom"

class AlertStatus(str, Enum):
    """Enumeration for alert statuses."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class AlertPriority(str, Enum):
    """Enumeration for alert priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertCreate(BaseModel):
    """Schema for creating an alert."""
    alert_type: AlertType
    message: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: AlertPriority = AlertPriority.HIGH
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Message cannot be longer than 500 characters')
        return v

class PanicAlertCreate(BaseModel):
    """Schema for creating a panic alert."""
    message: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    silent_mode: bool = False
    include_audio: bool = False
    include_video: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Message cannot be longer than 500 characters')
        return v

class TestAlertCreate(BaseModel):
    """Schema for creating a test alert."""
    message: Optional[str] = "Test alert - please ignore"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    test_type: str = "manual"
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v
    
    @validator('test_type')
    def validate_test_type(cls, v):
        valid_types = ['manual', 'scheduled', 'automated', 'system']
        if v not in valid_types:
            raise ValueError(f'Test type must be one of: {valid_types}')
        return v

class AlertStatusUpdate(BaseModel):
    """Schema for updating alert status."""
    status: AlertStatus
    notes: Optional[str] = None
    resolved_by: Optional[str] = None
    
    @validator('notes')
    def validate_notes(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError('Notes cannot be longer than 1000 characters')
        return v

class AlertResponse(BaseModel):
    """Response schema for alert."""
    id: UUID
    user_id: UUID
    alert_type: AlertType
    status: AlertStatus
    priority: AlertPriority
    message: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    response_time_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    """Response schema for alert list."""
    alerts: List[AlertResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

class AlertSummaryResponse(BaseModel):
    """Response schema for alert summary/analytics."""
    total_alerts: int
    panic_alerts: int
    test_alerts: int
    medical_alerts: int
    fire_alerts: int
    security_alerts: int
    natural_disaster_alerts: int
    custom_alerts: int
    active_alerts: int
    resolved_alerts: int
    cancelled_alerts: int
    average_response_time_seconds: Optional[float] = None
    fastest_response_time_seconds: Optional[int] = None
    slowest_response_time_seconds: Optional[int] = None
    alerts_by_day: List[Dict[str, Any]] = []
    alerts_by_hour: List[Dict[str, Any]] = []
    most_common_locations: List[Dict[str, Any]] = []

class AlertTimelineEvent(BaseModel):
    """Schema for alert timeline events."""
    event_type: str
    description: str
    timestamp: datetime
    user_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class AlertTimelineResponse(BaseModel):
    """Response schema for alert timeline."""
    alert_id: UUID
    events: List[AlertTimelineEvent]

class AlertNotificationResponse(BaseModel):
    """Response schema for alert notifications."""
    id: UUID
    alert_id: UUID
    notification_type: str  # 'sms', 'email', 'push', 'call'
    recipient: str
    status: str  # 'sent', 'delivered', 'failed', 'pending'
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class AlertSearchRequest(BaseModel):
    """Schema for searching alerts."""
    query: Optional[str] = None
    alert_type: Optional[AlertType] = None
    status: Optional[AlertStatus] = None
    priority: Optional[AlertPriority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    limit: int = 20
    skip: int = 0
    
    @validator('limit')
    def validate_limit(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('Limit must be between 1 and 100')
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

class AlertMetrics(BaseModel):
    """Schema for alert metrics."""
    period: str  # 'hour', 'day', 'week', 'month'
    timestamp: datetime
    total_alerts: int
    panic_alerts: int
    test_alerts: int
    resolved_alerts: int
    average_response_time: Optional[float] = None

class AlertMetricsResponse(BaseModel):
    """Response schema for alert metrics."""
    metrics: List[AlertMetrics]
    summary: AlertSummaryResponse

class AlertLocationInfo(BaseModel):
    """Schema for alert location information."""
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    accuracy: Optional[float] = None
    nearby_landmarks: List[str] = []
    emergency_services: List[Dict[str, Any]] = []

class AlertEscalationRule(BaseModel):
    """Schema for alert escalation rules."""
    alert_type: AlertType
    escalation_delay_minutes: int
    escalation_levels: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    
    @validator('escalation_delay_minutes')
    def validate_delay(cls, v):
        if not 1 <= v <= 1440:  # 1 minute to 24 hours
            raise ValueError('Escalation delay must be between 1 and 1440 minutes')
        return v

class AlertEscalationResponse(BaseModel):
    """Response schema for alert escalation."""
    id: UUID
    alert_id: UUID
    escalation_level: int
    escalated_at: datetime
    escalated_to: List[str]
    status: str
    
    class Config:
        from_attributes = True

class AlertBulkAction(BaseModel):
    """Schema for bulk alert actions."""
    alert_ids: List[UUID]
    action: str  # 'acknowledge', 'resolve', 'cancel', 'delete'
    notes: Optional[str] = None
    
    @validator('alert_ids')
    def validate_alert_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one alert ID is required')
        if len(v) > 100:
            raise ValueError('Cannot perform bulk action on more than 100 alerts')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['acknowledge', 'resolve', 'cancel', 'delete']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v

class AlertBulkActionResponse(BaseModel):
    """Response schema for bulk alert actions."""
    successful_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []
    processed_alert_ids: List[UUID]

class AlertExportRequest(BaseModel):
    """Schema for exporting alerts."""
    format: str = 'csv'  # 'csv', 'json', 'pdf'
    filters: Optional[AlertSearchRequest] = None
    include_timeline: bool = False
    include_notifications: bool = False
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['csv', 'json', 'pdf', 'xlsx']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {valid_formats}')
        return v

class AlertExportResponse(BaseModel):
    """Response schema for alert export."""
    export_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None

class AlertWebhookConfig(BaseModel):
    """Schema for alert webhook configuration."""
    url: str
    events: List[str]  # 'created', 'updated', 'resolved', 'escalated'
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    retry_count: int = 3
    timeout_seconds: int = 30
    
    @validator('events')
    def validate_events(cls, v):
        valid_events = ['created', 'updated', 'resolved', 'escalated', 'cancelled']
        for event in v:
            if event not in valid_events:
                raise ValueError(f'Event must be one of: {valid_events}')
        return v
    
    @validator('retry_count')
    def validate_retry_count(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Retry count must be between 0 and 10')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        if not 1 <= v <= 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v

class AlertWebhookResponse(BaseModel):
    """Response schema for alert webhook."""
    id: UUID
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None
    success_count: int
    failure_count: int
    
    class Config:
        from_attributes = True