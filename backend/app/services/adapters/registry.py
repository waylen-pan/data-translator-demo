"""适配器注册表。"""

from __future__ import annotations

from app.services.adapters.csv_adapter import CsvAdapter
from app.services.adapters.json_adapter import JsonAdapter
from app.services.adapters.jsonl_adapter import JsonlAdapter
from app.services.adapters.xlsx_adapter import XlsxAdapter
from app.services.adapters.base import DataAdapter


_ADAPTERS: dict[str, DataAdapter] = {
    "csv": CsvAdapter(),
    "xlsx": XlsxAdapter(),
    "json": JsonAdapter(),
    "jsonl": JsonlAdapter(),
}


def get_adapter(fmt: str) -> DataAdapter | None:
    return _ADAPTERS.get((fmt or "").strip().lower())

