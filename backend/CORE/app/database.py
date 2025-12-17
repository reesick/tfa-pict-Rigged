"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional

# Base class for all models - can be imported without database connection
Base = declarative_base()

# Lazy-loaded globals
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine (lazy initialization)."""
    global _engine
    if _engine is None:
        from app.config import get_settings
        settings = get_settings()
        
        # Detect if using SQLite (for testing) or PostgreSQL
        if settings.database_url.startswith('sqlite'):
            _engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False}
            )
        else:
            _engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,      # Verify connections before using
                pool_size=20,            # Persistent connections
                max_overflow=40,         # Additional connections during peak
                pool_recycle=3600        # Recycle connections every hour
            )
    return _engine


def get_session_local():
    """Get or create SessionLocal factory (lazy initialization)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal


# For backwards compatibility - lazy properties
@property
def engine():
    return get_engine()


@property
def SessionLocal():
    return get_session_local()


def get_db():
    """
    Dependency for FastAPI routes to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_engine():
    """Reset engine for testing purposes."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
