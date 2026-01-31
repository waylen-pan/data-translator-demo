"""翻译任务相关 Schema。"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class CreateJobRequest(BaseModel):
    file_id: str
    selected_fields: list[str] = Field(default_factory=list)
    row_limit: int = Field(default=50, ge=1, le=5000)
    mode: Literal["add_columns", "overwrite"] = "add_columns"
    target_lang: str = "zh-CN"

    @field_validator("selected_fields", mode="before")
    @classmethod
    def _normalize_selected_fields(cls, v: object) -> object:
        """清洗字段/列选择：
        - 去掉空字符串与纯空白
        - 去重（保留顺序）
        """

        if v is None:
            return []
        if not isinstance(v, list):
            return v

        out: list[str] = []
        seen: set[str] = set()
        for x in v:
            s = str(x).strip()
            if not s:
                continue
            if s in seen:
                continue
            out.append(s)
            seen.add(s)
        return out


class CreateJobResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    file_id: str
    status: str
    mode: str
    target_lang: str
    row_limit: int
    selected_fields: list[str] = Field(default_factory=list)

    progress_total: int
    progress_done: int
    progress_failed: int

    error_message: str = ""
    download_url: Optional[str] = None

