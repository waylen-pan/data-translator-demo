from __future__ import annotations

import json
from pathlib import Path

from app.services.adapters.jsonl_adapter import JsonlAdapter


def test_jsonl_adapter_add_columns_preserve_blank_lines(tmp_path: Path) -> None:
    """JSONL：应保留空行；row_limit 以“对象行数”计数，而不是物理行数。"""

    in_path = tmp_path / "input.jsonl"
    lines = [
        json.dumps({"text": "Hello"}, ensure_ascii=False),
        "",  # 空行
        json.dumps({"text": "World"}, ensure_ascii=False),
    ]
    in_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    adapter = JsonlAdapter()
    prepared = adapter.prepare(
        file_path=in_path,
        selected_fields=["text"],
        row_limit=1,  # 只翻译第一个对象
        mode="add_columns",
        target_lang="zh-CN",
        export_dir=tmp_path,
        job_id="job1",
    )

    assert len(prepared.items) == 1
    translations = {prepared.items[0].id: "你好"}
    out_path = prepared.apply(translations)

    out_lines = out_path.read_text(encoding="utf-8").splitlines()
    assert len(out_lines) == 3

    obj1 = json.loads(out_lines[0])
    assert obj1["text"] == "Hello"
    assert obj1["text_zh"] == "你好"

    assert out_lines[1] == ""  # 空行保留

    obj2 = json.loads(out_lines[2])
    assert obj2["text"] == "World"
    assert "text_zh" not in obj2  # row_limit=1，不应翻译第二个对象

