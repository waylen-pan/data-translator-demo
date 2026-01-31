"""长文本切分工具。"""

from __future__ import annotations


def split_text_by_max_chars(text: str, *, max_chars: int) -> list[str]:
    """将长文本切成若干段，每段长度 <= max_chars。

    切分策略（从易到难）：
    - 尽量按换行切分（更符合表格/日志/JSON 字符串场景）
    - 兜底按固定长度切分
    """

    s = str(text or "")
    max_chars = max(1, int(max_chars or 1))
    if len(s) <= max_chars:
        return [s]

    parts: list[str] = []
    start = 0
    n = len(s)

    while start < n:
        end = min(start + max_chars, n)

        # 尽量在窗口内找最后一个换行作为断点
        cut = s.rfind("\n", start, end)
        # 如果换行太靠前（会导致过度碎片化），则不用换行切
        if cut <= start + max_chars * 0.5:
            cut = end

        # 安全兜底：避免死循环
        if cut <= start:
            cut = end

        parts.append(s[start:cut])
        start = cut

    return parts

