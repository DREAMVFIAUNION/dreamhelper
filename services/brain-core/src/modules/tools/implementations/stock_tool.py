"""全球股市工具 — Yahoo Finance 非官方 API (免费, 零 API Key)

数据源: https://query1.finance.yahoo.com/v8/finance/chart/
支持: 实时股价、涨跌幅、交易量、主要指数、日K线
"""

import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# 全球主要指数预设
MAJOR_INDICES: dict[str, str] = {
    # 美国
    "标普500": "^GSPC", "sp500": "^GSPC", "s&p500": "^GSPC",
    "纳斯达克": "^IXIC", "nasdaq": "^IXIC",
    "道琼斯": "^DJI", "道指": "^DJI", "dow": "^DJI",
    # 中国
    "上证": "000001.SS", "上证指数": "000001.SS", "沪指": "000001.SS",
    "深证": "399001.SZ", "深证成指": "399001.SZ",
    "创业板": "399006.SZ", "创业板指": "399006.SZ",
    "恒生": "^HSI", "恒生指数": "^HSI", "港股": "^HSI",
    # 日本
    "日经": "^N225", "日经225": "^N225", "nikkei": "^N225",
    # 欧洲
    "富时100": "^FTSE", "ftse": "^FTSE",
    "德国dax": "^GDAXI", "dax": "^GDAXI",
    "法国cac": "^FCHI", "cac40": "^FCHI",
    # 其他
    "韩国kospi": "^KS11", "kospi": "^KS11",
    "台湾加权": "^TWII",
    "印度sensex": "^BSESN", "sensex": "^BSESN",
    # 大宗商品
    "黄金": "GC=F", "gold": "GC=F",
    "原油": "CL=F", "oil": "CL=F", "wti": "CL=F",
    "白银": "SI=F", "silver": "SI=F",
}

# 热门科技股
POPULAR_STOCKS: dict[str, str] = {
    "苹果": "AAPL", "谷歌": "GOOGL", "微软": "MSFT",
    "亚马逊": "AMZN", "特斯拉": "TSLA", "英伟达": "NVDA",
    "脸书": "META", "meta": "META", "台积电": "TSM",
    "腾讯": "0700.HK", "阿里巴巴": "BABA", "阿里": "BABA",
    "比亚迪": "1211.HK", "小米": "1810.HK",
}


def _resolve_symbol(input_str: str) -> str:
    """将中文名/缩写解析为 Yahoo Finance 符号"""
    key = input_str.strip().lower()
    if key in MAJOR_INDICES:
        return MAJOR_INDICES[key]
    if key in POPULAR_STOCKS:
        return POPULAR_STOCKS[key]
    # 直接返回（可能是 AAPL, 000001.SZ 等）
    return input_str.strip().upper()


class StockArgs(BaseModel):
    action: str = Field(
        default="quote",
        description="操作: 'quote'(实时报价), 'indices'(全球主要指数), 'chart'(日K线)",
    )
    symbol: str = Field(
        default="",
        description="股票代码或名称: 'AAPL', '苹果', '000001.SZ', '标普500', '纳斯达克'",
    )
    symbols: str = Field(
        default="",
        description="多个股票逗号分隔(action=quote时批量查询), 如 'AAPL,GOOGL,MSFT'",
    )
    period: str = Field(
        default="5d",
        description="K线周期: '1d','5d','1mo','3mo','6mo','1y'(action=chart时用)",
    )


class StockTool(BaseTool):
    name = "stock"
    description = (
        "全球股市实时查询工具(免费无Key)。支持:\n"
        "- action=quote: 实时报价(symbol='AAPL'或'苹果'或'000001.SZ')\n"
        "- action=indices: 全球主要指数概览(标普/纳斯达克/上证/恒生/日经/DAX)\n"
        "- action=chart: 日K线数据(symbol+period='5d'/'1mo'/'1y')\n"
        "支持中文: '苹果'→AAPL, '标普500'→^GSPC, '上证'→000001.SS"
    )
    args_schema = StockArgs

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "quote")
        try:
            if action == "quote":
                symbols_str = kwargs.get("symbols", "") or kwargs.get("symbol", "")
                if not symbols_str:
                    return "请提供股票代码或名称, 如 symbol='AAPL' 或 '苹果'"
                symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]
                results = []
                for sym in symbols[:10]:
                    resolved = _resolve_symbol(sym)
                    q = await self._fetch_quote(resolved)
                    if q:
                        results.append(q)
                    else:
                        results.append(f"  {sym} ({resolved}): 查询失败")
                return "📈 股市实时报价:\n" + "\n".join(results)

            elif action == "indices":
                return await self._global_indices()

            elif action == "chart":
                symbol = kwargs.get("symbol", "")
                period = kwargs.get("period", "5d")
                if not symbol:
                    return "请提供 symbol"
                resolved = _resolve_symbol(symbol)
                return await self._fetch_chart(resolved, period, symbol)

            else:
                return f"未知操作: {action}"
        except Exception as e:
            logging.getLogger(__name__).exception("Stock query failed")
            return "❌ 股市查询失败"

    async def _fetch_quote(self, symbol: str) -> str | None:
        """获取单只股票/指数实时报价"""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"interval": "1d", "range": "2d"}
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            if resp.status_code != 200:
                return None
            data = resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            return None

        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0)
        currency = meta.get("currency", "USD")
        name = meta.get("shortName", symbol)
        exchange = meta.get("exchangeName", "")

        change = price - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0
        arrow = "🔺" if change >= 0 else "🔻"

        return (
            f"  {name} ({symbol}) [{exchange}]\n"
            f"    价格: {price:.2f} {currency}  {arrow}{change:+.2f} ({change_pct:+.2f}%)"
        )

    async def _global_indices(self) -> str:
        """全球主要指数概览"""
        index_list = [
            ("标普500", "^GSPC"), ("纳斯达克", "^IXIC"), ("道琼斯", "^DJI"),
            ("上证指数", "000001.SS"), ("深证成指", "399001.SZ"),
            ("恒生指数", "^HSI"), ("日经225", "^N225"),
            ("富时100", "^FTSE"), ("德国DAX", "^GDAXI"),
        ]
        lines = ["🌐 全球主要指数:"]
        for label, sym in index_list:
            q = await self._fetch_quote(sym)
            if q:
                lines.append(q)
            else:
                lines.append(f"  {label} ({sym}): 暂无数据")
        return "\n".join(lines)

    async def _fetch_chart(self, symbol: str, period: str, display_name: str) -> str:
        """K线数据"""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"interval": "1d", "range": period}
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            return f"❌ 无法获取 {display_name} 的K线数据"

        meta = result[0].get("meta", {})
        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
        currency = meta.get("currency", "USD")

        opens = indicators.get("open", [])
        highs = indicators.get("high", [])
        lows = indicators.get("low", [])
        closes = indicators.get("close", [])
        volumes = indicators.get("volume", [])

        from datetime import datetime, timezone
        lines = [f"📊 {display_name} ({symbol}) {period} K线 [{currency}]:"]
        lines.append(f"  {'日期':10} {'开盘':>10} {'最高':>10} {'最低':>10} {'收盘':>10} {'成交量':>12}")
        for i in range(min(len(timestamps), 30)):
            dt = datetime.fromtimestamp(timestamps[i], tz=timezone.utc).strftime("%Y-%m-%d")
            o = f"{opens[i]:.2f}" if opens[i] else "—"
            h = f"{highs[i]:.2f}" if highs[i] else "—"
            l = f"{lows[i]:.2f}" if lows[i] else "—"
            c = f"{closes[i]:.2f}" if closes[i] else "—"
            v = f"{volumes[i]:,.0f}" if volumes[i] else "—"
            lines.append(f"  {dt:10} {o:>10} {h:>10} {l:>10} {c:>10} {v:>12}")
        return "\n".join(lines)
