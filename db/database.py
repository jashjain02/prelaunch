import os
from datetime import datetime, timezone, timedelta

# Use DATABASE_URL from environment variable only
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Convert postgres:// to postgresql:// for SQLAlchemy compatibility
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# Indian Standard Time (UTC+5:30)
IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

# Create engine with proper configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Set to False in production
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
    connect_args={"sslmode": "require"}  # Enable SSL for Heroku
)

# Set timezone to IST for all database connections (PostgreSQL only)
if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_timezone(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET timezone = 'Asia/Kolkata';")
        cursor.close()

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class DBSession:
    @staticmethod
    def get_session():
        return scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    
    @staticmethod
    def get_connection():
        return engine.connect()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        




