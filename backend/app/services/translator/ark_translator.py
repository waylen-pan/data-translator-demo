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

import concurrent.futures
import hashlib
import random
import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

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
        # 说明：
        # - 为避免多线程并发时共享 client 的潜在问题，这里使用“线程本地 client”。
        # - 这能让我们在提升吞吐（并发请求）时更稳健。
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = float(request_timeout_seconds)
        self._client_local = threading.local()
        self._cache = RedisTranslationCache(settings.REDIS_URL) if enable_redis_cache else None

    def translate_items(self, items: list[TranslateItem], *, target_lang: str) -> dict[str, str]:
        """翻译一组单元并返回映射：item_id -> translated_text。"""
        return dict(self.translate_items_stream(items, target_lang=target_lang))

    def translate_items_stream(self, items: list[TranslateItem], *, target_lang: str) -> Iterator[tuple[str, str]]:
        """流式翻译：尽可能早地产出结果（按“原始 item”维度产出）。

        背景：
        - 之前 `TRANSLATION_BATCH_SIZE` 在任务层被用于“分块翻译 + 更新进度”，
          会让人误以为“系统只有 20 并发/20 rpm”。实际上它只是进度写库批次。
        - 真正限制吞吐的是：翻译器内部对 expanded items 的模型调用是串行的。

        这里的策略：
        - 一次性把所有 item（含长文本切分后的 part）提交到线程池并发执行；
        - 仍通过 `SmoothRpmLimiter` 做进程内 RPM 平滑限流；
        - 对外只在同一 parent 的所有 part 完成后，才 yield 合并后的结果。
        """

        # 并发度：用于提升吞吐，尽量打满 RPM
        max_workers = int(getattr(settings, "TRANSLATION_MAX_CONCURRENCY", 50) or 50)
        max_workers = max(1, max_workers)

        # parent -> 预期 part 数量 / 已完成数量 / part 结果缓冲
        parent_expected: dict[str, int] = {}
        parent_done: dict[str, int] = {}
        parent_buf: dict[str, list[Optional[str]]] = {}

        # future -> (parent_id, part_idx)
        future_meta: dict[concurrent.futures.Future[str], tuple[str, int]] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 1) 提交任务（part 级别）
            for it in items:
                parent_id = it.id
                text = str(it.text or "")
                if not text.strip():
                    yield (parent_id, "")
                    continue

                parts = split_text_by_max_chars(text, max_chars=self._max_cell_chars)
                parent_expected[parent_id] = len(parts)
                parent_done[parent_id] = 0
                parent_buf[parent_id] = [None] * len(parts)

                for idx, part in enumerate(parts):
                    fut = executor.submit(self._translate_single_text, part, target_lang=target_lang)
                    future_meta[fut] = (parent_id, idx)

            # 2) 消费完成的 part；当 parent 所有 part 就绪后合并产出
            for fut in concurrent.futures.as_completed(future_meta):
                parent_id, idx = future_meta[fut]
                out = fut.result()

                buf = parent_buf.get(parent_id)
                if buf is None:
                    # 防御性兜底：理论上不应发生
                    continue

                buf[idx] = out
                parent_done[parent_id] = int(parent_done.get(parent_id, 0)) + 1

                if parent_done[parent_id] >= int(parent_expected.get(parent_id, 0)):
                    merged = "".join([(x or "") for x in buf])
                    yield (parent_id, merged)
                    # 释放内存，避免大批量时持续增长
                    parent_buf.pop(parent_id, None)
                    parent_expected.pop(parent_id, None)
                    parent_done.pop(parent_id, None)

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
                resp = self._get_client().chat.completions.create(**kwargs)
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

    def _get_client(self) -> OpenAI:
        """获取线程本地 OpenAI client。"""

        client = getattr(self._client_local, "client", None)
        if client is None:
            client = OpenAI(api_key=self._api_key, base_url=self._base_url, timeout=self._timeout_seconds)
            self._client_local.client = client
        return client


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

