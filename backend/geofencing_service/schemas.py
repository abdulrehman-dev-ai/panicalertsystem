from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from enum import Enum

class GeofenceType(str, Enum):
    """Enumeration for geofence types."""
    SAFE_ZONE = "safe_zone"
    RESTRICTED_ZONE = "restricted_zone"
    HOME = "home"
    WORK = "work"
    SCHOOL = "school"
    CUSTOM = "custom"

class GeofenceStatus(str, Enum):
    """Enumeration for geofence statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    EXPIRED = "expired"

class GeofenceEventType(str, Enum):
    """Enumeration for geofence event types."""
    ENTER = "enter"
    EXIT = "exit"
    DWELL = "dwell"
    BREACH = "breach"

class GeofenceShape(str, Enum):
    """Enumeration for geofence shapes."""
    CIRCLE = "circle"
    POLYGON = "polygon"
    RECTANGLE = "rectangle"

class GeofenceCreate(BaseModel):
    """Schema for creating a geofence."""
    name: str
    description: Optional[str] = None
    geofence_type: GeofenceType
    shape: GeofenceShape = GeofenceShape.CIRCLE
    center_latitude: float
    center_longitude: float
    radius_meters: Optional[float] = None
    coordinates: Optional[List[Tuple[float, float]]] = None
    is_active: bool = True
    send_notifications: bool = True
    notification_events: List[GeofenceEventType] = [GeofenceEventType.ENTER, GeofenceEventType.EXIT]
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name cannot be longer than 100 characters')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Description cannot be longer than 500 characters')
        return v
    
    @validator('center_latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('center_longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v
    
    @validator('radius_meters')
    def validate_radius(cls, v, values):
        if values.get('shape') == GeofenceShape.CIRCLE:
            if v is None:
                raise ValueError('Radius is required for circular geofences')
            if not 10 <= v <= 100000:  # 10 meters to 100 km
                raise ValueError('Radius must be between 10 and 100,000 meters')
        return v
    
    @validator('coordinates')
    def validate_coordinates(cls, v, values):
        shape = values.get('shape')
        if shape in [GeofenceShape.POLYGON, GeofenceShape.RECTANGLE]:
            if v is None or len(v) < 3:
                raise ValueError(f'{shape} geofences require at least 3 coordinates')
            if shape == GeofenceShape.RECTANGLE and len(v) != 4:
                raise ValueError('Rectangle geofences require exactly 4 coordinates')
            if len(v) > 100:
                raise ValueError('Maximum 100 coordinates allowed')
            
            # Validate each coordinate
            for i, (lat, lng) in enumerate(v):
                if not -90 <= lat <= 90:
                    raise ValueError(f'Coordinate {i}: Latitude must be between -90 and 90 degrees')
                if not -180 <= lng <= 180:
                    raise ValueError(f'Coordinate {i}: Longitude must be between -180 and 180 degrees')
        return v
    
    @validator('notification_events')
    def validate_notification_events(cls, v):
        if len(v) == 0:
            raise ValueError('At least one notification event is required')
        return v

class GeofenceUpdate(BaseModel):
    """Schema for updating a geofence."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    send_notifications: Optional[bool] = None
    notification_events: Optional[List[GeofenceEventType]] = None
    radius_meters: Optional[float] = None
    coordinates: Optional[List[Tuple[float, float]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 100:
                raise ValueError('Name cannot be longer than 100 characters')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Description cannot be longer than 500 characters')
        return v
    
    @validator('radius_meters')
    def validate_radius(cls, v):
        if v is not None and not 10 <= v <= 100000:
            raise ValueError('Radius must be between 10 and 100,000 meters')
        return v
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('At least 3 coordinates are required')
            if len(v) > 100:
                raise ValueError('Maximum 100 coordinates allowed')
            
            # Validate each coordinate
            for i, (lat, lng) in enumerate(v):
                if not -90 <= lat <= 90:
                    raise ValueError(f'Coordinate {i}: Latitude must be between -90 and 90 degrees')
                if not -180 <= lng <= 180:
                    raise ValueError(f'Coordinate {i}: Longitude must be between -180 and 180 degrees')
        return v

class GeofenceResponse(BaseModel):
    """Response schema for geofence."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    geofence_type: GeofenceType
    shape: GeofenceShape
    center_latitude: float
    center_longitude: float
    radius_meters: Optional[float] = None
    coordinates: Optional[List[Tuple[float, float]]] = None
    is_active: bool
    send_notifications: bool
    notification_events: List[GeofenceEventType]
    created_at: datetime
    updated_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class GeofenceListResponse(BaseModel):
    """Response schema for geofence list."""
    geofences: List[GeofenceResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

class LocationUpdate(BaseModel):
    """Schema for location updates."""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v
    
    @validator('accuracy')
    def validate_accuracy(cls, v):
        if v is not None and v < 0:
            raise ValueError('Accuracy cannot be negative')
        return v
    
    @validator('speed')
    def validate_speed(cls, v):
        if v is not None and v < 0:
            raise ValueError('Speed cannot be negative')
        return v
    
    @validator('heading')
    def validate_heading(cls, v):
        if v is not None and not 0 <= v <= 360:
            raise ValueError('Heading must be between 0 and 360 degrees')
        return v

class GeofenceEventCreate(BaseModel):
    """Schema for creating a geofence event."""
    geofence_id: UUID
    event_type: GeofenceEventType
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

class GeofenceEventResponse(BaseModel):
    """Response schema for geofence event."""
    id: UUID
    user_id: UUID
    geofence_id: UUID
    geofence_name: str
    event_type: GeofenceEventType
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    address: Optional[str] = None
    timestamp: datetime
    duration_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class GeofenceEventListResponse(BaseModel):
    """Response schema for geofence event list."""
    events: List[GeofenceEventResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

class GeofenceAnalyticsRequest(BaseModel):
    """Schema for geofence analytics request."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    geofence_ids: Optional[List[UUID]] = None
    event_types: Optional[List[GeofenceEventType]] = None
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

class GeofenceAnalyticsResponse(BaseModel):
    """Response schema for geofence analytics."""
    total_events: int
    enter_events: int
    exit_events: int
    dwell_events: int
    breach_events: int
    most_active_geofence: Optional[Dict[str, Any]] = None
    average_dwell_time_minutes: Optional[float] = None
    events_by_period: List[Dict[str, Any]] = []
    events_by_geofence: List[Dict[str, Any]] = []
    events_by_hour: List[Dict[str, Any]] = []
    events_by_day_of_week: List[Dict[str, Any]] = []

class GeofenceSearchRequest(BaseModel):
    """Schema for searching geofences."""
    query: Optional[str] = None
    geofence_type: Optional[GeofenceType] = None
    is_active: Optional[bool] = None
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

class GeofenceImportRequest(BaseModel):
    """Schema for importing geofences."""
    geofences: List[GeofenceCreate]
    overwrite_existing: bool = False
    
    @validator('geofences')
    def validate_geofences(cls, v):
        if len(v) == 0:
            raise ValueError('At least one geofence is required')
        if len(v) > 100:
            raise ValueError('Cannot import more than 100 geofences at once')
        return v

class GeofenceImportResponse(BaseModel):
    """Response schema for geofence import."""
    successful_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []
    imported_geofence_ids: List[UUID]

class GeofenceExportRequest(BaseModel):
    """Schema for exporting geofences."""
    format: str = 'json'  # 'json', 'csv', 'kml', 'geojson'
    geofence_ids: Optional[List[UUID]] = None
    include_events: bool = False
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['json', 'csv', 'kml', 'geojson']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {valid_formats}')
        return v

class GeofenceExportResponse(BaseModel):
    """Response schema for geofence export."""
    export_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None

class GeofenceTemplate(BaseModel):
    """Schema for geofence templates."""
    name: str
    description: Optional[str] = None
    geofence_type: GeofenceType
    shape: GeofenceShape
    default_radius_meters: Optional[float] = None
    default_coordinates: Optional[List[Tuple[float, float]]] = None
    default_notification_events: List[GeofenceEventType] = [GeofenceEventType.ENTER, GeofenceEventType.EXIT]
    is_public: bool = False
    
    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name cannot be longer than 100 characters')
        return v

class GeofenceTemplateResponse(BaseModel):
    """Response schema for geofence template."""
    id: UUID
    name: str
    description: Optional[str] = None
    geofence_type: GeofenceType
    shape: GeofenceShape
    default_radius_meters: Optional[float] = None
    default_coordinates: Optional[List[Tuple[float, float]]] = None
    default_notification_events: List[GeofenceEventType]
    is_public: bool
    created_by: UUID
    created_at: datetime
    usage_count: int = 0
    
    class Config:
        from_attributes = True

class GeofenceNotificationSettings(BaseModel):
    """Schema for geofence notification settings."""
    send_push_notifications: bool = True
    send_sms_notifications: bool = False
    send_email_notifications: bool = False
    notification_delay_seconds: int = 0
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # Format: "HH:MM"
    quiet_hours_end: Optional[str] = None    # Format: "HH:MM"
    
    @validator('notification_delay_seconds')
    def validate_delay(cls, v):
        if not 0 <= v <= 3600:  # 0 to 1 hour
            raise ValueError('Notification delay must be between 0 and 3600 seconds')
        return v
    
    @validator('quiet_hours_start', 'quiet_hours_end')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                hour, minute = map(int, v.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError('Invalid time format')
            except (ValueError, AttributeError):
                raise ValueError('Time must be in HH:MM format (24-hour)')
        return v

class GeofenceStatistics(BaseModel):
    """Schema for geofence statistics."""
    total_geofences: int
    active_geofences: int
    inactive_geofences: int
    geofences_by_type: Dict[str, int]
    total_events_today: int
    total_events_this_week: int
    total_events_this_month: int
    most_triggered_geofence: Optional[Dict[str, Any]] = None
    average_events_per_geofence: float
    last_event_timestamp: Optional[datetime] = None

class GeofenceBulkAction(BaseModel):
    """Schema for bulk geofence actions."""
    geofence_ids: List[UUID]
    action: str  # 'activate', 'deactivate', 'delete', 'duplicate'
    
    @validator('geofence_ids')
    def validate_geofence_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one geofence ID is required')
        if len(v) > 50:
            raise ValueError('Cannot perform bulk action on more than 50 geofences')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['activate', 'deactivate', 'delete', 'duplicate']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v

class GeofenceBulkActionResponse(BaseModel):
    """Response schema for bulk geofence actions."""
    successful_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []
    processed_geofence_ids: List[UUID]