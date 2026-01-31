"""JSONL 适配器（每行一个 JSON）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from app.services.adapters.base import PreparedTranslation
from app.services.adapters.json_path import find_leaf_refs
from app.services.translator.ark_translator import TranslateItem


def _is_blank_text(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return True
    return not value.strip()


@dataclass(frozen=True)
class _SetOp:
    item_id: str
    parent: Any
    key: Any


class JsonlAdapter:
    format_name = "jsonl"

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
        # 读取：保留空行（None）以便原样输出
        rows: list[Optional[Any]] = []
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                s = line.rstrip("\n")
                if not s.strip():
                    rows.append(None)
                    continue
                rows.append(json.loads(s))

        obj_indices = [i for i, obj in enumerate(rows) if obj is not None]
        translate_indices = obj_indices[: max(0, int(row_limit or 0))]

        items: list[TranslateItem] = []
        ops: list[_SetOp] = []
        counter = 0

        for idx in translate_indices:
            obj = rows[idx]
            if obj is None:
                continue
            for path in selected_fields:
                for ref in find_leaf_refs(obj, path):
                    if _is_blank_text(ref.value):
                        continue
                    op_key: Any
                    if mode == "add_columns":
                        if isinstance(ref.parent, dict) and isinstance(ref.key, str):
                            op_key = f"{ref.key}_zh"
                        else:
                            continue
                    elif mode == "overwrite":
                        op_key = ref.key
                    else:
                        raise ValueError(f"未知 mode: {mode}")

                    item_id = f"t{counter}"
                    counter += 1
                    items.append(TranslateItem(id=item_id, text=str(ref.value), hint=f"line={idx} path={path}"))
                    ops.append(_SetOp(item_id=item_id, parent=ref.parent, key=op_key))

        def apply(translations: dict[str, str]) -> Path:
            for op in ops:
                op.parent[op.key] = translations.get(op.item_id, "")

            export_dir.mkdir(parents=True, exist_ok=True)
            out_path = export_dir / f"{file_path.stem}_translated_{job_id}.jsonl"
            with out_path.open("w", encoding="utf-8") as out:
                for obj in rows:
                    if obj is None:
                        out.write("\n")
                    else:
                        out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            return out_path

        return PreparedTranslation(items=items, apply=apply)

