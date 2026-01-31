"""路径工具（统一处理相对路径的基准）。

背景：
- 本项目大量使用“相对路径”来存储上传文件/导出文件（便于迁移运行）。
- 但如果运行命令时的工作目录（cwd）变化，直接用相对路径做文件 IO 会踩坑。

原则：
- 配置与 DB 中保存“相对 backend/ 的路径”；
- 实际读写文件时，统一解析为基于 backend 根目录的绝对路径；
- 下载等入口再做一次目录约束校验，避免路径穿越风险。
"""

from __future__ import annotations

from pathlib import Path


# backend/ 目录（即包含 venv、app、storage 的目录）
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def resolve_backend_path(p: str | Path) -> Path:
    """把配置/DB 中的路径解析为绝对路径。

    - 绝对路径：原样返回
    - 相对路径：以 backend 根目录为基准拼接
    """

    pp = Path(p)
    if pp.is_absolute():
        return pp
    # strict=False：即便路径尚不存在（例如即将创建的 uploads 文件），也可以解析
    return (BACKEND_ROOT / pp).resolve(strict=False)


def is_within_dir(path: Path, base_dir: Path) -> bool:
    """判断 path 是否位于 base_dir 下（用于下载/读取等安全约束）。"""

    rp = resolve_backend_path(path)
    rb = resolve_backend_path(base_dir)
    try:
        rp.relative_to(rb)
        return True
    except ValueError:
        return False

