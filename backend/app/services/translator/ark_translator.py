"""火山方舟（OpenAI SDK 兼容）翻译器。

本版本的核心约束（按你最新要求）：
- 使用 `doubao-seed-1-6-lite-251015`（由 `.env` / Settings 控制）
- **不使用模型侧的 JSON 输出模式**（不传 response_format、不依赖 parse）
- 仅通过 Prompt 约束“输入是什么格式，输出就保持什么格式”

工程要点：
- RPM=1000：进程内平滑限流（若未来要多进程全局限流，可升级为 Redis 分布式 limiter）
- 长文本切分：单元 > max_chars 时分片翻译后拼回
- Redis 缓存：减少重复翻译与成本（连接失败会自动降级为不缓存）
"""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass
from typing import Optional

import redis
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from app.core.config import settings
from app.prompts import DATA_TRANSLATOR_SYSTEM_PROMPT
from app.services.translator.rpm_limiter import SmoothRpmLimiter
from app.services.translator.splitter import split_text_by_max_chars


@dataclass(frozen=True)
class TranslateItem:
    """一个最小翻译单元（字段值/单元格）。"""

    id: str
    text: str
    hint: str = ""


class RedisTranslationCache:
    """Redis 缓存（可选，失败自动降级）。"""

    # 重要：缓存版本号。
    # 说明：我们曾经从 `json_schema(parse)` 路径缓存过“未翻译直接回传原文”的结果。
    # 为避免旧缓存污染新的翻译策略，这里显式加版本号做一次“软清库”。
    # 说明：prompt/输出协议变更时，务必 bump 版本号，避免旧缓存污染新策略。
    _CACHE_VERSION = "v3"

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Optional[redis.Redis] = None

    def _get_client(self) -> Optional[redis.Redis]:
        if self._client is not None:
            return self._client
        try:
            self._client = redis.Redis.from_url(self._redis_url, decode_responses=True)
            self._client.ping()
            return self._client
        except Exception:  # noqa: BLE001
            self._client = None
            return None

    @staticmethod
    def _key(model: str, target_lang: str, text: str) -> str:
        raw = f"{model}|{target_lang}|{text}".encode("utf-8")
        h = hashlib.sha256(raw).hexdigest()
        return f"translation:{RedisTranslationCache._CACHE_VERSION}:{h}"

    def get(self, *, model: str, target_lang: str, text: str) -> Optional[str]:
        client = self._get_client()
        if client is None:
            return None
        try:
            return client.get(self._key(model, target_lang, text))
        except Exception:  # noqa: BLE001
            return None

    def set(
        self,
        *,
        model: str,
        target_lang: str,
        text: str,
        translated_text: str,
        ttl_seconds: int = 86400 * 30,
    ) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            client.set(self._key(model, target_lang, text), translated_text, ex=int(ttl_seconds))
        except Exception:  # noqa: BLE001
            return


class ArkBatchTranslator:
    """翻译器（保持对外接口：translate_items(items)->mapping）。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        rpm: int,
        disable_thinking: bool,
        max_cell_chars: int,
        request_timeout_seconds: float = 120.0,
        enable_redis_cache: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("缺少 ARK_API_KEY")

        self.model = model
        self._disable_thinking = bool(disable_thinking)
        self._max_cell_chars = int(max_cell_chars or 10000)
        self._limiter = SmoothRpmLimiter(int(rpm or 1))
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=request_timeout_seconds)
        self._cache = RedisTranslationCache(settings.REDIS_URL) if enable_redis_cache else None

    def translate_items(self, items: list[TranslateItem], *, target_lang: str) -> dict[str, str]:
        """翻译一组单元并返回映射：item_id -> translated_text。"""

        # 1) 拆分长文本
        expanded: list[TranslateItem] = []
        parent_to_part_ids: dict[str, list[str]] = {}
        for it in items:
            text = str(it.text or "")
            if not text.strip():
                parent_to_part_ids[it.id] = []
                continue
            parts = split_text_by_max_chars(text, max_chars=self._max_cell_chars)
            if len(parts) == 1:
                expanded.append(it)
                parent_to_part_ids[it.id] = [it.id]
                continue
            part_ids: list[str] = []
            for idx, part in enumerate(parts):
                pid = f"{it.id}__part_{idx}"
                part_ids.append(pid)
                expanded.append(TranslateItem(id=pid, text=part, hint=it.hint))
            parent_to_part_ids[it.id] = part_ids

        translated_parts: dict[str, str] = {}
        for it in expanded:
            translated_parts[it.id] = self._translate_single_text(it.text, target_lang=target_lang)

        # 4) 合并分片
        merged: dict[str, str] = {}
        for parent_id, part_ids in parent_to_part_ids.items():
            if not part_ids:
                merged[parent_id] = ""
                continue
            merged[parent_id] = "".join([translated_parts.get(pid, "") for pid in part_ids])
        return merged

    def _translate_single_text(self, text: str, *, target_lang: str) -> str:
        """翻译单段文本（带缓存、限流、重试）。

        注意：该函数不会对输出做 strip()，避免破坏“格式保真”要求。
        """

        s = str(text or "")
        if not s.strip():
            return ""

        if self._cache:
            hit = self._cache.get(model=self.model, target_lang=target_lang, text=s)
            if hit is not None:
                return hit

        system_prompt = DATA_TRANSLATOR_SYSTEM_PROMPT
        # 当前产品目标固定为中文 PM 场景，因此系统 prompt 直接写死为简体中文；
        # 如果未来需要支持其它目标语言，可在此处做 prompt 版本化/按语言切换。

        last_exc: Optional[Exception] = None
        for attempt in range(5):
            self._limiter.acquire()
            try:
                kwargs = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": s},
                    ],
                    "temperature": 0.0,
                }
                if self._disable_thinking:
                    kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
                resp = self._client.chat.completions.create(**kwargs)
                out = resp.choices[0].message.content or ""
                if self._cache:
                    self._cache.set(model=self.model, target_lang=target_lang, text=s, translated_text=out)
                return out
            except APIStatusError as e:
                last_exc = e
                status = int(getattr(e, "status_code", 0) or 0)
                if status < 500:
                    # 4xx 更可能是参数/请求体问题，直接抛出便于定位
                    raise
            except (RateLimitError, APIConnectionError, APITimeoutError) as e:
                last_exc = e

            wait = min(20.0, (0.6 * (2**attempt)) + random.random())
            time.sleep(wait)

        raise RuntimeError(f"模型调用失败（多次重试仍失败）: {last_exc}")


def build_default_translator() -> ArkBatchTranslator:
    """从 settings 构建默认翻译器。"""

    return ArkBatchTranslator(
        api_key=settings.ARK_API_KEY,
        base_url=settings.ARK_BASE_URL,
        model=settings.ARK_MODEL,
        rpm=settings.ARK_RPM,
        disable_thinking=settings.ARK_DISABLE_THINKING,
        max_cell_chars=settings.TRANSLATION_MAX_CELL_CHARS,
        request_timeout_seconds=120.0,
        enable_redis_cache=True,
    )

