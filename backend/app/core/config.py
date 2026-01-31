"""配置管理（Pydantic v2）。

说明：
- Demo 优先使用 `backend/.env` 进行配置（env_file=".env"）。
- 涉及磁盘路径时尽量用相对路径（相对 backend/），便于不同环境直接运行。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置（可通过环境变量或 backend/.env 覆盖）。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- 基础 ---
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    # 默认仅放行本机前端（Vite dev server / preview 常见端口）
    # 说明：
    # - 推荐开发期使用 Vite proxy（浏览器同源，不需要 CORS）。
    # - 只有在“前端直连后端（跨端口）”时才需要配置该项。
    # - 支持两种写法：
    #   1) 逗号分隔：CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    #   2) JSON 数组：CORS_ALLOW_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
    CORS_ALLOW_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )

    # --- DB ---
    DATABASE_URL: str = "sqlite:///./data_translator.db"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- 本地存储（相对 backend/）---
    STORAGE_DIR: Path = Field(default=Path("./storage"))
    UPLOADS_DIR: Path = Field(default=Path("./storage/uploads"))
    EXPORTS_DIR: Path = Field(default=Path("./storage/exports"))

    # --- LLM：火山方舟（OpenAI SDK 兼容）---
    ARK_API_KEY: str = ""
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_MODEL: str = "doubao-seed-1-6-lite-251015"
    ARK_RPM: int = 1000
    # 默认关闭深度思考，提升翻译吞吐与稳定性
    ARK_DISABLE_THINKING: bool = True

    # --- 翻译策略 ---
    TRANSLATION_MAX_CELL_CHARS: int = 10000
    TRANSLATION_BATCH_SIZE: int = 20

    # 开发调试：不调用外部模型，使用 mock 翻译（用于本地联调）
    TRANSLATION_DRY_RUN: bool = False

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_allow_origins(cls, v: object) -> object:
        """把环境变量中的 CORS_ALLOW_ORIGINS 解析为 list[str]。"""

        if v is None:
            return v

        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []

            # 允许 JSON 数组写法
            if s.startswith("[") and s.endswith("]"):
                try:
                    import json

                    data = json.loads(s)
                    if isinstance(data, list):
                        out = [str(x).strip() for x in data if str(x).strip()]
                        return out
                except Exception:  # noqa: BLE001
                    pass

            # 兜底：逗号分隔
            return [x.strip() for x in s.split(",") if x.strip()]

        return v


settings = Settings()

