"""SQLAlchemy Declarative Base。"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM Model 的基类。"""

