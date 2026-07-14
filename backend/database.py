"""
Database module for the AI-CRM HCP Module.

Provides SQLAlchemy engine, session factory, declarative Base,
and a FastAPI dependency for obtaining database sessions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# For SQLite, we need connect_args to allow multi-threaded access
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy database session.

    Yields a session and ensures it is closed after the request completes,
    even if an exception occurs.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """
    Utility function that returns a new database session directly.

    Use this in non-FastAPI contexts (e.g., agent tools, scripts)
    where dependency injection is not available. The caller is
    responsible for closing the session.

    Returns:
        Session: A new SQLAlchemy database session.
    """
    return SessionLocal()
