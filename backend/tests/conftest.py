from __future__ import annotations

"""
pytest 基础配置。

说明：
- 本项目后端代码位于 backend/app/，导入根包为 `app`。
- 某些 pytest/导入模式下，项目根目录可能不会自动加入 sys.path，导致 `import app` 失败。
- 这里显式把 backend/ 目录加入 sys.path，确保单测稳定可运行。
"""

import sys
from pathlib import Path


def _ensure_backend_on_syspath() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    p = str(backend_dir)
    if p not in sys.path:
        sys.path.insert(0, p)


_ensure_backend_on_syspath()

