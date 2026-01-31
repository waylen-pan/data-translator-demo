"""数据库初始化（Demo：启动时自动建表）。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.models.uploaded_file import UploadedFile


def init_db() -> None:
    """创建表并做最小健康校验。"""

    Base.metadata.create_all(bind=engine)

    # 轻量校验：至少能跑通一次查询
    with Session(engine) as db:
        db.execute(select(UploadedFile.id).limit(1))

