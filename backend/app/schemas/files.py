"""文件上传与预览相关 Schema。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PreviewTable(BaseModel):
    """表格预览（CSV/XLSX）。"""

    type: Literal["table"] = "table"
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class PreviewJson(BaseModel):
    """JSON/JSONL 预览。"""

    type: Literal["json"] = "json"
    value: Any = None


Preview = PreviewTable | PreviewJson


class UploadFileResponse(BaseModel):
    file_id: str
    detected_format: str
    field_candidates: list[str] = Field(default_factory=list)
    preview: Preview

