"""Webhook 接收器 — 接收外部系统事件通知"""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from ..hooks.hook_registry import HookRegistry, HookEventType
from ...common.admin_auth import require_admin
from ...common.config import settings
from ...common.rate_limit import limiter

router = APIRouter(prefix="/webhook", tags=["webhook"])

# 内存事件队列（生产环境可替换为 Redis Stream）
_event_log: list[dict[str, Any]] = []
_MAX_LOG_SIZE = 500


class WebhookResponse(BaseModel):
    received: bool
    event_type: str
    timestamp: str


def _verify_signature(body: bytes, signature: str | None) -> bool:
    """验证 Webhook 签名（HMAC-SHA256）"""
    if not settings.WEBHOOK_SECRET:
        # 开发环境跳过验证；生产环境无 secret 则拒绝
        return settings.ENV == "development"
    if not signature:
        return False
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@router.post("/{event_type}")
@limiter.limit("30/minute")
async def receive_webhook(
    event_type: str,
    request: Request,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
):
    """接收外部 Webhook 事件

    支持的 event_type 示例:
    - github.push / github.pr
    - custom.notify / custom.alert
    - monitor.alert
    """
    body = await request.body()

    # 签名验证
    if not _verify_signature(body, x_webhook_signature):
        return {"error": "Invalid signature", "received": False}

    # 解析 body
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {"raw": body.decode("utf-8", errors="replace")}

    now = datetime.utcnow().isoformat()

    # 记录事件
    event_record = {
        "event_type": event_type,
        "payload": payload,
        "timestamp": now,
        "source_ip": request.client.host if request.client else "unknown",
    }
    _event_log.append(event_record)
    if len(_event_log) > _MAX_LOG_SIZE:
        _event_log.pop(0)

    # 触发 Hook 事件系统
    await HookRegistry.emit(HookEventType.WEBHOOK_RECEIVE, {
        "event_type": event_type,
        "payload": payload,
    })

    return WebhookResponse(received=True, event_type=event_type, timestamp=now)


@router.get("/events")
async def list_recent_events(limit: int = 20, _=Depends(require_admin)):
    """查看最近的 Webhook 事件（需管理员权限）"""
    return {"events": _event_log[-limit:], "total": len(_event_log)}


@router.get("/stats")
async def webhook_stats(_=Depends(require_admin)):
    """Webhook 统计（需管理员权限）"""
    type_counts: dict[str, int] = {}
    for e in _event_log:
        t = e["event_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "total_events": len(_event_log),
        "event_types": type_counts,
        "hooks": HookRegistry.get_stats(),
    }
