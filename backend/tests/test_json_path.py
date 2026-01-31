from __future__ import annotations

from app.services.adapters.json_path import find_leaf_refs


def test_find_leaf_refs_simple_path() -> None:
    """基础点号路径：a.b.c"""

    obj = {"a": {"b": {"c": "hello"}}}
    refs = find_leaf_refs(obj, "a.b.c")
    assert len(refs) == 1
    assert refs[0].key == "c"
    assert refs[0].value == "hello"


def test_find_leaf_refs_list_wildcard_in_middle() -> None:
    """列表通配：items[].text"""

    obj = {"items": [{"text": "hi"}, {"text": "bye"}]}
    refs = find_leaf_refs(obj, "items[].text")
    assert [r.value for r in refs] == ["hi", "bye"]
    assert all(r.key == "text" for r in refs)


def test_find_leaf_refs_list_wildcard_as_leaf() -> None:
    """叶子为列表元素：tags[]"""

    obj = {"tags": ["a", "b", "c"]}
    refs = find_leaf_refs(obj, "tags[]")
    assert [r.value for r in refs] == ["a", "b", "c"]
    assert [r.key for r in refs] == [0, 1, 2]

