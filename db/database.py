import os
from datetime import datetime, timezone, timedelta

# Use DATABASE_URL from env, fallback to local Postgres for development
# Production/Remote Database URL (commented out)
# SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or "postgres://ufnm38v543cc8b:p204b52508d79872aacc0b43f9c9efe67118dc4c54d888a9059d01a7b3c05147c@c3v5n5ajfopshl.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfhak67qpimir3"

# Local Database URL
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://postgres:jash.doers@localhost:5432/postgres"

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# Indian Standard Time (UTC+5:30)
IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

# Create engine with proper configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
    # connect_args={"sslmode": "require"}  # Uncomment for Heroku/SSL
)

# Set timezone to IST for all database connections
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
        
        




