"""API 认证中间件 — 保护 brain-core 敏感端点

开发模式: 允许无 key 访问（便于调试）
生产模式: 必须携带 Authorization: Bearer <API_KEY> 或 X-API-Key header

公开端点（无需认证）:
- /health, /metrics, /docs, /openapi.json
- /api/v1/webhook/* (有独立的签名验证)
"""

import hmac
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# 无需认证的路径前缀
PUBLIC_PREFIXES = (
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/webhook",
)


class APIAuthMiddleware(BaseHTTPMiddleware):
    """
    API Key 认证中间件

    - 开发环境: 跳过认证（BRAIN_API_KEY 为空时自动跳过）
    - 生产环境: 检查 Authorization: Bearer <key> 或 X-API-Key header
    """

    def __init__(self, app, *, api_key: str = "", env: str = "development"):
        super().__init__(app)
        self.api_key = api_key
        self.env = env
        self.enabled = bool(api_key)

        if self.enabled:
            logger.info("API auth: enabled (key: %s...)", api_key[:8])
        else:
            logger.info("API auth: disabled (no BRAIN_API_KEY set)")

    async def dispatch(self, request: Request, call_next):
        # 未启用时直接放行
        if not self.enabled:
            return await call_next(request)

        path = request.url.path

        # 公开端点无需认证
        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return await call_next(request)

        # OPTIONS 预检请求放行
        if request.method == "OPTIONS":
            return await call_next(request)

        # 提取 API Key
        key = self._extract_key(request)

        if not key:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing API key. Use Authorization: Bearer <key> or X-API-Key header."},
            )

        if not hmac.compare_digest(key, self.api_key):
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid API key."},
            )

        return await call_next(request)

    @staticmethod
    def _extract_key(request: Request) -> str | None:
        """从请求头提取 API Key"""
        # 优先 Authorization: Bearer <key>
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:].strip()

        # 备选 X-API-Key
        x_key = request.headers.get("x-api-key", "")
        if x_key:
            return x_key.strip()

        return None
