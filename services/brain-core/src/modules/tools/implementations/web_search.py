"""网络搜索工具 — DuckDuckGo lite HTML 解析 (零 API Key)"""

import re
import logging
from typing import Any
from urllib.parse import quote_plus

import httpx
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


class WebSearchArgs(BaseModel):
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=3, description="返回结果数量，默认3条")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "搜索互联网获取最新信息。输入搜索关键词，返回相关网页摘要。适用于查询实时信息、新闻、天气、股价等。"
    args_schema = WebSearchArgs

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        max_results = min(int(kwargs.get("max_results", 3)), 5)

        if not query:
            return "请提供搜索关键词"

        try:
            results = await self._ddg_search(query, max_results)
            if results:
                lines = [f"[搜索结果] 关键词: '{query}'"]
                for i, r in enumerate(results, 1):
                    lines.append(f"{i}. {r['title']}\n   {r['snippet']}\n   链接: {r['url']}")
                return "\n".join(lines)
            return f"[搜索结果] 关键词: '{query}' — 未找到相关结果"
        except Exception as e:
            logging.getLogger(__name__).exception("Web search failed")
            return "[搜索错误] 请稍后重试"

    async def _ddg_search(self, query: str, max_results: int) -> list[dict]:
        """通过 DuckDuckGo lite HTML 页面解析搜索结果"""
        url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()
            html = resp.text

        results: list[dict] = []
        # DuckDuckGo lite 使用 <a class="result-link"> 和后续 <td> 放摘要
        link_pattern = re.compile(
            r'<a[^>]+class="result-link"[^>]*href="([^"]+)"[^>]*>(.+?)</a>',
            re.DOTALL,
        )
        snippet_pattern = re.compile(
            r'<td[^>]+class="result-snippet"[^>]*>(.*?)</td>',
            re.DOTALL,
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (href, title_raw) in enumerate(links[:max_results]):
            title = re.sub(r"<[^>]+>", "", title_raw).strip()
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()
            if title:
                results.append({"title": title, "url": href, "snippet": snippet or "无摘要"})

        # 如果 lite 页面格式变了，尝试通用 <a> + <td> 解析
        if not results:
            generic_links = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>', html)
            for href, title in generic_links[:max_results]:
                if "duckduckgo" not in href:
                    results.append({"title": title.strip(), "url": href, "snippet": "—"})

        return results
