"""数据库初始化（Demo：启动时自动建表）。"""

from __future__ import annotations

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401
from app.models.uploaded_file import UploadedFile


def _assert_schema_compatible() -> None:
    """启动期 schema 校验（失败要给出明确的修复方式）。

    说明：
    - SQLAlchemy 的 create_all 只负责“建表”，不会对已有表做 ALTER；
    - 本项目不做向后兼容：当 schema 升级时，要求一次性重建 DB/数据卷；
    - 因此这里做一次“是否缺字段”的快速检测，避免用户踩到更难读的 SQL 报错。
    """

    insp = inspect(engine)
    required = {
        "uploaded_files": {"client_id"},
        "translation_jobs": {"client_id"},
    }

    missing: list[str] = []
    for table, required_cols in required.items():
        if not insp.has_table(table):
            continue
        cols = {c.get("name") for c in insp.get_columns(table)}
        for col in required_cols:
            if col not in cols:
                missing.append(f"{table}.{col}")

    if missing:
        raise RuntimeError(
            "数据库结构过旧（缺少字段："
            + ", ".join(missing)
            + "）。\n"
            + "本项目不做向后兼容，请重建数据库/数据卷：\n"
            + "- Docker：docker compose down -v && docker compose up -d --build\n"
            + "- SQLite：删除 backend/data_translator.db 后重启后端\n"
        )


def init_db() -> None:
    """创建表并做最小健康校验。"""

    Base.metadata.create_all(bind=engine)
    _assert_schema_compatible()

    # 轻量校验：至少能跑通一次查询
    with Session(engine) as db:
        db.execute(select(UploadedFile.id).limit(1))

