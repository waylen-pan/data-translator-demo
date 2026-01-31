"""XLSX 适配器（pandas + openpyxl）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.services.adapters.base import PreparedTranslation
from app.services.translator.ark_translator import TranslateItem


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:  # noqa: BLE001
        pass
    return not str(value).strip()


def _parse_item_id(item_id: str) -> tuple[int, str]:
    left, right = item_id.split("::", 1)
    row_idx = int(left[1:])
    col = right[1:]
    return row_idx, col


class XlsxAdapter:
    format_name = "xlsx"

    def prepare(
        self,
        *,
        file_path: Path,
        selected_fields: list[str],
        row_limit: int,
        mode: str,
        target_lang: str,  # noqa: ARG002
        export_dir: Path,
        job_id: str,
    ) -> PreparedTranslation:
        # 读取全量（Demo 简化）
        df = pd.read_excel(file_path, engine="openpyxl")

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
                    out_df.at[r, f"{col}_zh"] = translations.get(it.id, "")
            elif mode == "overwrite":
                for it in items:
                    r, col = _parse_item_id(it.id)
                    out_df.at[r, col] = translations.get(it.id, out_df.at[r, col])
            else:
                raise ValueError(f"未知 mode: {mode}")

            export_dir.mkdir(parents=True, exist_ok=True)
            out_path = export_dir / f"{file_path.stem}_translated_{job_id}.xlsx"
            out_df.to_excel(out_path, index=False, engine="openpyxl")
            return out_path

        return PreparedTranslation(items=items, apply=apply)

