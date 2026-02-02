from __future__ import annotations

from app.services.translator.ark_translator import ArkBatchTranslator, TranslateItem


def test_translate_items_stream_merges_parts_in_order(monkeypatch):
    """验证：长文本切分后，按 part 顺序合并并按 parent 产出。"""

    translator = ArkBatchTranslator(
        api_key="dummy",
        base_url="https://example.com",
        model="dummy",
        rpm=10_000,  # 测试不希望被 limiter 影响
        disable_thinking=True,
        max_cell_chars=3,  # 强制切分
        request_timeout_seconds=1.0,
        enable_redis_cache=False,
    )

    # 让翻译逻辑可预测：直接把输入包一层，避免真实网络调用
    def _fake_translate_single_text(text: str, *, target_lang: str) -> str:  # noqa: ARG001
        return f"<{text}>"

    monkeypatch.setattr(translator, "_translate_single_text", _fake_translate_single_text)

    # "abcdef" 在 max_cell_chars=3 下会切成 ["abc", "def"]
    items = [TranslateItem(id="x", text="abcdef")]
    out = dict(translator.translate_items_stream(items, target_lang="zh"))

    assert out == {"x": "<abc><def>"}


def test_translate_items_stream_handles_empty_text():
    """验证：空白文本不会走模型调用，直接产出空字符串。"""

    translator = ArkBatchTranslator(
        api_key="dummy",
        base_url="https://example.com",
        model="dummy",
        rpm=10_000,
        disable_thinking=True,
        max_cell_chars=3,
        request_timeout_seconds=1.0,
        enable_redis_cache=False,
    )

    items = [TranslateItem(id="x", text="   \n\t")]
    out = dict(translator.translate_items_stream(items, target_lang="zh"))

    assert out == {"x": ""}

