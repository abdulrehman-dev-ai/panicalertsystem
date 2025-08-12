from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/emergency_response_db"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=30,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db() -> Generator:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables in the database."""
    Base.metadata.drop_all(bind=engine)

def get_engine():
    """Get the database engine."""
    return engine

def get_session():
    """Get a new database session."""
    return SessionLocal()

# Database health check
def check_database_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Database initialization
def init_database():
    """Initialize the database with tables and initial data."""
    try:
        # Create all tables
        create_tables()
        print("Database tables created successfully")
        
        # Check connection
        if check_database_connection():
            print("Database connection established successfully")
        else:
            print("Failed to establish database connection")
            
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise e

# Connection string for Alembic
def get_database_url() -> str:
    """Get the database URL for Alembic migrations."""
    return DATABASE_URL