"""Database connection and session management."""

import os
from contextlib import contextmanager
from typing import Generator, Optional

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.pool import QueuePool
    from quantlib_pro.data.models.base import Base
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None
    sessionmaker = None
    Session = None
    QueuePool = None
    Base = None


# Database URLs from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quantlib:devpassword@localhost:5433/quantlib_pro"
)

TIMESCALE_URL = os.getenv(
    "TIMESCALE_URL",
    "postgresql://quantlib:devpassword@localhost:5433/timeseries_db"
)

# Global engine and session variables (created lazily)
_postgres_engine = None
_timescale_engine = None
_PostgresSession = None
_TimescaleSession = None


def _get_postgres_engine():
    """Get or create PostgreSQL engine (lazy initialization)."""
    global _postgres_engine
    if not SQLALCHEMY_AVAILABLE:
        return None
    if _postgres_engine is None:
        try:
            _postgres_engine = create_engine(
                DATABASE_URL,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
        except Exception as e:
            print(f"Warning: Could not connect to PostgreSQL: {e}")
            return None
    return _postgres_engine


def _get_timescale_engine():
    """Get or create TimescaleDB engine (lazy initialization)."""
    global _timescale_engine
    if not SQLALCHEMY_AVAILABLE:
        return None
    if _timescale_engine is None:
        try:
            _timescale_engine = create_engine(
                TIMESCALE_URL,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
        except Exception as e:
            print(f"Warning: Could not connect to TimescaleDB: {e}")
            return None
    return _timescale_engine


def _get_postgres_session_factory():
    """Get PostgreSQL session factory (lazy initialization)."""
    global _PostgresSession
    if not SQLALCHEMY_AVAILABLE:
        return None
    engine = _get_postgres_engine()
    if engine is None:
        return None
    if _PostgresSession is None:
        _PostgresSession = sessionmaker(bind=engine, expire_on_commit=False)
    return _PostgresSession


def _get_timescale_session_factory():
    """Get TimescaleDB session factory (lazy initialization)."""
    global _TimescaleSession
    if not SQLALCHEMY_AVAILABLE:
        return None
    engine = _get_timescale_engine()
    if engine is None:
        return None
    if _TimescaleSession is None:
        _TimescaleSession = sessionmaker(bind=engine, expire_on_commit=False)
    return _TimescaleSession


# Module-level "constants" that are actually None (for graceful degradation)
# These prevent import errors when SQLAlchemy is not available
postgres_engine = None
timescale_engine = None
PostgresSession = None
TimescaleSession = None


def init_db() -> None:
    """Initialize database schemas (create all tables)."""
    if not SQLALCHEMY_AVAILABLE:
        print("Warning: SQLAlchemy not available, skipping database initialization")
        return
    
    engine = _get_postgres_engine()
    if engine is None:
        print("Warning: Could not connect to database, skipping initialization")
        return
        
    # Create PostgreSQL tables
    Base.metadata.create_all(bind=engine)
    print(" PostgreSQL tables created")
    
    # TimescaleDB tables will be created via Alembic migrations
    # (hypertables require special handling)
    print(" Database initialization complete")


def drop_db() -> None:
    """Drop all database tables (DANGEROUS - use only in dev/test)."""
    if not SQLALCHEMY_AVAILABLE:
        print("Warning: SQLAlchemy not available, cannot drop tables")
        return
        
    engine = _get_postgres_engine()
    if engine is None:
        print("Warning: Could not connect to database, cannot drop tables")
        return
        
    Base.metadata.drop_all(bind=engine)
    print(" PostgreSQL tables dropped")


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
