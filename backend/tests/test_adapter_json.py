from __future__ import annotations

import json
from pathlib import Path

from app.services.adapters.json_adapter import JsonAdapter


def test_json_adapter_add_columns(tmp_path: Path) -> None:
    """JSON：add_columns 模式应新增 *_zh 字段，并尽量保持原结构不变。"""

    data = [
        {
            "id": 1,
            "text": "Hello",
            "nested": {"desc": "Bye"},
            "items": [{"text": "Hi"}, {"text": "Ok"}],
            "tags": ["a", "b"],
        }
    ]
    in_path = tmp_path / "input.json"
    in_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    adapter = JsonAdapter()
    prepared = adapter.prepare(
        file_path=in_path,
        selected_fields=["text", "nested.desc", "items[].text", "tags[]"],
        row_limit=50,
        mode="add_columns",
        target_lang="zh-CN",
        export_dir=tmp_path,
        job_id="job1",
    )

    # tags[] 在 add_columns 下无法新增 sibling 字段（list 元素），应被跳过
    assert len(prepared.items) == 4

    translations = {it.id: f"ZH_{it.text}" for it in prepared.items}
    out_path = prepared.apply(translations)
    out = json.loads(out_path.read_text(encoding="utf-8"))

    assert out[0]["text"] == "Hello"
    assert out[0]["text_zh"] == "ZH_Hello"
    assert out[0]["nested"]["desc"] == "Bye"
    assert out[0]["nested"]["desc_zh"] == "ZH_Bye"
    assert out[0]["items"][0]["text"] == "Hi"
    assert out[0]["items"][0]["text_zh"] == "ZH_Hi"
    assert out[0]["items"][1]["text_zh"] == "ZH_Ok"
    # tags 不应被新增 tags_zh（不支持）
    assert "tags_zh" not in out[0]


def test_json_adapter_overwrite_including_list_leaf(tmp_path: Path) -> None:
    """JSON：overwrite 模式应覆盖原值，并支持 tags[] 这种 list leaf。"""

    data = [
        {
            "id": 1,
            "text": "Hello",
            "nested": {"desc": "Bye"},
            "items": [{"text": "Hi"}, {"text": "Ok"}],
            "tags": ["a", "b"],
        }
    ]
    in_path = tmp_path / "input.json"
    in_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    adapter = JsonAdapter()
    prepared = adapter.prepare(
        file_path=in_path,
        selected_fields=["text", "nested.desc", "items[].text", "tags[]"],
        row_limit=50,
        mode="overwrite",
        target_lang="zh-CN",
        export_dir=tmp_path,
        job_id="job2",
    )

    # overwrite 会把 list leaf（tags[]）也作为可替换单元
    assert len(prepared.items) == 6

    translations = {it.id: f"ZH_{it.text}" for it in prepared.items}
    out_path = prepared.apply(translations)
    out = json.loads(out_path.read_text(encoding="utf-8"))

    assert out[0]["text"] == "ZH_Hello"
    assert out[0]["nested"]["desc"] == "ZH_Bye"
    assert out[0]["items"][0]["text"] == "ZH_Hi"
    assert out[0]["items"][1]["text"] == "ZH_Ok"
    assert out[0]["tags"] == ["ZH_a", "ZH_b"]

