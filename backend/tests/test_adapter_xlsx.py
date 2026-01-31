from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.services.adapters.xlsx_adapter import XlsxAdapter


def test_xlsx_adapter_add_columns(tmp_path: Path) -> None:
    """XLSX：add_columns 模式应新增 *_zh 列并写出 xlsx。"""

    df = pd.DataFrame(
        [
            {"col1": "Hello", "col2": 1},
            {"col1": "World", "col2": 2},
        ]
    )
    in_path = tmp_path / "input.xlsx"
    df.to_excel(in_path, index=False, engine="openpyxl")

    adapter = XlsxAdapter()
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
    assert item.text == "Hello"

    out_path = prepared.apply({item.id: "你好"})
    out_df = pd.read_excel(out_path, engine="openpyxl")

    assert "col1_zh" in out_df.columns
    assert out_df.at[0, "col1_zh"] == "你好"
    # 第二行未翻译：一般会是 NaN（Excel 空单元格）
    assert pd.isna(out_df.at[1, "col1_zh"])

