"""翻译任务相关接口。"""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.paths import is_within_dir, resolve_backend_path
from app.db.session import get_db
from app.models.translation_job import TranslationJob
from app.models.uploaded_file import UploadedFile
from app.schemas.jobs import CreateJobRequest, CreateJobResponse, JobStatusResponse
from app.tasks.translate import translate_job_task

router = APIRouter()


@router.post("", response_model=CreateJobResponse)
def create_job(req: CreateJobRequest, db: Session = Depends(get_db)) -> CreateJobResponse:
    """创建翻译任务并投递到 Celery。"""

    uploaded = db.get(UploadedFile, req.file_id)
    if not uploaded:
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    # 选择字段/列为强约束：否则任务没有实际意义
    if not req.selected_fields:
        raise HTTPException(status_code=400, detail="请选择至少一个字段/列")

    job = TranslationJob(
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
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    """查询任务状态与进度。"""

    job = db.get(TranslationJob, job_id)
    if not job:
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
def download(job_id: str, db: Session = Depends(get_db)) -> Any:
    """下载导出结果。"""

    job = db.get(TranslationJob, job_id)
    if not job:
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

