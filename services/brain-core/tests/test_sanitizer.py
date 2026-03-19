"""审计日志脱敏工具测试"""

from src.common.sanitizer import (
    mask_email, mask_phone, mask_token, mask_ip, mask_content,
    sanitize_dict, sanitize_for_log,
)


def test_mask_email():
    assert mask_email("alice@example.com") == "a****@example.com"
    assert mask_email("a@b.com") == "*@b.com"
    assert mask_email("abcdef@test.io") == "a*****@test.io"


def test_mask_phone():
    assert mask_phone("13812341234") == "138****1234"
    assert mask_phone("+86-138-1234-1234") == "861******1234"
    assert mask_phone("123") == "***"


def test_mask_token():
    assert mask_token("eyJhbGciOiJIUzI1NiJ9.xyz") == "eyJh....xyz"
    assert mask_token("short") == "***"


def test_mask_ip():
    assert mask_ip("192.168.1.100") == "192.168.*.*"
    assert mask_ip("10.0.0.1") == "10.0.*.*"


def test_mask_content():
    short = "hello"
    assert mask_content(short) == "hello"
    long = "a" * 200
    result = mask_content(long, max_len=50)
    assert "200 chars" in result
    assert len(result) < 200


def test_sanitize_dict():
    data = {
        "email": "alice@test.com",
        "password": "secret123",
        "content": "a" * 100,
        "ip": "10.0.0.1",
        "token": "eyJhbGciOiJIUzI1NiJ9.abcdef",
        "name": "Alice",
    }
    result = sanitize_dict(data)
    assert result["password"] == "***"
    assert "alice" not in result["email"]
    assert result["name"] == "Alice"
    assert "10.0" in result["ip"]
    assert "100 chars" in result["content"]


def test_sanitize_nested():
    data = {
        "user": {
            "email": "bob@test.com",
            "password": "pass",
        },
        "items": [{"token": "abcdefghijklmnop"}],
    }
    result = sanitize_dict(data)
    assert result["user"]["password"] == "***"
    assert result["items"][0]["token"] == "abcd...mnop"


def test_sanitize_for_log_error():
    """传入非dict不崩溃"""
    result = sanitize_for_log({})
    assert isinstance(result, dict)
