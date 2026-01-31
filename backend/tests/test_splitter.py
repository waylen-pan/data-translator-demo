from __future__ import annotations

from app.services.translator.splitter import split_text_by_max_chars


def test_split_text_no_split() -> None:
    """短文本不应被切分。"""

    text = "hello world"
    parts = split_text_by_max_chars(text, max_chars=10000)
    assert parts == [text]


def test_split_text_fallback_fixed_window() -> None:
    """没有换行符时，按固定窗口切分，且拼接后应完全一致。"""

    text = "a" * 25001
    max_chars = 10000
    parts = split_text_by_max_chars(text, max_chars=max_chars)

    assert "".join(parts) == text
    assert all(len(p) <= max_chars for p in parts)
    assert len(parts) == 3


def test_split_text_prefers_newline_when_reasonable() -> None:
    """有换行符时，优先在窗口内按换行切分（但不强制要求换行落在哪一段）。"""

    text = ("a" * 6000) + "\n" + ("b" * 6000)
    max_chars = 10000
    parts = split_text_by_max_chars(text, max_chars=max_chars)

    assert "".join(parts) == text
    assert all(len(p) <= max_chars for p in parts)
    assert len(parts) == 2

