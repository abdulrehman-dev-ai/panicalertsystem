from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import redis.asyncio as redis
from typing import AsyncGenerator, Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup for PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

# Global database connections
postgres_engine = None
mongo_client: Optional[AsyncIOMotorClient] = None
mongo_db = None
redis_client: Optional[redis.Redis] = None

async def init_db():
    """Initialize all database connections."""
    global postgres_engine, mongo_client, mongo_db, redis_client
    
    try:
        # PostgreSQL connection
        postgres_engine = engine
        logger.info("PostgreSQL connection initialized")
        
        # MongoDB connection
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db = mongo_client[settings.MONGODB_DB]
        
        # Test MongoDB connection
        await mongo_client.admin.command('ping')
        logger.info("MongoDB connection initialized")
        
        # Redis connection
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("Redis connection initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        raise

async def close_db():
    """Close all database connections."""
    global postgres_engine, mongo_client, redis_client
    
    try:
        if postgres_engine:
            postgres_engine.dispose()
            logger.info("PostgreSQL connection closed")
        
        if mongo_client:
            mongo_client.close()
            logger.info("MongoDB connection closed")
        
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")
            
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

# Dependency for getting PostgreSQL session
def get_db() -> Session:
    """Get PostgreSQL database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency for getting MongoDB database
async def get_mongo_db():
    """Get MongoDB database instance."""
    if mongo_db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo_db

# Dependency for getting Redis client
async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis not initialized")
    return redis_client

# Database models base class
class DatabaseModel(Base):
    """Base class for all database models."""
    __abstract__ = True
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# MongoDB collections helper
class MongoCollections:
    """Helper class for MongoDB collection access."""
    
    @staticmethod
    async def get_collection(collection_name: str):
        """Get MongoDB collection by name."""
        db = await get_mongo_db()
        return db[collection_name]
    
    @staticmethod
    async def alert_events():
        """Get alert events collection."""
        return await MongoCollections.get_collection("alert_events")
    
    @staticmethod
    async def location_events():
        """Get location events collection."""
        return await MongoCollections.get_collection("location_events")
    
    @staticmethod
    async def media_events():
        """Get media events collection."""
        return await MongoCollections.get_collection("media_events")
    
    @staticmethod
    async def geofence_events():
        """Get geofence events collection."""
        return await MongoCollections.get_collection("geofence_events")
    
    @staticmethod
    async def system_logs():
        """Get system logs collection."""
        return await MongoCollections.get_collection("system_logs")

# Redis keys helper
class RedisKeys:
    """Helper class for Redis key management."""
    
    @staticmethod
    def user_session(user_id: str) -> str:
        return f"session:user:{user_id}"
    
    @staticmethod
    def agent_session(agent_id: str) -> str:
        return f"session:agent:{agent_id}"
    
    @staticmethod
    def alert_cache(alert_id: str) -> str:
        return f"alert:cache:{alert_id}"
    
    @staticmethod
    def user_location(user_id: str) -> str:
        return f"location:user:{user_id}"
    
    @staticmethod
    def agent_location(agent_id: str) -> str:
        return f"location:agent:{agent_id}"
    
    @staticmethod
    def rate_limit(identifier: str) -> str:
        return f"rate_limit:{identifier}"
    
    @staticmethod
    def geofence_cache(zone_id: str) -> str:
        return f"geofence:cache:{zone_id}"

# Database health check
async def check_database_health() -> dict:
    """Check the health of all database connections."""
    health_status = {
        "postgres": False,
        "mongodb": False,
        "redis": False
    }
    
    try:
        # Check PostgreSQL
        with SessionLocal() as db:
            db.execute("SELECT 1")
            health_status["postgres"] = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
    
    try:
        # Check MongoDB
        if mongo_client:
            await mongo_client.admin.command('ping')
            health_status["mongodb"] = True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    try:
        # Check Redis
        if redis_client:
            await redis_client.ping()
            health_status["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    return health_status