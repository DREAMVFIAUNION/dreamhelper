"""全球加密货币工具 — CoinGecko API (免费层, 零 API Key)

数据源: https://api.coingecko.com/api/v3/
限制: 免费层 30 次/分钟, 足够日常使用
"""

import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool

_BASE = "https://api.coingecko.com/api/v3"
_HEADERS = {
    "User-Agent": "DreamHelper/3.4 (crypto-tool)",
    "Accept": "application/json",
}

# 常见币种中文别名
COIN_ALIASES: dict[str, str] = {
    "比特币": "bitcoin", "btc": "bitcoin",
    "以太坊": "ethereum", "eth": "ethereum", "以太": "ethereum",
    "狗狗币": "dogecoin", "doge": "dogecoin",
    "瑞波": "ripple", "xrp": "ripple",
    "莱特币": "litecoin", "ltc": "litecoin",
    "索拉纳": "solana", "sol": "solana",
    "艾达币": "cardano", "ada": "cardano",
    "波卡": "polkadot", "dot": "polkadot",
    "柴犬币": "shiba-inu", "shib": "shiba-inu",
    "bnb": "binancecoin", "币安币": "binancecoin",
    "泰达币": "tether", "usdt": "tether",
    "usdc": "usd-coin",
    "雪崩": "avalanche-2", "avax": "avalanche-2",
    "马蹄": "matic-network", "matic": "matic-network", "polygon": "matic-network",
    "链环": "chainlink", "link": "chainlink",
    "sui": "sui",
    "ton": "the-open-network", "toncoin": "the-open-network",
    "近协议": "near", "near": "near",
    "tron": "tron", "trx": "tron", "波场": "tron",
}


def _resolve_coin(name: str) -> str:
    key = name.strip().lower()
    return COIN_ALIASES.get(key, key)


class CryptoArgs(BaseModel):
    action: str = Field(
        default="price",
        description="操作: 'price'(实时价格), 'top'(市值排行Top N), 'detail'(详细信息), 'trending'(热门币种)",
    )
    coin: str = Field(
        default="",
        description="币种: 'bitcoin','比特币','btc','ethereum','eth' 等",
    )
    coins: str = Field(
        default="",
        description="多币种逗号分隔, 如 'btc,eth,sol'",
    )
    currency: str = Field(
        default="usd",
        description="法币: 'usd','cny','eur','jpy','krw'",
    )
    top_n: int = Field(default=10, description="排行榜数量(action=top时用), 默认10")


