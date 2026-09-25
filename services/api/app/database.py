"""
Database engine, session factory, and declarative base.

All models import Base from here. All request handlers receive a Session
via the get_db dependency in dependencies.py.
"""

from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


def _build_engine():
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,   # avoids stale connections after Postgres restart
        pool_size=10,
        max_overflow=20,
    )

    # Ensure PostGIS extension is available on first connection.
    # In production this should be done via migration; this is a dev safety net.
    @event.listens_for(engine, "connect")
    def _enable_postgis(dbapi_conn, _record):
        with dbapi_conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        dbapi_conn.commit()

    return engine


engine = _build_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


class Base(DeclarativeBase):
    """Shared declarative base — all ORM models inherit from this."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request,
    rolling back on exception and always closing.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
