"""时间工具。

说明：
- 统一使用 UTC 且 timezone-aware 的 datetime；
- 避免使用 `datetime.utcnow()`（返回 naive datetime，且在部分依赖链中会触发弃用警告）。
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """返回当前 UTC 时间（timezone-aware）。"""

    return datetime.now(UTC)

