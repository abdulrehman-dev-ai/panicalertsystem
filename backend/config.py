import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    APP_NAME: str = "Emergency Response System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/emergency_response_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "emergency_response_group"
    
    # Redis (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_EXPIRE_TIME: int = 3600  # 1 hour
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React admin portal
        "http://localhost:8080",  # Flutter web
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # Trusted hosts
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "*.localhost",
    ]
    
    # File storage
    MEDIA_ROOT: str = "media"
    MEDIA_URL: str = "/media/"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "video/mp4",
        "video/avi",
        "audio/mp3",
        "audio/wav",
        "application/pdf",
        "text/plain"
    ]
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = "noreply@emergencyresponse.com"
    
    # SMS settings (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Push notifications (Firebase)
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    
    # Geolocation settings
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    DEFAULT_LOCATION_ACCURACY: float = 10.0  # meters
    GEOFENCE_BUFFER_DISTANCE: float = 50.0  # meters
    
    # Alert settings
    ALERT_ESCALATION_TIMEOUT: int = 300  # 5 minutes
    MAX_ALERT_RADIUS: float = 10000.0  # 10km
    DEFAULT_ALERT_RADIUS: float = 1000.0  # 1km
    
    # Agent settings
    AGENT_LOCATION_UPDATE_INTERVAL: int = 30  # seconds
    AGENT_OFFLINE_TIMEOUT: int = 300  # 5 minutes
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    METRICS_ENABLED: bool = True
    
    # External APIs
    WEATHER_API_KEY: Optional[str] = None
    TRAFFIC_API_KEY: Optional[str] = None
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def assemble_file_types(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Global settings instance
settings = get_settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"

class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Override security settings for production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long in production")
        return v

class TestingSettings(Settings):
    """Testing environment settings."""
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/emergency_response_test_db"
    REDIS_URL: str = "redis://localhost:6379/1"
    
def get_environment_settings() -> Settings:
    """Get settings based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()