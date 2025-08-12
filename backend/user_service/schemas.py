from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserProfileResponse(BaseModel):
    """Response schema for user profile."""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, v))
            # Check if it's a valid length (10-15 digits)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError('Phone number must be between 10 and 15 digits')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 50:
                raise ValueError('Name cannot be longer than 50 characters')
        return v

class EmergencyContactCreate(BaseModel):
    """Schema for creating an emergency contact."""
    name: str
    phone_number: str
    email: Optional[EmailStr] = None
    relationship: str
    is_primary: bool = False
    
    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name cannot be longer than 100 characters')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        # Check if it's a valid length (10-15 digits)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return v
    
    @validator('relationship')
    def validate_relationship(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Relationship is required')
        if len(v) > 50:
            raise ValueError('Relationship cannot be longer than 50 characters')
        
        # Common relationship types
        valid_relationships = [
            'spouse', 'partner', 'parent', 'child', 'sibling', 'friend',
            'colleague', 'neighbor', 'relative', 'guardian', 'caregiver', 'other'
        ]
        
        if v.lower() not in valid_relationships:
            # Allow custom relationships but warn
            pass
        
        return v

class EmergencyContactUpdate(BaseModel):
    """Schema for updating an emergency contact."""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    relationship: Optional[str] = None
    is_primary: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 100:
                raise ValueError('Name cannot be longer than 100 characters')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, v))
            # Check if it's a valid length (10-15 digits)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError('Phone number must be between 10 and 15 digits')
        return v
    
    @validator('relationship')
    def validate_relationship(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError('Relationship cannot be empty')
            if len(v) > 50:
                raise ValueError('Relationship cannot be longer than 50 characters')
        return v

class EmergencyContactResponse(BaseModel):
    """Response schema for emergency contact."""
    id: UUID
    name: str
    phone_number: str
    email: Optional[str] = None
    relationship: str
    is_primary: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    silent_mode: Optional[bool] = None
    auto_location_sharing: Optional[bool] = None
    emergency_contacts_notification: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None

class UserPreferencesResponse(BaseModel):
    """Response schema for user preferences."""
    silent_mode: bool
    auto_location_sharing: bool
    emergency_contacts_notification: bool
    push_notifications: bool
    sms_notifications: bool
    email_notifications: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    """Response schema for user statistics."""
    total_alerts: int
    panic_alerts: int
    test_alerts: int
    active_geofences: int
    emergency_contacts_count: int
    account_age_days: int
    last_alert_date: Optional[datetime] = None
    last_login_date: Optional[datetime] = None

class UserActivityResponse(BaseModel):
    """Response schema for user activity."""
    user_id: UUID
    activity_type: str
    description: str
    timestamp: datetime
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True

class UserDeviceInfo(BaseModel):
    """Schema for user device information."""
    device_id: str
    device_type: str  # 'mobile', 'web', 'tablet'
    platform: str  # 'ios', 'android', 'web'
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    push_token: Optional[str] = None
    
    @validator('device_type')
    def validate_device_type(cls, v):
        valid_types = ['mobile', 'web', 'tablet', 'desktop']
        if v.lower() not in valid_types:
            raise ValueError(f'Device type must be one of: {valid_types}')
        return v.lower()
    
    @validator('platform')
    def validate_platform(cls, v):
        valid_platforms = ['ios', 'android', 'web', 'windows', 'macos', 'linux']
        if v.lower() not in valid_platforms:
            raise ValueError(f'Platform must be one of: {valid_platforms}')
        return v.lower()

class UserDeviceResponse(BaseModel):
    """Response schema for user device."""
    id: UUID
    device_id: str
    device_type: str
    platform: str
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    is_active: bool
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLocationUpdate(BaseModel):
    """Schema for updating user location."""
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

class UserLocationResponse(BaseModel):
    """Response schema for user location."""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    address: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class UserSearchRequest(BaseModel):
    """Schema for searching users (admin only)."""
    query: str
    search_type: str = 'email'  # 'email', 'name', 'phone'
    limit: int = 20
    skip: int = 0
    
    @validator('search_type')
    def validate_search_type(cls, v):
        valid_types = ['email', 'name', 'phone', 'all']
        if v not in valid_types:
            raise ValueError(f'Search type must be one of: {valid_types}')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('Limit must be between 1 and 100')
        return v

class UserListResponse(BaseModel):
    """Response schema for user list."""
    users: List[UserProfileResponse]
    total: int
    skip: int
    limit: int

class EmergencyContactListResponse(BaseModel):
    """Response schema for emergency contact list."""
    contacts: List[EmergencyContactResponse]
    total: int

class UserNotificationSettings(BaseModel):
    """Schema for user notification settings."""
    emergency_alerts: bool = True
    geofence_alerts: bool = True
    system_notifications: bool = True
    marketing_emails: bool = False
    sms_alerts: bool = True
    email_alerts: bool = True
    push_notifications: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # Format: "HH:MM"
    quiet_hours_end: Optional[str] = None    # Format: "HH:MM"
    
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

class UserPrivacySettings(BaseModel):
    """Schema for user privacy settings."""
    location_sharing: bool = True
    contact_sharing: bool = False
    activity_logging: bool = True
    analytics_participation: bool = True
    data_retention_days: int = 365
    
    @validator('data_retention_days')
    def validate_retention_days(cls, v):
        if not 30 <= v <= 2555:  # 30 days to 7 years
            raise ValueError('Data retention must be between 30 and 2555 days')
        return v