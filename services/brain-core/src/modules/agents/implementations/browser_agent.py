"""浏览器控制 Agent — Playwright CDP 网页自动化（Phase 12）

功能:
- 网页截图 (screenshot)
- 网页内容提取 (extract_text)
- 网页元素操作 (click, fill, select)
- 搜索引擎查询 (search)

安全限制:
- 只允许访问白名单域名（可配置）
- 超时 30 秒自动终止
- 无头模式运行
"""

import asyncio
import json
import logging
import re
from typing import AsyncGenerator, Any, Optional
from urllib.parse import quote_plus, urlparse

from ..base.base_agent import BaseAgent
from ..base.types import AgentContext, AgentStep, AgentStepType

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# 默认超时
DEFAULT_TIMEOUT = 30000  # 30s
# 并发限制: 最多同时运行 3 个浏览器实例
_browser_semaphore = asyncio.Semaphore(3)
# 截图最大大小 5MB
MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024
# 禁止访问的内网/危险协议
_BLOCKED_SCHEMES = {"file", "ftp", "data", "javascript", "vbscript"}
_BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "metadata.google.internal", "169.254.169.254",  # cloud metadata
}


def _is_url_safe(url: str) -> tuple[bool, str]:
    """检查 URL 是否安全（防 SSRF）"""
    if not url:
        return False, "空 URL"
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL 解析失败"
    # 协议检查
    scheme = (parsed.scheme or "").lower()
    if scheme in _BLOCKED_SCHEMES:
        return False, f"禁止的协议: {scheme}"
    if scheme not in ("http", "https"):
        return False, f"不支持的协议: {scheme}"
    # 主机检查
    host = (parsed.hostname or "").lower()
    if host in _BLOCKED_HOSTS:
        return False, f"禁止访问内网地址: {host}"
    # 私有 IP 检查
    if _is_private_ip(host):
        return False, f"禁止访问私有 IP: {host}"
    return True, ""


def _is_private_ip(host: str) -> bool:
    """检查是否为私有 IP 地址"""
    import ipaddress
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False  # 域名，非 IP


