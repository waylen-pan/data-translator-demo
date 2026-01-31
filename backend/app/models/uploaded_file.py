"""上传文件表。"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UploadedFile(Base):
    """用户上传的原始文件信息（仅存元数据与本地存储路径）。"""

    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # 自动识别的数据格式：json/jsonl/csv/xlsx/unknown
    detected_format: Mapped[str] = mapped_column(String(32), default="unknown")

    # 相对路径（相对 backend/），便于迁移运行
    storage_path: Mapped[str] = mapped_column(String(1024))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

