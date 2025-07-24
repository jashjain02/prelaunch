from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
import os

# Heroku Postgres credentials
HEROKU_DATABASE_URL = "postgresql://ufnm38v543cc8b:p204b52508d79872aacc0b43f9c9efe67118dc4c54d888a9059d01a7b3c05147c@c3v5n5ajfopshl.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfhak67qpimir3"

# Use DATABASE_URL from env if present (for Heroku), else fallback to hardcoded Heroku URI
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", HEROKU_DATABASE_URL)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with SSL required for Heroku
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
    connect_args={"sslmode": "require"}
)

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
        
        




