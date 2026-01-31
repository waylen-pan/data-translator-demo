"""翻译任务（Celery）。

说明：
- 任务状态以 DB 为准（前端轮询 `/api/v1/jobs/{job_id}`）。
- 导出文件写入 `settings.EXPORTS_DIR`，并把相对路径写回 DB。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.paths import BACKEND_ROOT, resolve_backend_path
from app.db.session import SessionLocal
from app.models.translation_job import TranslationJob
from app.models.uploaded_file import UploadedFile
from app.services.adapters.registry import get_adapter
from app.services.translator.ark_translator import TranslateItem, build_default_translator


@celery_app.task(name="app.tasks.translate.translate_job_task")
def translate_job_task(job_id: str) -> dict[str, str]:
    """后台翻译任务入口。"""

    # 1) 读取任务与文件元信息
    with SessionLocal() as db:
        job = db.get(TranslationJob, job_id)
        if not job:
            return {"job_id": job_id, "status": "missing"}

        uploaded = db.get(UploadedFile, job.file_id)
        if not uploaded:
            job.status = "failed"
            job.error_message = "找不到上传文件记录"
            db.commit()
            return {"job_id": job_id, "status": "failed"}

        adapter = get_adapter(uploaded.detected_format)
        if adapter is None:
            job.status = "failed"
            job.error_message = f"暂不支持该格式: {uploaded.detected_format}"
            db.commit()
            return {"job_id": job_id, "status": "failed"}

        file_path = resolve_backend_path(uploaded.storage_path)
        export_dir = resolve_backend_path(settings.EXPORTS_DIR)

        selected_fields_obj: Any = job.selected_fields
        selected_fields: list[str] = selected_fields_obj if isinstance(selected_fields_obj, list) else []
        selected_fields = [str(x) for x in selected_fields if str(x).strip()]

        # 2) 准备翻译单元（并初始化进度）
        prepared = adapter.prepare(
            file_path=file_path,
            selected_fields=selected_fields,
            row_limit=int(job.row_limit or 0),
            mode=job.mode,
            target_lang=job.target_lang,
            export_dir=export_dir,
            job_id=job.id,
        )

        items: list[TranslateItem] = prepared.items
        job.status = "running"
        job.error_message = ""
        job.progress_total = len(items)
        job.progress_done = 0
        job.progress_failed = 0
        job.result_path = ""
        db.commit()

        # 把必要字段拷贝出来，避免下方持有 ORM 对象
        target_lang = job.target_lang
        mode = job.mode

    # 3) 执行翻译（分批更新进度）
    # 开发联调：允许使用 mock 翻译，便于在没有 Key 的情况下走通全链路
    if settings.TRANSLATION_DRY_RUN:
        class _MockTranslator:
            def translate_items(self, xs: list[TranslateItem], *, target_lang: str) -> dict[str, str]:  # noqa: ARG002
                return {it.id: f"【mock】{it.text}" for it in xs}

        translator: Any = _MockTranslator()
    else:
        try:
            translator = build_default_translator()
        except Exception as e:  # noqa: BLE001
            with SessionLocal() as db:
                job = db.get(TranslationJob, job_id)
                if job:
                    job.status = "failed"
                    job.error_message = f"初始化翻译器失败: {str(e)[:200]}"
                    db.commit()
            return {"job_id": job_id, "status": "failed"}

    translations: dict[str, str] = {}

    # cell-level 批次：用于更新进度
    # - 数值越小，前端进度条越“实时”，但 DB 写入更频繁
    # - 使用 settings.TRANSLATION_BATCH_SIZE 作为可调参数（默认 20）
    cell_batch_size = max(1, int(getattr(settings, "TRANSLATION_BATCH_SIZE", 20) or 20))
    try:
        for i in range(0, len(items), cell_batch_size):
            chunk = items[i : i + cell_batch_size]
            chunk_map = translator.translate_items(chunk, target_lang=target_lang)
            translations.update(chunk_map)

            with SessionLocal() as db:
                job = db.get(TranslationJob, job_id)
                if job:
                    job.progress_done = min(int(job.progress_total or 0), int(job.progress_done or 0) + len(chunk))
                    db.commit()
    except Exception as e:  # noqa: BLE001
        with SessionLocal() as db:
            job = db.get(TranslationJob, job_id)
            if job:
                job.status = "failed"
                job.error_message = f"翻译失败: {str(e)[:200]}"
                db.commit()
        return {"job_id": job_id, "status": "failed"}

    # 4) 回填并导出
    try:
        out_path = prepared.apply(translations)
    except Exception as e:  # noqa: BLE001
        with SessionLocal() as db:
            job = db.get(TranslationJob, job_id)
            if job:
                job.status = "failed"
                job.error_message = f"导出失败: {str(e)[:200]}"
                db.commit()
        return {"job_id": job_id, "status": "failed"}

    # 5) 写回任务完成状态
    with SessionLocal() as db:
        job = db.get(TranslationJob, job_id)
        if job:
            job.status = "succeeded"
            p = Path(out_path)
            try:
                p = p.relative_to(BACKEND_ROOT)
            except Exception:  # noqa: BLE001
                pass
            job.result_path = p.as_posix()
            db.commit()

    return {"job_id": job_id, "status": "succeeded", "mode": mode, "target_lang": target_lang}

