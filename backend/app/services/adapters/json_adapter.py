"""JSON 适配器。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.adapters.base import PreparedTranslation
from app.services.adapters.json_path import JsonLeafRef, find_leaf_refs
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
    parent: Any  # dict 或 list
    key: Any  # str 或 int


class JsonAdapter:
    format_name = "json"

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
        data = json.loads(file_path.read_text(encoding="utf-8"))

        # 统一按“记录列表”处理：root 为 list -> 多条；root 为 dict -> 单条
        if isinstance(data, list):
            records = data
            record_indices = list(range(min(max(0, int(row_limit or 0)), len(records))))
        else:
            records = [data]
            record_indices = [0]

        items: list[TranslateItem] = []
        ops: list[_SetOp] = []
        counter = 0

        for ridx in record_indices:
            record = records[ridx]
            for path in selected_fields:
                for ref in find_leaf_refs(record, path):
                    # 仅翻译字符串
                    if _is_blank_text(ref.value):
                        continue

                    op_key: Any
                    if mode == "add_columns":
                        # dict 叶子：新增 sibling key；list 叶子：无法新增字段，只能跳过
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
                    items.append(TranslateItem(id=item_id, text=str(ref.value), hint=f"path={path}"))
                    ops.append(_SetOp(item_id=item_id, parent=ref.parent, key=op_key))

        def apply(translations: dict[str, str]) -> Path:
            # 回填
            for op in ops:
                op.parent[op.key] = translations.get(op.item_id, "")

            export_dir.mkdir(parents=True, exist_ok=True)
            out_path = export_dir / f"{file_path.stem}_translated_{job_id}.json"
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return out_path

        return PreparedTranslation(items=items, apply=apply)

