from __future__ import annotations

"""匿名会话（同一浏览器）任务归属测试。

目标：
- 不做账号体系的情况下，仍然确保“关页可找回、跨浏览器隔离”；
- job_id 不能成为访问钥匙：换浏览器拿到 job_id 也应无法查询/下载。

说明：
- 这里使用 FastAPI TestClient 做轻量集成测试；
- 由于创建任务会投递 Celery（依赖 Redis），测试中会 stub 掉 `.delay()`，避免外部依赖。
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db import init_db as init_db_mod
from app.db import session as session_mod
from app.main import app


@pytest.fixture()
def isolated_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """隔离 DB 与文件存储目录，避免污染本地开发数据。"""

    # 1) 隔离存储目录：使用临时绝对路径（resolve_backend_path 会原样返回）
    storage_dir = tmp_path / "storage"
    uploads_dir = storage_dir / "uploads"
    exports_dir = storage_dir / "exports"
    monkeypatch.setattr(settings, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(settings, "UPLOADS_DIR", uploads_dir)
    monkeypatch.setattr(settings, "EXPORTS_DIR", exports_dir)

    # 2) 隔离 DB：使用临时 sqlite 文件
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True, echo=False)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    # 注意：init_db 模块内部缓存了 engine 引用，需同步替换
    monkeypatch.setattr(session_mod, "engine", engine)
    monkeypatch.setattr(session_mod, "SessionLocal", SessionLocal)
    monkeypatch.setattr(init_db_mod, "engine", engine)

    # 预创建表结构（也会在 TestClient 触发 startup 时再次执行，重复无副作用）
    init_db_mod.init_db()


def test_anonymous_session_job_ownership(isolated_runtime: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """同一浏览器可查；换浏览器（新 cookie）不可查。"""

    # stub：避免测试依赖 Redis/Celery
    import app.api.endpoints.jobs as jobs_ep

    monkeypatch.setattr(jobs_ep.translate_job_task, "delay", lambda *_args, **_kwargs: None)

    # --- 浏览器 A：创建上传与任务 ---
    client_a = TestClient(app)
    try:
        r = client_a.post(
            "/api/v1/files/upload",
            files={"file": ("demo.json", b'{"a":"hello"}', "application/json")},
        )
        assert r.status_code == 200
        assert "dt_client_id=" in (r.headers.get("set-cookie") or "")
        file_id = r.json()["file_id"]

        r = client_a.post(
            "/api/v1/jobs",
            json={
                "file_id": file_id,
                "selected_fields": ["a"],
                "row_limit": 1,
                "mode": "add_columns",
                "target_lang": "zh-CN",
            },
        )
        assert r.status_code == 200
        job_id = r.json()["job_id"]

        # 同一浏览器可查询
        r = client_a.get(f"/api/v1/jobs/{job_id}")
        assert r.status_code == 200

        # 同一浏览器可列表找回
        r = client_a.get("/api/v1/jobs?limit=20&offset=0")
        assert r.status_code == 200
        jobs = r.json()["jobs"]
        assert any(j["job_id"] == job_id for j in jobs)
    finally:
        client_a.close()

    # --- 浏览器 B：无法访问浏览器 A 的任务 ---
    client_b = TestClient(app)
    try:
        # 任务查询：返回 404（不泄露是否存在）
        r = client_b.get(f"/api/v1/jobs/{job_id}")
        assert r.status_code == 404

        # 下载：也应 404（归属校验在前）
        r = client_b.get(f"/api/v1/jobs/{job_id}/download")
        assert r.status_code == 404

        # 不能用别人的 file_id 创建任务
        r = client_b.post(
            "/api/v1/jobs",
            json={
                "file_id": file_id,
                "selected_fields": ["a"],
                "row_limit": 1,
                "mode": "add_columns",
                "target_lang": "zh-CN",
            },
        )
        assert r.status_code == 404

        # 列表隔离：应为空
        r = client_b.get("/api/v1/jobs?limit=20&offset=0")
        assert r.status_code == 200
        assert r.json()["jobs"] == []
    finally:
        client_b.close()

