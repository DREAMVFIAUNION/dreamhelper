"""代码执行沙箱测试 — 安全检查 + 子进程执行"""

import asyncio
import re
import sys
import tempfile


# ── 内联安全检查逻辑（避免相对导入问题） ──

_BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "socket", "signal",
    "ctypes", "importlib", "builtins", "__builtins__",
    "pathlib", "glob", "tempfile", "webbrowser", "http",
    "ftplib", "smtplib", "telnetlib", "xmlrpc", "multiprocessing",
    "threading", "pickle", "shelve", "marshal",
}

_BLOCKED_PATTERNS = [
    r"\bopen\s*\(",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"\bcompile\s*\(",
    r"__import__",
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
    r"\bdelattr\s*\(",
    r"\bglobals\s*\(",
    r"\blocals\s*\(",
]


def _check_code_safety(code: str) -> str | None:
    import_pattern = re.compile(r'(?:from\s+(\w+)|import\s+(\w+))')
    for match in import_pattern.finditer(code):
        module = match.group(1) or match.group(2)
        if module in _BLOCKED_IMPORTS:
            return f"安全限制: 禁止导入模块 '{module}'"
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, code):
            return f"安全限制: 检测到危险操作"
    return None


# ── 安全检查测试 ──

def test_block_os_import():
    """禁止导入 os 模块"""
    err = _check_code_safety("import os\nos.system('ls')")
    assert err is not None
    assert "os" in err


def test_block_subprocess_import():
    """禁止导入 subprocess"""
    err = _check_code_safety("import subprocess")
    assert err is not None
    assert "subprocess" in err


def test_block_from_import():
    """禁止 from ... import"""
    err = _check_code_safety("from shutil import rmtree")
    assert err is not None
    assert "shutil" in err


def test_block_open():
    """禁止 open() 文件操作"""
    err = _check_code_safety("f = open('/etc/passwd', 'r')")
    assert err is not None


def test_block_exec():
    """禁止 exec()"""
    err = _check_code_safety("exec('print(1)')")
    assert err is not None


def test_block_eval():
    """禁止 eval()"""
    err = _check_code_safety("result = eval('1+1')")
    assert err is not None


def test_block_dunder_import():
    """禁止 __import__"""
    err = _check_code_safety("m = __import__('os')")
    assert err is not None


def test_allow_safe_code():
    """安全代码通过检查"""
    err = _check_code_safety("import math\nprint(math.sqrt(16))")
    assert err is None


def test_allow_json():
    """允许导入 json"""
    err = _check_code_safety("import json\nprint(json.dumps({'a': 1}))")
    assert err is None


# ── 子进程执行测试 ──

def test_execute_simple():
    """简单代码执行"""
    async def _run():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("print(2 + 3)")
            path = f.name
        proc = await asyncio.create_subprocess_exec(
            sys.executable, path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        return stdout.decode().strip()

    result = asyncio.run(_run())
    assert result == "5"


def test_execute_timeout():
    """超时终止"""
    async def _run():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("import time\ntime.sleep(60)")
            path = f.name
        proc = await asyncio.create_subprocess_exec(
            sys.executable, path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=2)
            return "completed"
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return "timeout"

    result = asyncio.run(_run())
    assert result == "timeout"
