"""安全 HTTP 响应头中间件 — 防 XSS / Clickjacking / MIME 嗅探"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """注入安全响应头，生产环境启用 HSTS"""

    def __init__(self, app, *, env: str = "development"):
        super().__init__(app)
        self.env = env

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 防 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 防 Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS 过滤（旧浏览器兼容）
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 引用来源策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略 — 禁用不必要的浏览器功能
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # HSTS — 仅非开发环境启用
        if self.env != "development":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
