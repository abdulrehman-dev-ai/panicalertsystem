from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import AsyncGenerator

# Import routers from different services
from backend.auth_service.routes import router as auth_router
from backend.user_service.routes import router as user_router
from backend.alert_service.routes import router as alert_router
from backend.geofencing_service.routes import router as geofencing_router
from backend.media_service.routes import router as media_router
from backend.agent_service.routes import router as agent_router

# Import database and Kafka connections
from backend.database import init_database, check_database_connection
from backend.kafka_config import init_kafka, close_kafka
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Panic Alert System Backend...")
    
    try:
        # Initialize database
        init_database()
        if not check_database_connection():
            raise Exception("Database connection failed")
        logger.info("Database initialized successfully")
        
        # Initialize Kafka
        await init_kafka()
        logger.info("Kafka connection initialized")
        
        logger.info("Backend startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Panic Alert System Backend...")
    
    try:
        # Close Kafka connections
        await close_kafka()
        logger.info("Kafka connections closed")
        
        logger.info("Backend shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="Panic Alert System API",
    description="Backend API for the Panic Alert System with real-time emergency response capabilities",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "panic-alert-backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Panic Alert System API",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "Documentation disabled in production",
        "health": "/health"
    }

# Include routers with prefixes
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    user_router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    alert_router,
    prefix="/api/v1/alerts",
    tags=["Alerts"]
)

app.include_router(
    geofencing_router,
    prefix="/api/v1/geofencing",
    tags=["Geofencing"]
)

app.include_router(
    media_router,
    prefix="/api/v1/media",
    tags=["Media"]
)

app.include_router(
    agent_router,
    prefix="/api/v1/agents",
    tags=["Agents"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error occurred"
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )