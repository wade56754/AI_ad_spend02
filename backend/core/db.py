from __future__ import annotations

from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.core.config import get_settings

Base = declarative_base()

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """Lazily create and return the SQLAlchemy engine instance."""
    global _engine

    if _engine is None:
        settings = get_settings()
        database_url = getattr(settings, "database_url", None)
        if not database_url:
            raise RuntimeError("DATABASE_URL 未配置，无法初始化数据库连接")
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)

    return _engine


def get_session_factory() -> sessionmaker:
    """Return a lazily-created session factory bound to the engine."""
    global _SessionFactory

    if _SessionFactory is None:
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

    return _SessionFactory


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
