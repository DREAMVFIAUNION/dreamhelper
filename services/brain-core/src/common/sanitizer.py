"""审计日志脱敏工具 — 敏感信息自动掩码

用于日志输出、审计记录中的敏感字段脱敏:
- 邮箱: a**@example.com
- 手机: 138****1234
- Token/密钥: 前4后4保留，中间掩码
- IP: 保留前两段
- 消息内容: 截断 + 掩码
"""

import re
from typing import Any


# ── 脱敏规则 ──

def mask_email(email: str) -> str:
    """a]**@example.com"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}{'*' * min(len(local) - 1, 6)}@{domain}"


def mask_phone(phone: str) -> str:
    """138****1234"""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return "***"
    return f"{digits[:3]}{'*' * (len(digits) - 7)}{digits[-4:]}"


def mask_token(token: str) -> str:
    """eyJh...xyz"""
    if len(token) <= 12:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def mask_ip(ip: str) -> str:
    """192.168.*.*"""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    # IPv6 简化
    return ip[:8] + "..."


def mask_content(content: str, max_len: int = 50) -> str:
    """截断长文本，仅保留摘要"""
    if len(content) <= max_len:
        return content
    return content[:max_len] + f"... [{len(content)} chars]"


# ── 通用脱敏器 ──

_SENSITIVE_KEYS = {
    "email", "password", "password_hash", "token", "api_key", "secret",
    "authorization", "cookie", "jwt", "access_token", "refresh_token",
    "phone", "mobile", "ip", "ip_address", "user_agent",
}

_CONTENT_KEYS = {"content", "message", "body", "text", "input", "output"}


def sanitize_dict(data: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    """递归脱敏字典中的敏感字段"""
    if depth > 5:
        return {"__truncated__": True}

    result = {}
    for key, value in data.items():
        k_lower = key.lower()

        if k_lower in {"password", "password_hash", "secret", "api_key"}:
            result[key] = "***"
        elif k_lower in {"email"}:
            result[key] = mask_email(str(value)) if isinstance(value, str) else "***"
        elif k_lower in {"phone", "mobile"}:
            result[key] = mask_phone(str(value)) if isinstance(value, str) else "***"
        elif k_lower in {"token", "jwt", "access_token", "refresh_token", "authorization"}:
            result[key] = mask_token(str(value)) if isinstance(value, str) else "***"
        elif k_lower in {"ip", "ip_address"}:
            result[key] = mask_ip(str(value)) if isinstance(value, str) else "***"
        elif k_lower in _CONTENT_KEYS and isinstance(value, str):
            result[key] = mask_content(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, depth + 1) if isinstance(item, dict) else item
                for item in value[:20]  # 限制列表长度
            ]
        else:
            result[key] = value

    return result


def sanitize_for_log(data: dict[str, Any]) -> dict[str, Any]:
    """日志输出专用 — 深拷贝 + 脱敏"""
    try:
        return sanitize_dict(dict(data))
    except Exception:
        return {"__sanitize_error__": True}
