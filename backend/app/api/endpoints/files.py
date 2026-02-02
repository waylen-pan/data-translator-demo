"""文件相关接口。"""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.paths import resolve_backend_path
from app.db.session import get_db
from app.models.uploaded_file import UploadedFile
from app.schemas.files import UploadFileResponse
from app.services.adapters.detect import detect_format
from app.services.adapters.preview import preview_and_candidates

router = APIRouter()


@router.post("/upload", response_model=UploadFileResponse)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadFileResponse:
    """上传文件并返回格式检测结果、预览与字段/列候选。"""

    # 由中间件注入（Cookie dt_client_id）
    client_id = getattr(request.state, "client_id", "") or ""
    if not client_id:
        raise HTTPException(status_code=500, detail="匿名会话未初始化，请刷新后重试")

    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    file_id = str(uuid4())
    fmt = detect_format(filename=file.filename, content_type=file.content_type or "").name

    suffix = Path(file.filename).suffix
    save_name = f"{file_id}{suffix}"
    # DB 中只存相对路径（相对 backend/），文件 IO 使用绝对路径
    relative_save_path = Path(settings.UPLOADS_DIR) / save_name
    abs_save_path = resolve_backend_path(relative_save_path)

    try:
        # 保存到本地
        abs_save_path.parent.mkdir(parents=True, exist_ok=True)
        with abs_save_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)[:200]}")
    finally:
        try:
            file.file.close()
        except Exception:  # noqa: BLE001
            pass

    size_bytes = 0
    try:
        size_bytes = abs_save_path.stat().st_size
    except Exception:  # noqa: BLE001
        size_bytes = 0

    # 预览与字段候选（先解析成功再落库，避免“脏记录”）
    try:
        preview, candidates = preview_and_candidates(file_path=abs_save_path, detected_format=fmt, limit=20)
    except Exception as e:  # noqa: BLE001
        try:
            abs_save_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass
        raise HTTPException(status_code=400, detail=f"解析文件失败: {str(e)[:200]}")

    # 落库：保存“相对路径”，方便迁移运行
    record = UploadedFile(
        id=file_id,
        client_id=client_id,
        filename=file.filename,
        content_type=file.content_type or "",
        size_bytes=size_bytes,
        detected_format=fmt,
        storage_path=str(relative_save_path.as_posix()),
    )
    db.add(record)
    db.commit()

    return UploadFileResponse(
        file_id=file_id,
        detected_format=fmt,
        field_candidates=candidates,
        preview=preview,
    )

