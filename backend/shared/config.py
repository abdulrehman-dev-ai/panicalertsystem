from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application settings
    APP_NAME: str = "Panic Alert System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security settings
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Alternative dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # Database settings - PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "panic_alert_db"
    POSTGRES_USER: str = "panic_user"
    POSTGRES_PASSWORD: str = "panic_password_2024"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # MongoDB settings
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = "panic_events"
    MONGODB_USER: str = "panic_admin"
    MONGODB_PASSWORD: str = "panic_mongo_2024"
    
    @property
    def MONGODB_URL(self) -> str:
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}?authSource=admin"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_password_2024"
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: List[str] = ["localhost:9092"]
    KAFKA_GROUP_ID: str = "panic-alert-backend"
    KAFKA_AUTO_OFFSET_RESET: str = "latest"
    
    # Kafka topics
    KAFKA_TOPICS = {
        "PANIC_ALERTS": "panic-alerts",
        "ALERT_RESPONSES": "alert-responses",
        "ALERT_STATUS_UPDATES": "alert-status-updates",
        "USER_EVENTS": "user-events",
        "AGENT_EVENTS": "agent-events",
        "LOCATION_UPDATES": "location-updates",
        "GEOFENCE_EVENTS": "geofence-events",
        "MEDIA_UPLOADS": "media-uploads",
        "MEDIA_PROCESSING": "media-processing",
        "PUSH_NOTIFICATIONS": "push-notifications",
        "SMS_NOTIFICATIONS": "sms-notifications",
        "EMAIL_NOTIFICATIONS": "email-notifications",
        "SYSTEM_EVENTS": "system-events",
        "AUDIT_LOGS": "audit-logs"
    }
    
    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/webm", "video/quicktime"]
    ALLOWED_AUDIO_TYPES: List[str] = ["audio/mpeg", "audio/wav", "audio/webm"]
    
    # Media storage settings
    MEDIA_STORAGE_PATH: str = "./media"
    MEDIA_BASE_URL: str = "/media"
    
    # External service settings
    # Twilio for SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # Email settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    
    # Push notification settings
    FCM_SERVER_KEY: str = ""
    APNS_KEY_ID: str = ""
    APNS_TEAM_ID: str = ""
    APNS_BUNDLE_ID: str = ""
    
    # Geofencing settings
    DEFAULT_GEOFENCE_RADIUS: int = 1000  # meters
    MAX_GEOFENCE_RADIUS: int = 10000  # meters
    
    # Alert settings
    MAX_ALERT_RESPONSE_TIME_MINUTES: int = 15
    AUTO_ESCALATE_AFTER_MINUTES: int = 5
    MAX_EMERGENCY_CONTACTS: int = 5
    
    # Security settings
    ENABLE_MFA: bool = False
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure media directory exists
Path(settings.MEDIA_STORAGE_PATH).mkdir(parents=True, exist_ok=True)