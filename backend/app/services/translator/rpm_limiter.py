"""RPM（每分钟请求数）限流器（同步版）。

设计目标：
- 只表达“每分钟最多 N 次请求”的语义。
- 采用“平滑放行”（固定间隔放行 1 次），避免短时间 burst 触发 429。

说明：
- 该实现为“进程内限流”。Celery 多进程/多机器部署时，整体 RPM 可能仍会叠加。
  Demo 阶段先保持简单；如需全局限流，可升级为 Redis 分布式令牌桶。
"""

from __future__ import annotations

import threading
import time


class SmoothRpmLimiter:
    """平滑 RPM 限流器（leaky bucket 的最小实现）。"""

    def __init__(self, rpm: int) -> None:
        safe_rpm = int(rpm) if rpm is not None else 0
        self._rpm = max(1, safe_rpm)
        self._interval_seconds = 60.0 / float(self._rpm)
        self._lock = threading.Lock()
        self._next_ts = 0.0

    @property
    def rpm(self) -> int:
        return self._rpm

    def acquire(self) -> None:
        """阻塞等待直到当前请求被放行。"""

        with self._lock:
            now = time.monotonic()
            wait_seconds = max(0.0, self._next_ts - now)
            base = max(self._next_ts, now)
            self._next_ts = base + self._interval_seconds

        if wait_seconds > 0:
            time.sleep(wait_seconds)

