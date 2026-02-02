"""匿名会话（同一浏览器）标识中间件。

目标：
- 本项目是内部工具，不做账号登录；
- 但需要支持：用户提交任务后关闭页面，再打开仍可找回任务列表与结果；
- 同时要求：任务只允许“同一浏览器”访问（job_id 不能当作访问钥匙）。

方案（最佳实践）：
- 使用 HttpOnly Cookie 存一个随机 UUID（dt_client_id）作为“匿名会话身份”；
- 每个请求把该值写入 `request.state.client_id`，供业务接口做归属写入与校验；
- 避免使用浏览器指纹/UA 等不稳定且有隐私风险的标识。
"""

from __future__ import annotations

import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


DEFAULT_COOKIE_NAME = "dt_client_id"
# 30 天：足够覆盖“用户过几天再回来查”的常见场景；也不会无限期堆积数据。
DEFAULT_MAX_AGE_SECONDS = 30 * 24 * 60 * 60


def _normalize_uuid(s: str) -> str | None:
    """把输入解析为 UUID；失败返回 None。

    注意：
    - 这里不做“宽松容错”来尝试修复异常值；直接换新值更安全、行为更可预期。
    """

    try:
        return str(uuid.UUID(str(s).strip()))
    except Exception:  # noqa: BLE001
        return None


def _should_secure_cookie(request: Request) -> bool:
    """判断是否应设置 Secure Cookie。

    说明：
    - 在 HTTPS 下应设置 Secure；HTTP 下设置会导致浏览器不回传 Cookie。
    - 生产环境通常有反向代理（Nginx）终止 TLS，因此优先读取 `X-Forwarded-Proto`。
    """

    xf_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    if xf_proto in {"http", "https"}:
        return xf_proto == "https"
    return (request.url.scheme or "").lower() == "https"


class ClientIdCookieMiddleware(BaseHTTPMiddleware):
    """为每个请求注入 `request.state.client_id`，必要时下发 Cookie。"""

    def __init__(
        self,
        app: Any,
        *,
        cookie_name: str = DEFAULT_COOKIE_NAME,
        max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
    ) -> None:
        super().__init__(app)
        self.cookie_name = str(cookie_name or DEFAULT_COOKIE_NAME)
        self.max_age_seconds = int(max_age_seconds or DEFAULT_MAX_AGE_SECONDS)

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # type: ignore[override]
        raw = request.cookies.get(self.cookie_name, "") or ""
        client_id = _normalize_uuid(raw)
        need_set_cookie = False
        if not client_id:
            client_id = str(uuid.uuid4())
            need_set_cookie = True

        # 业务侧统一从这里读取，不要重复解析 cookie
        request.state.client_id = client_id

        response = await call_next(request)

        # 仅在缺失/非法时下发，减少每次响应都 set-cookie 的噪声
        if need_set_cookie:
            response.set_cookie(
                key=self.cookie_name,
                value=client_id,
                max_age=self.max_age_seconds,
                httponly=True,
                samesite="lax",
                secure=_should_secure_cookie(request),
                path="/",
            )

        return response

