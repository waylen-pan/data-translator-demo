"""API 总路由入口。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import files, jobs

api_router = APIRouter()

api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

