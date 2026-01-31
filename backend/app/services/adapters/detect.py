"""文件格式检测（MVP）。

优先策略：
1) 文件扩展名（最稳定、最可解释）
2) content-type（作为兜底）
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectedFormat:
    """内部统一格式标识。"""

    name: str  # json/jsonl/csv/xlsx/unknown


def detect_format(*, filename: str, content_type: str) -> DetectedFormat:
    """检测上传文件的格式。"""

    fname = (filename or "").lower().strip()
    ctype = (content_type or "").lower().strip()

    if fname.endswith(".jsonl") or "jsonl" in ctype:
        return DetectedFormat("jsonl")
    if fname.endswith(".json") or ctype in {"application/json", "text/json"}:
        return DetectedFormat("json")
    if fname.endswith(".csv") or "csv" in ctype:
        return DetectedFormat("csv")
    if fname.endswith(".xlsx") or "spreadsheetml" in ctype or "excel" in ctype:
        return DetectedFormat("xlsx")

    return DetectedFormat("unknown")