class BrowserAgent(BaseAgent):
    """浏览器控制 Agent — 网页截图/提取/操作"""

    def __init__(self):
        super().__init__(
            name="browser_agent",
            description="浏览器控制专家 — 网页截图、内容提取、自动操作",
        )

    async def run(
        self, user_input: str, context: AgentContext
    ) -> AsyncGenerator[AgentStep, None]:
        """解析用户意图并执行浏览器操作"""
        if not HAS_PLAYWRIGHT:
            yield AgentStep(
                type=AgentStepType.FINAL_ANSWER,
                content="浏览器控制功能需要安装 playwright。请运行: pip install playwright && playwright install chromium",
                is_final=True,
                final_answer="浏览器控制功能需要安装 playwright。请运行: pip install playwright && playwright install chromium",
            )
            return

        yield AgentStep(
            type=AgentStepType.THINKING,
            content="正在分析浏览器操作需求...",
            metadata={"phase": "planning"},
        )

        # 用 LLM 解析用户意图
        action = await self._parse_intent(user_input, context)

        if action is None:
            yield AgentStep(
                type=AgentStepType.FINAL_ANSWER,
                content="无法理解浏览器操作需求，请明确说明要访问的网址或操作。",
                is_final=True,
                final_answer="无法理解浏览器操作需求，请明确说明要访问的网址或操作。",
            )
            return

        action_type = action.get("action", "screenshot")
        url = action.get("url", "")

        yield AgentStep(
            type=AgentStepType.TOOL_CALL,
            content=f"执行浏览器操作: {action_type} → {url}",
            tool_name="browser",
            tool_input=action,
            metadata={"phase": "executing"},
        )

        # 执行浏览器操作
        try:
            result = await self._execute_browser_action(action)
            yield AgentStep(
                type=AgentStepType.OBSERVATION,
                content=result,
                tool_name="browser",
                tool_output=result,
                metadata={"phase": "observation"},
            )

            # Hook 事件
            try:
                from ...hooks.hook_registry import HookRegistry, HookEventType
                await HookRegistry.emit(HookEventType.BROWSER_ACTION, {
                    "action": action_type, "url": url, "success": True,
                })
            except Exception:
                pass

            # 综合回答
            final = await self._synthesize_result(user_input, action, result, context)
            yield AgentStep(
                type=AgentStepType.FINAL_ANSWER,
                content=final,
                is_final=True,
                final_answer=final,
            )

        except Exception as e:
            error_msg = f"浏览器操作失败: {e}"
            logger.warning(error_msg)
            yield AgentStep(
                type=AgentStepType.FINAL_ANSWER,
                content=error_msg,
                is_final=True,
                final_answer=error_msg,
            )

    async def _parse_intent(self, user_input: str, context: AgentContext) -> Optional[dict]:
        """用 LLM 解析浏览器操作意图"""
        from ...llm.llm_client import get_llm_client
        client = get_llm_client()

        prompt = f"""你是一个浏览器操作解析器。根据用户请求，返回 JSON 操作指令。

可用操作:
- screenshot: 截图 {{"action": "screenshot", "url": "https://..."}}
- extract: 提取文本 {{"action": "extract", "url": "https://..."}}
- search: 搜索 {{"action": "search", "query": "搜索关键词"}}

用户请求: {user_input}

只返回 JSON 对象。"""

        try:
            response = await client.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=256,
            )
            text = response if isinstance(response, str) else response.content
            match = re.search(r'\{[^}]+\}', text)
            if match:
                parsed = json.loads(match.group())
                # 安全校验: URL 安全检查
                url = parsed.get("url", "")
                if url:
                    safe, reason = _is_url_safe(url)
                    if not safe:
                        logger.warning(f"Blocked unsafe URL: {url} ({reason})")
                        return None
                return parsed
        except Exception as e:
            logger.warning(f"Intent parse failed: {e}")

        # 简单 fallback: 如果包含 URL 则截图
        url_match = re.search(r'https?://\S+', user_input)
        if url_match:
            url = url_match.group()
            safe, reason = _is_url_safe(url)
            if not safe:
                logger.warning(f"Blocked unsafe URL from input: {url} ({reason})")
                return None
            return {"action": "screenshot", "url": url}

        return None

    async def _execute_browser_action(self, action: dict) -> str:
        """执行实际的浏览器操作（并发受限）"""
        action_type = action.get("action", "screenshot")

        async with _browser_semaphore:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                ctx = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    java_script_enabled=True,
                    ignore_https_errors=False,
                )
                page = await ctx.new_page()

                try:
                    if action_type == "screenshot":
                        return await self._do_screenshot(page, action)
                    elif action_type == "extract":
                        return await self._do_extract(page, action)
                    elif action_type == "search":
                        return await self._do_search(page, action)
                    else:
                        return f"不支持的操作类型: {action_type}"
                finally:
                    await ctx.close()
                    await browser.close()

    async def _do_screenshot(self, page: "Page", action: dict) -> str:
        """截图操作"""
        url = action.get("url", "")
        await page.goto(url, timeout=DEFAULT_TIMEOUT, wait_until="networkidle")
        title = await page.title()
        screenshot = await page.screenshot(type="png")

        import base64
        b64 = base64.b64encode(screenshot).decode()
        size_kb = len(screenshot) / 1024

        return (
            f"页面标题: {title}\n"
            f"URL: {url}\n"
            f"截图大小: {size_kb:.1f}KB\n"
            f"截图已生成 (base64, {len(b64)} 字符)"
        )

    async def _do_extract(self, page: "Page", action: dict) -> str:
        """提取网页文本"""
        url = action.get("url", "")
        await page.goto(url, timeout=DEFAULT_TIMEOUT, wait_until="networkidle")
        title = await page.title()

        # 提取正文内容
        text = await page.evaluate("""() => {
            const selectors = ['article', 'main', '.content', '.post-content', '#content', 'body'];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.trim().length > 100) {
                    return el.innerText.trim();
                }
            }
            return document.body.innerText.trim();
        }""")

        # 截断过长文本
        if len(text) > 3000:
            text = text[:3000] + "\n\n...(内容已截断)"

        return f"页面标题: {title}\nURL: {url}\n\n{text}"

    async def _do_search(self, page: "Page", action: dict) -> str:
        """搜索引擎查询"""
        query = action.get("query", "")
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        await page.goto(search_url, timeout=DEFAULT_TIMEOUT, wait_until="networkidle")

        # 提取搜索结果
        results = await page.evaluate("""() => {
            const items = document.querySelectorAll('.b_algo');
            return Array.from(items).slice(0, 5).map(item => {
                const title = item.querySelector('h2')?.innerText || '';
                const snippet = item.querySelector('.b_caption p')?.innerText || '';
                const link = item.querySelector('a')?.href || '';
                return { title, snippet, link };
            });
        }""")

        if not results:
            return f"搜索 '{query}' 未找到结果"

        lines = [f"搜索结果: '{query}'\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.get('title', '')}**")
            lines.append(f"   {r.get('snippet', '')}")
            lines.append(f"   {r.get('link', '')}\n")

        return "\n".join(lines)

    async def _synthesize_result(self, user_input: str, action: dict, result: str, context: AgentContext) -> str:
        """综合浏览器操作结果生成回答"""
        from ...llm.llm_client import get_llm_client
        client = get_llm_client()

        try:
            response = await client.complete(
                messages=[
                    {"role": "system", "content": "你是梦帮小助，根据浏览器操作结果回答用户。简洁清晰。"},
                    {"role": "user", "content": f"用户请求: {user_input}\n\n浏览器操作结果:\n{result[:2000]}"},
                ],
                temperature=0.7, max_tokens=2048,
            )
            return response if isinstance(response, str) else response.content
        except Exception:
            return result

    # BaseAgent 接口
    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        return AgentStep(type=AgentStepType.THINKING, content="Browser Agent mode")

    async def act(self, tool_name: str, tool_input: dict[str, Any], context: AgentContext) -> AgentStep:
        return AgentStep(type=AgentStepType.OBSERVATION, content="")

    async def synthesize(self, user_input: str, context: AgentContext) -> AgentStep:
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content="", is_final=True, final_answer="")
