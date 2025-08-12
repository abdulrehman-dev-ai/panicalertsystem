from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum
import re

class UserRole(str, Enum):
    """Enumeration for user roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    EMERGENCY_RESPONDER = "emergency_responder"
    AGENT = "agent"
    SYSTEM = "system"

class TokenType(str, Enum):
    """Enumeration for token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"

class AuthProvider(str, Enum):
    """Enumeration for authentication providers."""
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"
    MICROSOFT = "microsoft"

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove any non-digit characters for validation
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or just whitespace')
        return v.strip().title()

class AgentCreate(BaseModel):
    """Schema for agent registration."""
    employee_id: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    badge_number: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field("agent", max_length=50)
    
    @validator('phone')
    def validate_phone(cls, v):
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or just whitespace')
        return v.strip().title()
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['agent', 'supervisor', 'admin', 'dispatcher']
        if v and v.lower() not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v.lower() if v else 'agent'

class UserLogin(BaseModel):
    """Schema for user login."""
    identifier: str = Field(..., description="Email or phone number")
    password: str = Field(..., min_length=1)
    
    @validator('identifier')
    def validate_identifier(cls, v):
        if not v.strip():
            raise ValueError('Identifier cannot be empty')
        return v.strip()

class AgentLogin(BaseModel):
    """Schema for agent login."""
    identifier: str = Field(..., description="Email, phone number, or employee ID")
    password: str = Field(..., min_length=1)
    
    @validator('identifier')
    def validate_identifier(cls, v):
        if not v.strip():
            raise ValueError('Identifier cannot be empty')
        return v.strip()

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_data: Dict[str, Any]

class UserResponse(BaseModel):
    """Schema for user response."""
    user: Dict[str, Any]
    message: str

class AgentResponse(BaseModel):
    """Schema for agent response."""
    agent: Dict[str, Any]
    message: str

class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordReset(BaseModel):
    """Schema for password reset request."""
    identifier: str = Field(..., description="Email or phone number")
    
    @validator('identifier')
    def validate_identifier(cls, v):
        if not v.strip():
            raise ValueError('Identifier cannot be empty')
        return v.strip()

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class EmailVerification(BaseModel):
    """Schema for email verification."""
    token: str = Field(..., min_length=1)

class PhoneVerification(BaseModel):
    """Schema for phone verification."""
    phone: str = Field(..., min_length=10, max_length=20)
    verification_code: str = Field(..., min_length=4, max_length=10)
    
    @validator('phone')
    def validate_phone(cls, v):
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., min_length=1)

class LogoutRequest(BaseModel):
    """Schema for logout request."""
    refresh_token: str = Field(..., min_length=1)

class UserUpdate(BaseModel):
    """Schema for user profile update."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            digits_only = re.sub(r'\D', '', v)
            if len(digits_only) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty or just whitespace')
            return v.strip().title()
        return v

class AgentUpdate(BaseModel):
    """Schema for agent profile update."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    badge_number: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    is_on_duty: Optional[bool] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            digits_only = re.sub(r'\D', '', v)
            if len(digits_only) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty or just whitespace')
            return v.strip().title()
        return v

class TokenVerification(BaseModel):
    """Schema for token verification response."""
    valid: bool
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class AuthResponse(BaseModel):
    """Generic auth response schema."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SocialLogin(BaseModel):
    """Schema for social media login."""
    provider: AuthProvider
    access_token: str
    device_info: Optional[Dict[str, str]] = None
    
    @validator('access_token')
    def validate_access_token(cls, v):
        if len(v) < 1:
            raise ValueError('Access token is required')
        return v

class TwoFactorSetup(BaseModel):
    """Schema for two-factor authentication setup."""
    method: str  # 'totp', 'sms', 'email'
    phone_number: Optional[str] = None
    
    @validator('method')
    def validate_method(cls, v):
        valid_methods = ['totp', 'sms', 'email']
        if v not in valid_methods:
            raise ValueError(f'Method must be one of: {valid_methods}')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v, values):
        if values.get('method') == 'sms' and v is None:
            raise ValueError('Phone number is required for SMS 2FA')
        if v is not None:
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError('Phone number must be between 10 and 15 digits')
        return v

class TwoFactorSetupResponse(BaseModel):
    """Response schema for two-factor authentication setup."""
    method: str
    secret_key: Optional[str] = None  # For TOTP
    qr_code_url: Optional[str] = None  # For TOTP
    backup_codes: List[str] = []
    
class TwoFactorVerify(BaseModel):
    """Schema for two-factor authentication verification."""
    code: str
    backup_code: Optional[str] = None
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            v = v.strip().replace(' ', '')
            if len(v) != 6 or not v.isdigit():
                raise ValueError('Code must be 6 digits')
        return v
    
    @validator('backup_code')
    def validate_backup_code(cls, v):
        if v is not None:
            v = v.strip().replace(' ', '').replace('-', '')
            if len(v) != 8 or not v.isalnum():
                raise ValueError('Backup code must be 8 alphanumeric characters')
        return v

class SessionInfo(BaseModel):
    """Schema for session information."""
    id: UUID
    user_id: UUID
    device_info: Optional[Dict[str, str]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    """Response schema for session list."""
    sessions: List[SessionInfo]
    current_session_id: UUID
    
class APIKeyCreate(BaseModel):
    """Schema for creating API keys."""
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    expires_at: Optional[datetime] = None
    
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
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = [
            'read:profile', 'write:profile', 'read:alerts', 'write:alerts',
            'read:geofences', 'write:geofences', 'read:media', 'write:media',
            'read:analytics', 'admin:users', 'admin:system'
        ]
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f'Invalid permission: {permission}')
        return v

class APIKeyResponse(BaseModel):
    """Response schema for API key."""
    id: UUID
    name: str
    description: Optional[str] = None
    key: Optional[str] = None  # Only returned on creation
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool
    usage_count: int = 0
    
    class Config:
        from_attributes = True

class SecurityEvent(BaseModel):
    """Schema for security events."""
    user_id: Optional[UUID] = None
    event_type: str
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    severity: str = 'info'
    
    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = [
            'login_success', 'login_failure', 'logout', 'password_change',
            'password_reset', 'email_verification', 'account_locked',
            'account_unlocked', 'two_factor_enabled', 'two_factor_disabled',
            'api_key_created', 'api_key_deleted', 'suspicious_activity'
        ]
        if v not in valid_types:
            raise ValueError(f'Event type must be one of: {valid_types}')
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['info', 'warning', 'error', 'critical']
        if v not in valid_severities:
            raise ValueError(f'Severity must be one of: {valid_severities}')
        return v
    
    class Config:
        from_attributes = True