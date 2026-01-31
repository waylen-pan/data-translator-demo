"""适配器抽象（用于不同数据格式）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.services.translator.ark_translator import TranslateItem


@dataclass(frozen=True)
class PreparedTranslation:
    """适配器准备好的“可翻译单元”与“回填导出方法”。"""

    items: list[TranslateItem]
    apply: Callable[[dict[str, str]], Path]


class DataAdapter(Protocol):
    """数据格式适配器协议。"""

    format_name: str

    def prepare(
        self,
        *,
        file_path: Path,
        selected_fields: list[str],
        row_limit: int,
        mode: str,
        target_lang: str,
        export_dir: Path,
        job_id: str,
    ) -> PreparedTranslation:
        """读取数据，生成翻译单元，并返回回填导出函数。"""

