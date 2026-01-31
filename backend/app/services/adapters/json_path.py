"""JSON 字段路径解析（轻量实现）。

支持语法：
- 点号路径：a.b.c
- 列表通配：items[].text  （表示 items 是列表，对列表中每个元素取 text）

不引入第三方 jsonpath 依赖，保持 Demo 简洁可维护。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class JsonLeafRef:
    """指向一个可被替换/新增的叶子值。"""

    parent: Any  # dict 或 list
    key: Any  # dict key(str) 或 list index(int)
    value: Any


def _parse_segments(path: str) -> list[tuple[str, bool]]:
    """把路径切成 (key, is_list_wildcard) 的序列。"""

    raw = (path or "").strip()
    if not raw:
        return []
    segs: list[tuple[str, bool]] = []
    for part in raw.split("."):
        p = part.strip()
        if not p:
            continue
        if p.endswith("[]") and len(p) > 2:
            segs.append((p[:-2], True))
        else:
            segs.append((p, False))
    return segs


def find_leaf_refs(obj: Any, path: str) -> list[JsonLeafRef]:
    """在 obj 中根据 path 找到所有叶子引用（支持 [] 通配）。"""

    segs = _parse_segments(path)
    if not segs:
        return []

    nodes: list[Any] = [obj]
    for i, (key, wildcard) in enumerate(segs):
        is_last = i == len(segs) - 1
        next_nodes: list[Any] = []
        refs: list[JsonLeafRef] = []

        for node in nodes:
            if not isinstance(node, dict):
                continue
            if key not in node:
                continue
            val = node.get(key)

            if is_last:
                if wildcard:
                    # 叶子是列表元素：可在 overwrite 模式下逐元素替换
                    if isinstance(val, list):
                        for idx, elem in enumerate(val):
                            refs.append(JsonLeafRef(parent=val, key=idx, value=elem))
                else:
                    refs.append(JsonLeafRef(parent=node, key=key, value=val))
            else:
                if wildcard:
                    if isinstance(val, list):
                        next_nodes.extend(val)
                else:
                    next_nodes.append(val)

        if is_last:
            return refs

        nodes = next_nodes

    return []

