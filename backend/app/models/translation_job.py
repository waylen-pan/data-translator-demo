"""翻译任务表。"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TranslationJob(Base):
    """一次翻译任务（后台 Celery 执行）。"""

    __tablename__ = "translation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("uploaded_files.id"), index=True)

    # pending/running/succeeded/failed
    status: Mapped[str] = mapped_column(String(16), default="pending")

    # add_columns（默认：新增 *_zh）/ overwrite（覆盖原值）
    mode: Mapped[str] = mapped_column(String(16), default="add_columns")

    target_lang: Mapped[str] = mapped_column(String(16), default="zh-CN")

    # 仅翻译前 N 行/条
    row_limit: Mapped[int] = mapped_column(Integer, default=50)

    # 前端选择的字段/列（格式由适配器解释）
    selected_fields: Mapped[object] = mapped_column(JSON, default=list)

    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    progress_done: Mapped[int] = mapped_column(Integer, default=0)
    progress_failed: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str] = mapped_column(String(2048), default="")

    # 导出文件相对路径（相对 backend/）
    result_path: Mapped[str] = mapped_column(String(1024), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

