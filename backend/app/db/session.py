"""数据库 Session 管理（SQLAlchemy 2.0）。"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _is_sqlite(url: str) -> bool:
    return str(url or "").strip().lower().startswith("sqlite")


connect_args = {"check_same_thread": False} if _is_sqlite(settings.DATABASE_URL) else {}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：获取一个 DB Session。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

