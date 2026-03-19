"""网页内容提取工具 — 抓取 URL 正文并返回纯文本摘要"""

import re
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}
MAX_CONTENT_LENGTH = 3000


class WebFetchArgs(BaseModel):
    url: str = Field(description="要抓取的网页 URL")
    max_chars: int = Field(default=2000, description="返回的最大字符数，默认2000")


class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "抓取网页内容并提取正文。输入 URL，返回网页的纯文本内容摘要。适用于阅读文章、查看网页详情等。"
    args_schema = WebFetchArgs

    async def execute(self, **kwargs: Any) -> str:
        url = kwargs.get("url", "")
        max_chars = min(int(kwargs.get("max_chars", 2000)), MAX_CONTENT_LENGTH)

        if not url:
            return "请提供要抓取的 URL"

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers=_HEADERS)
                resp.raise_for_status()
                html = resp.text

            # 提取标题
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else "无标题"

            # 移除 script/style/nav/footer
            for tag in ["script", "style", "nav", "footer", "header", "aside", "noscript"]:
                html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)

            # 移除所有 HTML 标签
            text = re.sub(r"<[^>]+>", " ", html)
            # 清理空白
            text = re.sub(r"\s+", " ", text).strip()
            # 移除常见噪音
            text = re.sub(r"(cookie|广告|关注我们|分享到|Copyright|©).*?(?=\. |\n|$)", "", text, flags=re.IGNORECASE)

            if not text:
                return f"[网页] {title}\n（页面内容为空或无法解析）"

            # 截断
            if len(text) > max_chars:
                text = text[:max_chars] + "...(已截断)"

            return f"[网页] {title}\nURL: {url}\n\n{text}"

        except httpx.HTTPStatusError as e:
            return f"[抓取失败] HTTP {e.response.status_code}: {url}"
        except httpx.ConnectError:
            return f"[抓取失败] 无法连接: {url}"
        except httpx.TimeoutException:
            return f"[抓取失败] 超时: {url}"
        except Exception as e:
            logging.getLogger(__name__).exception("Web fetch failed: %s", url)
            return "[抓取错误] 请稍后重试"
