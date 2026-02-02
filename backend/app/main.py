"""FastAPI 应用入口。"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.paths import resolve_backend_path
from app.db.init_db import init_db
from app.middlewares.client_id import ClientIdCookieMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """应用生命周期（启动/退出）。

    说明：
    - 使用 lifespan 替代 on_event（FastAPI 已标记 on_event 为 deprecated）。
    """

    # 确保存储目录存在（默认相对 backend/）
    for p in [settings.STORAGE_DIR, settings.UPLOADS_DIR, settings.EXPORTS_DIR]:
        resolve_backend_path(p).mkdir(parents=True, exist_ok=True)

    # 初始化数据库（Demo：自动建表）
    init_db()

    # 避免某些环境下相对路径混乱：打印一次当前工作目录（仅用于启动诊断）
    if settings.APP_DEBUG:
        _cwd = os.getcwd()
        print(f"[startup] cwd={_cwd}")

    yield


app = FastAPI(
    title="数据翻译器 Demo API",
    version="0.1.0",
    lifespan=lifespan,
)

# 匿名会话 Cookie：用于“同一浏览器”级别的任务归属与找回
app.add_middleware(ClientIdCookieMiddleware)

# CORS（按最佳实践尽量收敛默认放行范围）
# - 开发期推荐使用 Vite proxy（浏览器同源，不需要 CORS）
# - 如需“前端直连后端（跨端口）”，请在 `.env` 中配置 `CORS_ALLOW_ORIGINS`
if settings.CORS_ALLOW_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", summary="根路径占位")
def root() -> dict[str, str]:
    return {"message": "数据翻译器 Demo API"}

