"""预览与字段候选提取（MVP）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas.files import Preview, PreviewJson, PreviewTable


def _df_to_preview_table(df: pd.DataFrame) -> PreviewTable:
    # pandas 的 NaN/NaT 不适合直接序列化，统一转为 None
    df2 = df.where(pd.notnull(df), None)
    columns = [str(c) for c in df2.columns.tolist()]
    rows = df2.to_dict(orient="records")
    return PreviewTable(columns=columns, rows=rows)


def preview_and_candidates(*, file_path: Path, detected_format: str, limit: int = 20) -> tuple[Preview, list[str]]:
    """读取文件的前 N 行/条，用于前端预览与字段/列候选。"""

    fmt = (detected_format or "").strip().lower()
    limit = max(1, int(limit or 20))

    if fmt == "csv":
        try:
            df = pd.read_csv(file_path, nrows=limit)
        except UnicodeDecodeError:
            # 常见 BOM 情况
            df = pd.read_csv(file_path, nrows=limit, encoding="utf-8-sig")
        preview = _df_to_preview_table(df)
        return preview, preview.columns

    if fmt == "xlsx":
        df = pd.read_excel(file_path, nrows=limit, engine="openpyxl")
        preview = _df_to_preview_table(df)
        return preview, preview.columns

    if fmt == "json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        preview_value: Any = data
        candidates: list[str] = []

        if isinstance(data, dict):
            candidates = [str(k) for k in data.keys()]
            # 预览只展示前 N 个 key，避免超大对象撑爆页面
            preview_value = {k: data[k] for k in list(data.keys())[:limit]}
        elif isinstance(data, list):
            # 预览只取前 N 个元素
            preview_value = data[:limit]
            # 如果元素是 dict，则汇总 key
            keys: set[str] = set()
            for item in preview_value:
                if isinstance(item, dict):
                    keys.update([str(k) for k in item.keys()])
            candidates = sorted(keys)

        return PreviewJson(value=preview_value), candidates

    if fmt == "jsonl":
        items: list[Any] = []
        keys: set[str] = set()
        with file_path.open("r", encoding="utf-8") as f:
            for _ in range(limit):
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                items.append(obj)
                if isinstance(obj, dict):
                    keys.update([str(k) for k in obj.keys()])
        return PreviewJson(value=items), sorted(keys)

    return PreviewJson(value={"warning": "暂不支持预览该格式"}), []

