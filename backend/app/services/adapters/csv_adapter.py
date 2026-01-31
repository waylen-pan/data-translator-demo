"""CSV 适配器（pandas）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.services.adapters.base import PreparedTranslation
from app.services.translator.ark_translator import TranslateItem


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    # pandas NaN
    try:
        if pd.isna(value):
            return True
    except Exception:  # noqa: BLE001
        pass
    return not str(value).strip()


def _parse_item_id(item_id: str) -> tuple[int, str]:
    # item_id: r{row}::c{col}
    left, right = item_id.split("::", 1)
    row_idx = int(left[1:])
    col = right[1:]
    return row_idx, col


class CsvAdapter:
    format_name = "csv"

    def prepare(
        self,
        *,
        file_path: Path,
        selected_fields: list[str],
        row_limit: int,
        mode: str,
        target_lang: str,  # noqa: ARG002 - 适配器暂不依赖语言
        export_dir: Path,
        job_id: str,
    ) -> PreparedTranslation:
        # 读取全量（Demo 简化）：导出时需要保留未翻译的行
        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="utf-8-sig")

        selected = [c for c in selected_fields if c in df.columns]
        limit = min(max(0, int(row_limit or 0)), len(df))

        items: list[TranslateItem] = []
        for r in range(limit):
            for col in selected:
                val = df.at[r, col]
                if _is_blank(val):
                    continue
                items.append(
                    TranslateItem(
                        id=f"r{r}::c{col}",
                        text=str(val),
                        hint=f"列={col}",
                    )
                )

        def apply(translations: dict[str, str]) -> Path:
            out_df = df.copy()

            if mode == "add_columns":
                for col in selected:
                    zh_col = f"{col}_zh"
                    if zh_col not in out_df.columns:
                        out_df[zh_col] = ""
                for it in items:
                    r, col = _parse_item_id(it.id)
                    zh_col = f"{col}_zh"
                    out_df.at[r, zh_col] = translations.get(it.id, "")
            elif mode == "overwrite":
                for it in items:
                    r, col = _parse_item_id(it.id)
                    out_df.at[r, col] = translations.get(it.id, out_df.at[r, col])
            else:
                raise ValueError(f"未知 mode: {mode}")

            export_dir.mkdir(parents=True, exist_ok=True)
            out_path = export_dir / f"{file_path.stem}_translated_{job_id}.csv"
            out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
            return out_path

        return PreparedTranslation(items=items, apply=apply)

