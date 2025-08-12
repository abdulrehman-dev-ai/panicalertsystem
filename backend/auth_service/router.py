from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime, timedelta
import re

from ..shared.database import get_db
from ..shared.config import settings
from .models import User, Agent, RefreshToken, TokenManager
from .schemas import (
    UserCreate, UserLogin, AgentCreate, AgentLogin,
    TokenResponse, UserResponse, AgentResponse
)

router = APIRouter()
security = HTTPBearer()

# Password validation
def validate_password(password: str) -> bool:
    """Validate password strength."""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False
    
    if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
        return False
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token."""
    token = credentials.credentials
    
    payload = TokenManager.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user_type = payload.get("user_type")
    
    if user_type == "user":
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        return user
    elif user_type == "agent":
        agent = db.query(Agent).filter(Agent.id == user_id).first()
        if agent is None or not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent not found or inactive"
            )
        return agent
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user type"
        )

# User registration
@router.post("/register/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    
    # Validate password
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.phone == user_data.phone)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or phone already exists"
        )
    
    # Create new user
    hashed_password = User.hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        user=new_user.to_dict(),
        message="User registered successfully"
    )

# Agent registration
@router.post("/register/agent", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """Register a new agent."""
    
    # Validate password
    if not validate_password(agent_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements"
        )
    
    # Check if agent already exists
    existing_agent = db.query(Agent).filter(
        (Agent.email == agent_data.email) | 
        (Agent.phone == agent_data.phone) |
        (Agent.employee_id == agent_data.employee_id)
    ).first()
    
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent with this email, phone, or employee ID already exists"
        )
    
    # Create new agent
    hashed_password = Agent.hash_password(agent_data.password)
    
    new_agent = Agent(
        employee_id=agent_data.employee_id,
        email=agent_data.email,
        phone=agent_data.phone,
        password_hash=hashed_password,
        first_name=agent_data.first_name,
        last_name=agent_data.last_name,
        badge_number=agent_data.badge_number,
        department=agent_data.department,
        role=agent_data.role or "agent"
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    return AgentResponse(
        agent=new_agent.to_dict(),
        message="Agent registered successfully"
    )

# User login
@router.post("/login/user", response_model=TokenResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
    
    # Find user by email or phone
    user = db.query(User).filter(
        (User.email == login_data.identifier) | (User.phone == login_data.identifier)
    ).first()
    
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create tokens
    tokens = TokenManager.create_user_tokens(user)
    
    # Store refresh token in database
    refresh_token_record = RefreshToken(
        token=tokens["refresh_token"],
        user_id=user.id,
        user_type="user",
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    db.add(refresh_token_record)
    db.commit()
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user_data=user.to_dict()
    )

# Agent login
@router.post("/login/agent", response_model=TokenResponse)
async def login_agent(login_data: AgentLogin, db: Session = Depends(get_db)):
    """Authenticate agent and return tokens."""
    
    # Find agent by email, phone, or employee ID
    agent = db.query(Agent).filter(
        (Agent.email == login_data.identifier) | 
        (Agent.phone == login_data.identifier) |
        (Agent.employee_id == login_data.identifier)
    ).first()
    
    if not agent or not agent.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create tokens
    tokens = TokenManager.create_agent_tokens(agent)
    
    # Store refresh token in database
    refresh_token_record = RefreshToken(
        token=tokens["refresh_token"],
        agent_id=agent.id,
        user_type="agent",
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    db.add(refresh_token_record)
    db.commit()
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user_data=agent.to_dict()
    )

# Token refresh
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    
    # Find refresh token in database
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()
    
    if not token_record or not token_record.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user or agent
    if token_record.user_type == "user":
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        tokens = TokenManager.create_user_tokens(user)
        user_data = user.to_dict()
    else:
        agent = db.query(Agent).filter(Agent.id == token_record.agent_id).first()
        if not agent or not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent not found or inactive"
            )
        tokens = TokenManager.create_agent_tokens(agent)
        user_data = agent.to_dict()
    
    # Revoke old refresh token
    token_record.is_revoked = True
    
    # Create new refresh token
    new_refresh_token_record = RefreshToken(
        token=tokens["refresh_token"],
        user_id=token_record.user_id,
        agent_id=token_record.agent_id,
        user_type=token_record.user_type,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    db.add(new_refresh_token_record)
    db.commit()
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user_data=user_data
    )

# Logout
@router.post("/logout")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    """Logout user by revoking refresh token."""
    
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()
    
    if token_record:
        token_record.is_revoked = True
        db.commit()
    
    return {"message": "Logged out successfully"}

# Get current user profile
@router.get("/me")
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile."""
    return current_user.to_dict()

# Verify token
@router.get("/verify")
async def verify_token_endpoint(current_user = Depends(get_current_user)):
    """Verify if token is valid."""
    return {
        "valid": True,
        "user": current_user.to_dict()
    }