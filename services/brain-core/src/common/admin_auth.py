"""管理端点鉴权 — P0-#4 安全审计修复

用法:
    from ...common.admin_auth import require_admin

    @router.post("/config")
    async def update_config(request: Request, _=Depends(require_admin)):
        ...

或作为路由级依赖:
    app.include_router(router, dependencies=[Depends(require_admin)])
"""

import hmac
import logging
from fastapi import Depends, HTTPException, Request

from .config import settings

logger = logging.getLogger(__name__)


async def require_admin(request: Request) -> None:
    """FastAPI 依赖: 校验管理员密钥

    - BRAIN_ADMIN_KEY 为空时 (开发模式): 跳过校验
    - 生产环境: 必须携带 X-Admin-Key header 且值匹配
    """
    admin_key = settings.BRAIN_ADMIN_KEY
    if not admin_key:
        # 开发模式，跳过
        return

    provided = request.headers.get("x-admin-key", "").strip()

    if not hmac.compare_digest(provided, admin_key):
        logger.warning(
            "Admin auth failed: path=%s, ip=%s",
            request.url.path,
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="需要管理员权限")
