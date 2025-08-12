from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional

from ..shared.database import Base
from ..shared.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using Argon2."""
        return pwd_context.hash(password)
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "phone": self.phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Agent(Base):
    """Agent model for emergency responders."""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    badge_number = Column(String(50))
    department = Column(String(100))
    role = Column(String(50), default="agent")
    is_active = Column(Boolean, default=True)
    is_on_duty = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using Argon2."""
        return pwd_context.hash(password)
    
    @property
    def full_name(self) -> str:
        """Get agent's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "employee_id": self.employee_id,
            "email": self.email,
            "phone": self.phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "badge_number": self.badge_number,
            "department": self.department,
            "role": self.role,
            "is_active": self.is_active,
            "is_on_duty": self.is_on_duty,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class RefreshToken(Base):
    """Refresh token model for JWT token management."""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(Text, unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For regular users
    agent_id = Column(UUID(as_uuid=True), nullable=True)  # For agents
    user_type = Column(String(10), nullable=False)  # 'user' or 'agent'
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked

# JWT Token utilities
class TokenManager:
    """JWT token management utilities."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token() -> str:
        """Create refresh token."""
        return str(uuid.uuid4())
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def create_user_tokens(user: User) -> dict:
        """Create access and refresh tokens for user."""
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "user_type": "user",
            "is_verified": user.is_verified
        }
        
        access_token = TokenManager.create_access_token(access_token_data)
        refresh_token = TokenManager.create_refresh_token()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def create_agent_tokens(agent: Agent) -> dict:
        """Create access and refresh tokens for agent."""
        access_token_data = {
            "sub": str(agent.id),
            "email": agent.email,
            "user_type": "agent",
            "role": agent.role,
            "is_on_duty": agent.is_on_duty
        }
        
        access_token = TokenManager.create_access_token(access_token_data)
        refresh_token = TokenManager.create_refresh_token()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }