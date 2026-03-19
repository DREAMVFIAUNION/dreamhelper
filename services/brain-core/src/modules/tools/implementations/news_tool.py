"""实时新闻工具 — RSS Feeds 解析 (完全免费, 零 API Key)

数据源: 主要科技/财经/AI 媒体的 RSS feeds
解析: 标准库 xml.etree.ElementTree (零依赖)
"""

import re
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool

_HEADERS = {
    "User-Agent": "DreamHelper/3.4 (news-tool)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# RSS 源分类
RSS_FEEDS: dict[str, list[dict[str, str]]] = {
    "tech": [
        {"name": "Hacker News", "url": "https://hnrss.org/frontpage?count=10"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    ],
    "ai": [
        {"name": "AI News (HN)", "url": "https://hnrss.org/frontpage?q=AI+OR+LLM+OR+GPT+OR+Claude&count=10"},
        {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    ],
    "finance": [
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
        {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
    ],
    "crypto": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "Crypto (HN)", "url": "https://hnrss.org/frontpage?q=bitcoin+OR+ethereum+OR+crypto&count=10"},
    ],
    "world": [
        {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "Reuters", "url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"},
    ],
    "china": [
        {"name": "36氪", "url": "https://36kr.com/feed"},
        {"name": "少数派", "url": "https://sspai.com/feed"},
    ],
}


class NewsArgs(BaseModel):
    action: str = Field(
        default="headlines",
        description="操作: 'headlines'(头条新闻), 'category'(分类新闻), 'search'(搜索新闻)",
    )
    category: str = Field(
        default="tech",
        description="分类: 'tech'(科技), 'ai'(AI), 'finance'(财经), 'crypto'(加密货币), 'world'(国际), 'china'(中文科技)",
    )
    query: str = Field(default="", description="搜索关键词(action=search时用)")
    max_results: int = Field(default=5, description="返回条数, 默认5")


class NewsTool(BaseTool):
    name = "news"
    description = (
        "实时新闻查询工具(免费RSS无Key)。支持:\n"
        "- action=headlines: 获取头条新闻(category='tech'/'ai'/'finance'/'crypto'/'world'/'china')\n"
        "- action=category: 指定分类新闻\n"
        "- action=search: 搜索特定主题新闻(query='AI')\n"
        "数据源: Hacker News, TechCrunch, BBC, Yahoo Finance, CoinDesk, 36氪 等"
    )
    args_schema = NewsArgs

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "headlines")
        category = kwargs.get("category", "tech").lower()
        max_results = min(int(kwargs.get("max_results", 5)), 15)

        try:
            if action in ("headlines", "category"):
                feeds = RSS_FEEDS.get(category, RSS_FEEDS["tech"])
                articles = await self._fetch_feeds(feeds, max_results)
                cat_label = {
                    "tech": "科技", "ai": "AI/人工智能", "finance": "财经",
                    "crypto": "加密货币", "world": "国际", "china": "中文科技",
                }.get(category, category)
                return self._format_articles(f"📰 {cat_label}新闻", articles, max_results)

            elif action == "search":
                query = kwargs.get("query", "")
                if not query:
                    return "请提供搜索关键词 query"
                # 搜索: 用 HN 搜索 RSS
                feeds = [
                    {"name": "HN Search", "url": f"https://hnrss.org/newest?q={query}&count={max_results}"},
                ]
                articles = await self._fetch_feeds(feeds, max_results)
                return self._format_articles(f"🔍 搜索: {query}", articles, max_results)

            return f"未知操作: {action}"
        except Exception as e:
            logging.getLogger(__name__).exception("News fetch failed")
            return "❌ 新闻获取失败"

    async def _fetch_feeds(self, feeds: list[dict], max_per_feed: int) -> list[dict]:
        """并行获取多个 RSS 源"""
        articles: list[dict] = []
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            for feed in feeds:
                try:
                    resp = await client.get(feed["url"], headers=_HEADERS)
                    if resp.status_code != 200:
                        continue
                    items = self._parse_rss(resp.text, feed["name"], max_per_feed)
                    articles.extend(items)
                except Exception:
                    continue
        # 按时间排序(如果有)
        articles.sort(key=lambda a: a.get("pub_date", ""), reverse=True)
        return articles

    def _parse_rss(self, xml_text: str, source: str, max_items: int) -> list[dict]:
        """解析 RSS/Atom XML"""
        items: list[dict] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return items

        # RSS 2.0 格式
        for item in root.iter("item"):
            if len(items) >= max_items:
                break
            title = self._get_text(item, "title")
            link = self._get_text(item, "link")
            desc = self._get_text(item, "description")
            pub_date = self._get_text(item, "pubDate")
            if title:
                items.append({
                    "title": self._clean(title),
                    "link": link,
                    "description": self._clean(desc)[:200] if desc else "",
                    "pub_date": pub_date,
                    "source": source,
                })

        # Atom 格式 fallback
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                if len(items) >= max_items:
                    break
                title = self._get_text_ns(entry, "atom:title", ns)
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                summary = self._get_text_ns(entry, "atom:summary", ns)
                updated = self._get_text_ns(entry, "atom:updated", ns)
                if title:
                    items.append({
                        "title": self._clean(title),
                        "link": link,
                        "description": self._clean(summary)[:200] if summary else "",
                        "pub_date": updated,
                        "source": source,
                    })

        return items

    def _format_articles(self, header: str, articles: list[dict], max_show: int) -> str:
        if not articles:
            return f"{header}\n  暂无相关新闻"
        lines = [header]
        for i, a in enumerate(articles[:max_show], 1):
            src = a.get("source", "")
            title = a["title"]
            desc = a.get("description", "")
            link = a.get("link", "")
            line = f"  {i}. [{src}] {title}"
            if desc:
                line += f"\n     {desc}"
            if link:
                line += f"\n     🔗 {link}"
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _get_text(el: ET.Element, tag: str) -> str:
        child = el.find(tag)
        return child.text.strip() if child is not None and child.text else ""

    @staticmethod
    def _get_text_ns(el: ET.Element, tag: str, ns: dict) -> str:
        child = el.find(tag, ns)
        return child.text.strip() if child is not None and child.text else ""

    @staticmethod
    def _clean(text: str) -> str:
        """清理 HTML 标签和多余空白"""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