class CryptoTool(BaseTool):
    name = "crypto"
    description = (
        "全球加密货币实时查询工具(免费无Key)。支持:\n"
        "- action=price: 实时价格(coin='比特币' 或 'btc', 可多币种coins='btc,eth,sol')\n"
        "- action=top: 市值排行Top N(top_n=10)\n"
        "- action=detail: 详细信息(市值/流通量/24h高低/7d走势)\n"
        "- action=trending: 当前热门搜索币种\n"
        "支持法币: usd/cny/eur/jpy(currency参数)"
    )
    args_schema = CryptoArgs

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "price")
        currency = kwargs.get("currency", "usd").lower()
        try:
            if action == "price":
                return await self._price(kwargs, currency)
            elif action == "top":
                top_n = min(int(kwargs.get("top_n", 10)), 25)
                return await self._top(top_n, currency)
            elif action == "detail":
                coin = kwargs.get("coin", "")
                if not coin:
                    return "请提供 coin 参数, 如 coin='bitcoin' 或 '比特币'"
                return await self._detail(_resolve_coin(coin), currency)
            elif action == "trending":
                return await self._trending()
            else:
                return f"未知操作: {action}"
        except Exception as e:
            logging.getLogger(__name__).exception("Crypto query failed")
            return "❌ 加密货币查询失败"

    async def _price(self, kwargs: dict, currency: str) -> str:
        """实时价格查询(支持多币种)"""
        coins_str = kwargs.get("coins", "") or kwargs.get("coin", "")
        if not coins_str:
            return "请提供 coin 或 coins 参数"

        coin_list = [_resolve_coin(c.strip()) for c in coins_str.split(",") if c.strip()]
        ids = ",".join(coin_list[:20])

        url = f"{_BASE}/simple/price"
        params = {
            "ids": ids,
            "vs_currencies": currency,
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        cur_sym = {"usd": "$", "cny": "¥", "eur": "€", "jpy": "¥", "krw": "₩"}.get(currency, currency.upper())
        lines = [f"🪙 加密货币实时价格 ({currency.upper()}):"]

        for coin_id in coin_list:
            info = data.get(coin_id)
            if not info:
                lines.append(f"  {coin_id}: 未找到")
                continue
            price = info.get(currency, 0)
            change_24h = info.get(f"{currency}_24h_change", 0)
            vol_24h = info.get(f"{currency}_24h_vol", 0)
            mcap = info.get(f"{currency}_market_cap", 0)
            arrow = "🔺" if change_24h >= 0 else "🔻"

            price_str = f"{cur_sym}{price:,.2f}" if price >= 1 else f"{cur_sym}{price:.6f}"
            lines.append(
                f"  {coin_id.upper()}: {price_str}  "
                f"{arrow}{change_24h:+.2f}%  "
                f"24h量: {cur_sym}{self._fmt_num(vol_24h)}  "
                f"市值: {cur_sym}{self._fmt_num(mcap)}"
            )
        return "\n".join(lines)

    async def _top(self, top_n: int, currency: str) -> str:
        """市值排行"""
        url = f"{_BASE}/coins/markets"
        params = {
            "vs_currency": currency,
            "order": "market_cap_desc",
            "per_page": top_n,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h,7d",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        cur_sym = {"usd": "$", "cny": "¥", "eur": "€", "jpy": "¥"}.get(currency, "")
        lines = [f"🏆 加密货币市值排行 Top {top_n} ({currency.upper()}):"]

        for i, coin in enumerate(data, 1):
            name = coin.get("name", "?")
            sym = coin.get("symbol", "?").upper()
            price = coin.get("current_price", 0)
            change_24h = coin.get("price_change_percentage_24h", 0) or 0
            change_7d = coin.get("price_change_percentage_7d_in_currency", 0) or 0
            mcap = coin.get("market_cap", 0)
            arrow = "🔺" if change_24h >= 0 else "🔻"

            price_str = f"{cur_sym}{price:,.2f}" if price >= 1 else f"{cur_sym}{price:.6f}"
            lines.append(
                f"  {i:2}. {name} ({sym}) {price_str}  "
                f"{arrow}{change_24h:+.1f}%(24h) {change_7d:+.1f}%(7d)  "
                f"市值: {cur_sym}{self._fmt_num(mcap)}"
            )
        return "\n".join(lines)

    async def _detail(self, coin_id: str, currency: str) -> str:
        """详细信息"""
        url = f"{_BASE}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        name = data.get("name", coin_id)
        sym = data.get("symbol", "?").upper()
        md = data.get("market_data", {})
        cur_sym = {"usd": "$", "cny": "¥", "eur": "€"}.get(currency, "")

        price = md.get("current_price", {}).get(currency, 0)
        mcap = md.get("market_cap", {}).get(currency, 0)
        vol24 = md.get("total_volume", {}).get(currency, 0)
        high24 = md.get("high_24h", {}).get(currency, 0)
        low24 = md.get("low_24h", {}).get(currency, 0)
        ath = md.get("ath", {}).get(currency, 0)
        circulating = md.get("circulating_supply", 0)
        total = md.get("total_supply", 0)
        chg_24h = md.get("price_change_percentage_24h", 0) or 0
        chg_7d = md.get("price_change_percentage_7d", 0) or 0
        chg_30d = md.get("price_change_percentage_30d", 0) or 0

        return (
            f"🪙 {name} ({sym}) 详细信息:\n"
            f"  当前价格: {cur_sym}{price:,.2f}\n"
            f"  24h变化: {chg_24h:+.2f}%  |  7d: {chg_7d:+.2f}%  |  30d: {chg_30d:+.2f}%\n"
            f"  24h最高/最低: {cur_sym}{high24:,.2f} / {cur_sym}{low24:,.2f}\n"
            f"  历史最高: {cur_sym}{ath:,.2f}\n"
            f"  市值: {cur_sym}{self._fmt_num(mcap)}\n"
            f"  24h交易量: {cur_sym}{self._fmt_num(vol24)}\n"
            f"  流通量: {self._fmt_num(circulating)} {sym}\n"
            f"  总供应: {self._fmt_num(total) if total else '无上限'} {sym}"
        )

    async def _trending(self) -> str:
        """热门搜索币种"""
        url = f"{_BASE}/search/trending"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        coins = data.get("coins", [])
        lines = ["🔥 当前热门加密货币:"]
        for i, item in enumerate(coins[:10], 1):
            c = item.get("item", {})
            name = c.get("name", "?")
            sym = c.get("symbol", "?")
            rank = c.get("market_cap_rank", "?")
            lines.append(f"  {i}. {name} ({sym}) — 市值排名 #{rank}")
        return "\n".join(lines)

    @staticmethod
    def _fmt_num(n: float | int) -> str:
        """格式化大数字: 1.23B, 456.7M, 12.3K"""
        if not n:
            return "0"
        n = float(n)
        if n >= 1e12:
            return f"{n/1e12:.2f}T"
        if n >= 1e9:
            return f"{n/1e9:.2f}B"
        if n >= 1e6:
            return f"{n/1e6:.2f}M"
        if n >= 1e3:
            return f"{n/1e3:.1f}K"
        return f"{n:,.2f}"
