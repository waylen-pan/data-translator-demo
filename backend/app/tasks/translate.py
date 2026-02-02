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

        # 防御式检查：上传记录存在，但文件可能已被清理/移动
        if not file_path.exists():
            job.status = "failed"
            job.error_message = "找不到上传文件（文件可能已被清理或路径无效）"
            db.commit()
            return {"job_id": job_id, "status": "failed"}

        selected_fields_obj: Any = job.selected_fields
        selected_fields: list[str] = selected_fields_obj if isinstance(selected_fields_obj, list) else []
        selected_fields = [str(x) for x in selected_fields if str(x).strip()]

        # 2) 准备翻译单元（并初始化进度）
        try:
            prepared = adapter.prepare(
                file_path=file_path,
                selected_fields=selected_fields,
                row_limit=int(job.row_limit or 0),
                mode=job.mode,
                target_lang=job.target_lang,
                export_dir=export_dir,
                job_id=job.id,
            )
        except Exception as e:  # noqa: BLE001
            job.status = "failed"
            job.error_message = f"准备翻译单元失败: {str(e)[:200]}"
            db.commit()
            return {"job_id": job_id, "status": "failed"}

        items: list[TranslateItem] = prepared.items

        # 边界情况：所选字段没有可翻译的文本内容
        # - 可能原因：字段下全是数字/时间戳/null，或字段路径不匹配
        # - 处理方式：明确告知用户，让其调整字段选择后重试
        if not items:
            job.status = "failed"
            job.error_message = (
                "所选字段没有可翻译的文本内容。"
                "可能原因：字段值为空/数字/时间戳，或字段路径不存在。"
                "请检查字段选择后重新创建任务。"
            )
            db.commit()
            return {"job_id": job_id, "status": "failed"}

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
            def translate_items_stream(self, xs: list[TranslateItem], *, target_lang: str):  # noqa: ANN001,ARG002
                for it in xs:
                    yield (it.id, f"【mock】{it.text}")

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
        # 说明：
        # - 翻译器内部会尽量并发地跑满 RPM；这里不要再用 batch 切片去“限制翻译提交”；
        # - `cell_batch_size` 只用于控制“写 DB 更新进度”的频率。
        done = 0
        last_flushed_done = 0
        for item_id, translated_text in translator.translate_items_stream(items, target_lang=target_lang):
            translations[str(item_id)] = str(translated_text or "")
            done += 1

            if done - last_flushed_done >= cell_batch_size:
                with SessionLocal() as db:
                    job = db.get(TranslationJob, job_id)
                    if job:
                        job.progress_done = min(int(job.progress_total or 0), done)
                        db.commit()
                last_flushed_done = done

        # 收尾：把最后不足一个 batch 的进度写回
        if done != last_flushed_done:
            with SessionLocal() as db:
                job = db.get(TranslationJob, job_id)
                if job:
                    job.progress_done = min(int(job.progress_total or 0), done)
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

