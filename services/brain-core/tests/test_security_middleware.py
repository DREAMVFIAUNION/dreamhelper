"""安全 HTTP 响应头中间件测试"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.common.security_middleware import SecurityHeadersMiddleware


def _make_app(env: str = "development") -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, env=env)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    return app


def test_nosniff_header():
    """X-Content-Type-Options: nosniff"""
    client = TestClient(_make_app())
    resp = client.get("/test")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


def test_frame_options_header():
    """X-Frame-Options: DENY"""
    client = TestClient(_make_app())
    resp = client.get("/test")
    assert resp.headers.get("X-Frame-Options") == "DENY"


def test_xss_protection_header():
    """X-XSS-Protection"""
    client = TestClient(_make_app())
    resp = client.get("/test")
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"


def test_referrer_policy_header():
    """Referrer-Policy"""
    client = TestClient(_make_app())
    resp = client.get("/test")
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_permissions_policy_header():
    """Permissions-Policy"""
    client = TestClient(_make_app())
    resp = client.get("/test")
    pp = resp.headers.get("Permissions-Policy", "")
    assert "camera=()" in pp
    assert "microphone=()" in pp


def test_no_hsts_in_development():
    """开发模式不设 HSTS"""
    client = TestClient(_make_app(env="development"))
    resp = client.get("/test")
    assert "Strict-Transport-Security" not in resp.headers


def test_hsts_in_production():
    """生产模式启用 HSTS"""
    client = TestClient(_make_app(env="production"))
    resp = client.get("/test")
    hsts = resp.headers.get("Strict-Transport-Security", "")
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
