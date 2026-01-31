from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.services.adapters.csv_adapter import CsvAdapter


def _read_csv_keep_empty(path: Path) -> pd.DataFrame:
    """读取 CSV，并把空单元格保留为空字符串（避免被 pandas 默认转成 NaN 影响断言）。"""

    return pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)


def test_csv_adapter_add_columns(tmp_path: Path) -> None:
    """CSV：add_columns 模式应新增 *_zh 列，并仅翻译前 N 行。"""

    in_path = tmp_path / "input.csv"
    in_path.write_text("col1,col2\nhello,1\nworld,2\n", encoding="utf-8")

    adapter = CsvAdapter()
    prepared = adapter.prepare(
        file_path=in_path,
        selected_fields=["col1"],
        row_limit=1,
        mode="add_columns",
        target_lang="zh-CN",
        export_dir=tmp_path,
        job_id="job1",
    )

    assert len(prepared.items) == 1
    item = prepared.items[0]
    assert item.text == "hello"

    out_path = prepared.apply({item.id: "你好"})
    out_df = _read_csv_keep_empty(out_path)

    assert "col1_zh" in out_df.columns
    assert out_df.at[0, "col1_zh"] == "你好"
    # 第二行未在 row_limit 内，不应被翻译
    assert out_df.at[1, "col1_zh"] == ""


def test_csv_adapter_overwrite(tmp_path: Path) -> None:
    """CSV：overwrite 模式应覆盖原值。"""

    in_path = tmp_path / "input.csv"
    in_path.write_text("col1,col2\nhello,1\nworld,2\n", encoding="utf-8")

    adapter = CsvAdapter()
    prepared = adapter.prepare(
        file_path=in_path,
        selected_fields=["col1"],
        row_limit=2,
        mode="overwrite",
        target_lang="zh-CN",
        export_dir=tmp_path,
        job_id="job2",
    )

    translations = {it.id: f"ZH_{it.text}" for it in prepared.items}
    out_path = prepared.apply(translations)
    out_df = _read_csv_keep_empty(out_path)

    assert out_df.at[0, "col1"] == "ZH_hello"
    assert out_df.at[1, "col1"] == "ZH_world"

