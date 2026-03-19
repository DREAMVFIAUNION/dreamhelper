"""Webhook 接收器测试"""

import hashlib
import hmac
import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.modules.webhook.router import router, _event_log, _verify_signature


@pytest.fixture
def app():
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1")
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_events():
    _event_log.clear()
    yield
    _event_log.clear()


def test_receive_webhook(client):
    """接收 Webhook 事件"""
    resp = client.post(
        "/api/v1/webhook/github.push",
        json={"repo": "dreamhelp-v3", "ref": "refs/heads/main"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert data["event_type"] == "github.push"
    assert data["timestamp"]


def test_webhook_events_logged(client):
    """事件被记录到内存队列"""
    client.post("/api/v1/webhook/custom.notify", json={"msg": "hello"})
    client.post("/api/v1/webhook/custom.alert", json={"level": "warn"})

    resp = client.get("/api/v1/webhook/events?limit=10")
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) == 2
    assert events[0]["event_type"] == "custom.notify"
    assert events[1]["event_type"] == "custom.alert"


def test_webhook_stats(client):
    """统计信息"""
    client.post("/api/v1/webhook/github.push", json={})
    client.post("/api/v1/webhook/github.push", json={})
    client.post("/api/v1/webhook/monitor.alert", json={})

    resp = client.get("/api/v1/webhook/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_events"] == 3
    assert data["event_types"]["github.push"] == 2
    assert data["event_types"]["monitor.alert"] == 1


def test_verify_signature_valid():
    """有效签名验证通过"""
    secret = "test-secret"
    body = b'{"test": true}'
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    sig = f"sha256={expected}"

    with patch("src.modules.webhook.router.settings") as mock_settings:
        mock_settings.WEBHOOK_SECRET = secret
        assert _verify_signature(body, sig) is True


def test_verify_signature_invalid():
    """无效签名被拒绝"""
    with patch("src.modules.webhook.router.settings") as mock_settings:
        mock_settings.WEBHOOK_SECRET = "real-secret"
        assert _verify_signature(b"body", "sha256=fake") is False


def test_verify_signature_no_secret():
    """未配置 secret 时跳过验证"""
    with patch("src.modules.webhook.router.settings") as mock_settings:
        mock_settings.WEBHOOK_SECRET = ""
        assert _verify_signature(b"body", None) is True
