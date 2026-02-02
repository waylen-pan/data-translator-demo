"""翻译任务相关接口。"""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.paths import is_within_dir, resolve_backend_path
from app.db.session import get_db
from app.models.translation_job import TranslationJob
from app.models.uploaded_file import UploadedFile
from app.schemas.jobs import CreateJobRequest, CreateJobResponse, JobListItem, JobListResponse, JobStatusResponse
from app.tasks.translate import translate_job_task

router = APIRouter()


@router.get("", response_model=JobListResponse)
def list_jobs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """列出当前匿名会话（同一浏览器）的历史任务。

    说明：
    - 这是“关网页后仍可找回任务结果”的关键接口；
    - 必须按 client_id 过滤，否则会把 job_id 变成“访问钥匙”。
    """

    client_id = getattr(request.state, "client_id", "") or ""
    if not client_id:
        raise HTTPException(status_code=500, detail="匿名会话未初始化，请刷新后重试")

    stmt = (
        select(TranslationJob, UploadedFile.filename)
        .join(UploadedFile, UploadedFile.id == TranslationJob.file_id, isouter=True)
        .where(TranslationJob.client_id == client_id)
        .order_by(TranslationJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(stmt).all()

    jobs: list[JobListItem] = []
    for job, filename in rows:
        download_url = None
        if job.status == "succeeded" and job.result_path:
            download_url = f"{settings.API_V1_PREFIX}/jobs/{job.id}/download"

        selected_fields = job.selected_fields
        if not isinstance(selected_fields, list):
            selected_fields = []

        jobs.append(
            JobListItem(
                job_id=job.id,
                file_id=job.file_id,
                filename=str(filename or ""),
                status=job.status,
                mode=job.mode,
                target_lang=job.target_lang,
                row_limit=int(job.row_limit or 0),
                selected_fields=cast(list[str], selected_fields),
                progress_total=int(job.progress_total or 0),
                progress_done=int(job.progress_done or 0),
                progress_failed=int(job.progress_failed or 0),
                error_message=job.error_message or "",
                download_url=download_url,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
        )

    return JobListResponse(jobs=jobs, limit=limit, offset=offset)


@router.post("", response_model=CreateJobResponse)
def create_job(req: CreateJobRequest, request: Request, db: Session = Depends(get_db)) -> CreateJobResponse:
    """创建翻译任务并投递到 Celery。"""

    uploaded = db.get(UploadedFile, req.file_id)
    if not uploaded:
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    # 归属校验：同一浏览器（匿名会话）才能使用自己的上传文件创建任务
    client_id = getattr(request.state, "client_id", "") or ""
    if not client_id:
        raise HTTPException(status_code=500, detail="匿名会话未初始化，请刷新后重试")
    if uploaded.client_id != client_id:
        # 返回 404，避免泄露“该 file_id 是否存在”
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    # 选择字段/列为强约束：否则任务没有实际意义
    if not req.selected_fields:
        raise HTTPException(status_code=400, detail="请选择至少一个字段/列")

    job = TranslationJob(
        client_id=client_id,
        file_id=uploaded.id,
        status="pending",
        mode=req.mode,
        target_lang=req.target_lang,
        row_limit=req.row_limit,
        selected_fields=req.selected_fields,
        progress_total=0,
        progress_done=0,
        progress_failed=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 投递后台任务：由 worker 更新 status/progress/result
    translate_job_task.delay(job.id)

    return CreateJobResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, request: Request, db: Session = Depends(get_db)) -> JobStatusResponse:
    """查询任务状态与进度。"""

    job = db.get(TranslationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 归属校验：同一浏览器才能查询自己的任务
    client_id = getattr(request.state, "client_id", "") or ""
    if not client_id:
        raise HTTPException(status_code=500, detail="匿名会话未初始化，请刷新后重试")
    if job.client_id != client_id:
        raise HTTPException(status_code=404, detail="任务不存在")

    download_url = None
    if job.status == "succeeded" and job.result_path:
        download_url = f"{settings.API_V1_PREFIX}/jobs/{job.id}/download"

    selected_fields = job.selected_fields
    if not isinstance(selected_fields, list):
        selected_fields = []

    return JobStatusResponse(
        job_id=job.id,
        file_id=job.file_id,
        status=job.status,
        mode=job.mode,
        target_lang=job.target_lang,
        row_limit=job.row_limit,
        selected_fields=cast(list[str], selected_fields),
        progress_total=int(job.progress_total or 0),
        progress_done=int(job.progress_done or 0),
        progress_failed=int(job.progress_failed or 0),
        error_message=job.error_message or "",
        download_url=download_url,
    )


@router.get("/{job_id}/download")
def download(job_id: str, request: Request, db: Session = Depends(get_db)) -> Any:
    """下载导出结果。"""

    job = db.get(TranslationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 归属校验：同一浏览器才能下载自己的导出文件
    client_id = getattr(request.state, "client_id", "") or ""
    if not client_id:
        raise HTTPException(status_code=500, detail="匿名会话未初始化，请刷新后重试")
    if job.client_id != client_id:
        raise HTTPException(status_code=404, detail="任务不存在")

    if job.status != "succeeded" or not job.result_path:
        raise HTTPException(status_code=400, detail="任务未完成，无法下载")

    path = resolve_backend_path(job.result_path)
    exports_dir = resolve_backend_path(settings.EXPORTS_DIR)
    if not is_within_dir(path, exports_dir):
        raise HTTPException(status_code=400, detail="导出文件路径非法")
    if not path.exists():
        raise HTTPException(status_code=404, detail="导出文件不存在（可能已被清理）")

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/octet-stream",
    )

