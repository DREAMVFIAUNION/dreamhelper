"""Sentry 集成 — 错误追踪 + 性能监控

启用条件: SENTRY_DSN 环境变量非空
功能:
- 自动捕获未处理异常
- FastAPI 请求性能追踪
- 自定义标签 (环境, 服务名, 版本)
- LLM 调用 span (手动埋点)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_initialized = False


def init_sentry() -> bool:
    """初始化 Sentry SDK (如果配置了 DSN)

    Returns:
        True if Sentry was initialized, False otherwise
    """
    global _initialized
    if _initialized:
        return True

    from .config import settings

    if not settings.SENTRY_DSN:
        logger.info("SENTRY_DSN not set, Sentry disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENV,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=0.1,
            send_default_pii=False,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                HttpxIntegration(),
            ],
            release=f"brain-core@{_get_version()}",
            before_send=_before_send,
        )

        sentry_sdk.set_tag("service", "brain-core")
        sentry_sdk.set_tag("brain.left_model", settings.DUAL_BRAIN_LEFT_MODEL)
        sentry_sdk.set_tag("brain.right_model", settings.DUAL_BRAIN_RIGHT_MODEL)

        _initialized = True
        logger.info("Sentry initialized: env=%s sample_rate=%.1f", settings.ENV, settings.SENTRY_TRACES_SAMPLE_RATE)
        return True

    except ImportError:
        logger.info("sentry-sdk not installed, Sentry disabled")
        return False
    except Exception as e:
        logger.warning("Sentry init failed: %s", e)
        return False


def _before_send(event: dict, hint: dict) -> Optional[dict]:
    """过滤敏感信息"""
    # 不上报 ConnectionError (网络波动正常)
    if "exc_info" in hint:
        exc_type = hint["exc_info"][0]
        if exc_type and issubclass(exc_type, (ConnectionError, TimeoutError)):
            return None

    # 移除敏感 headers
    request = event.get("request", {})
    headers = request.get("headers", {})
    for key in ("authorization", "cookie", "x-api-key"):
        headers.pop(key, None)

    return event


def capture_llm_error(error: Exception, context: dict):
    """手动上报 LLM 调用错误"""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_type", "llm_call")
            scope.set_context("llm", context)
            sentry_sdk.capture_exception(error)
    except ImportError:
        pass


def _get_version() -> str:
    """获取版本号"""
    try:
        import importlib.metadata
        return importlib.metadata.version("brain-core")
    except Exception:
        return "0.1.0"
