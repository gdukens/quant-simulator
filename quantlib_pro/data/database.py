"""Database connection and session management."""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from quantlib_pro.data.models.base import Base


# Database URLs from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quantlib:changeme@localhost:5432/quantlib_db"
)

TIMESCALE_URL = os.getenv(
    "TIMESCALE_URL",
    "postgresql://quantlib:changeme@localhost:5433/timeseries_db"
)

# PostgreSQL engine (transactional data)
postgres_engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False,          # Set to True for SQL debug logging
)

# TimescaleDB engine (time-series data)
timescale_engine = create_engine(
    TIMESCALE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Session factories
PostgresSession = sessionmaker(bind=postgres_engine, expire_on_commit=False)
TimescaleSession = sessionmaker(bind=timescale_engine, expire_on_commit=False)


def init_db() -> None:
    """Initialize database schemas (create all tables)."""
    # Create PostgreSQL tables
    Base.metadata.create_all(bind=postgres_engine)
    print("✓ PostgreSQL tables created")
    
    # TimescaleDB tables will be created via Alembic migrations
    # (hypertables require special handling)
    print("✓ Database initialization complete")


def drop_db() -> None:
    """Drop all database tables (DANGEROUS - use only in dev/test)."""
    Base.metadata.drop_all(bind=postgres_engine)
    print("✓ PostgreSQL tables dropped")


@contextmanager
def get_postgres_session() -> Generator[Session, None, None]:
    """Context manager for PostgreSQL database sessions.
    
    Usage:
        with get_postgres_session() as session:
            user = session.query(User).first()
    """
    session = PostgresSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_timescale_session() -> Generator[Session, None, None]:
    """Context manager for TimescaleDB database sessions.
    
    Usage:
        with get_timescale_session() as session:
            prices = session.query(Price).filter_by(ticker='AAPL').all()
    """
    session = TimescaleSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_postgres_session_sync() -> Session:
    """Get a PostgreSQL session (manual management required).
    
    Usage:
        session = get_postgres_session_sync()
        try:
            user = session.query(User).first()
            session.commit()
        finally:
            session.close()
    """
    return PostgresSession()


def get_timescale_session_sync() -> Session:
    """Get a TimescaleDB session (manual management required)."""
    return TimescaleSession()
