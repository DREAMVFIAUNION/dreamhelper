"""世界模型 (WorldModel) — 感知外部世界

通过实时数据工具获取:
- 当前时间 & 日期
- 天气状况
- 科技/AI 新闻热点
- 股市/加密货币概况
- 用户项目状态 (基于记忆系统)

每小时自动观察一次 (Scheduler 调用)
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("consciousness.world_model")


@dataclass
class WorldState:
    """世界状态快照"""
    current_time: str = ""
    day_of_week: str = ""
    weather_summary: str = ""
    tech_headlines: list[str] = field(default_factory=list)
    ai_headlines: list[str] = field(default_factory=list)
    market_summary: str = ""
    crypto_summary: str = ""
    last_observed: float = 0.0


@dataclass
class UserContext:
    """用户情境"""
    user_id: str = ""
    recent_topics: list[str] = field(default_factory=list)
    mood_estimate: str = "neutral"
    last_interaction: float = 0.0
    interaction_count: int = 0


class WorldModel:
    """世界模型 — 感知外部世界"""

    def __init__(self, weather_city: str = "深圳"):
        self.world_state = WorldState()
        self.user_contexts: dict[str, UserContext] = {}
        self._weather_city = weather_city

    async def observe(self):
        """定时观察世界 — Scheduler 每小时调用"""
        logger.info("[WorldModel] Observing the world...")
        from ..tools.tool_registry import ToolRegistry

        # 1. 时间感知
        try:
            dt_tool = ToolRegistry.get("datetime")
            if dt_tool:
                result = await dt_tool.execute(action="now")
                self.world_state.current_time = result
                # 也获取全球时间概览
                world_result = await dt_tool.execute(
                    action="world",
                    cities="北京,东京,纽约,伦敦"
                )
                self.world_state.day_of_week = world_result.split("\n")[0] if world_result else ""
        except Exception as e:
            logger.warning("[WorldModel] Time observation failed: %s", e)

        # 2. 天气感知
        try:
            weather_tool = ToolRegistry.get("weather")
            if weather_tool:
                result = await weather_tool.execute(action="current", city=self._weather_city)
                self.world_state.weather_summary = result
        except Exception as e:
            logger.warning("[WorldModel] Weather observation failed: %s", e)

        # 3. 科技新闻
        try:
            news_tool = ToolRegistry.get("news")
            if news_tool:
                tech_result = await news_tool.execute(action="headlines", category="tech", max_results=3)
                self.world_state.tech_headlines = self._extract_headlines(tech_result)
                ai_result = await news_tool.execute(action="headlines", category="ai", max_results=3)
                self.world_state.ai_headlines = self._extract_headlines(ai_result)
        except Exception as e:
            logger.warning("[WorldModel] News observation failed: %s", e)

        # 4. 市场概况
        try:
            stock_tool = ToolRegistry.get("stock")
            if stock_tool:
                # 仅查几个关键指数
                result = await stock_tool.execute(
                    action="quote",
                    symbols="^GSPC,^IXIC,000001.SS"
                )
                self.world_state.market_summary = result
        except Exception as e:
            logger.warning("[WorldModel] Stock observation failed: %s", e)

        # 5. 加密货币
        try:
            crypto_tool = ToolRegistry.get("crypto")
            if crypto_tool:
                result = await crypto_tool.execute(
                    action="price",
                    coins="bitcoin,ethereum,solana",
                    currency="usd"
                )
                self.world_state.crypto_summary = result
        except Exception as e:
            logger.warning("[WorldModel] Crypto observation failed: %s", e)

        self.world_state.last_observed = time.time()
        logger.info("[WorldModel] World observation complete")

    async def observe_user(self, user_id: str, message: str):
        """每次用户消息时更新用户情境"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(user_id=user_id)

        ctx = self.user_contexts[user_id]
        ctx.last_interaction = time.time()
        ctx.interaction_count += 1

        # 简单话题提取 (取消息前50字)
        topic = message[:50].strip()
        if topic:
            ctx.recent_topics.append(topic)
            ctx.recent_topics = ctx.recent_topics[-10:]  # 保留最近10个

        # 简单情绪估计
        positive = ["谢谢", "太好了", "厉害", "不错", "赞", "感谢", "哈哈", "😄", "👍"]
        negative = ["不行", "错了", "问题", "失败", "bug", "烦", "😔", "😡"]
        lower = message.lower()
        if any(w in lower for w in positive):
            ctx.mood_estimate = "positive"
        elif any(w in lower for w in negative):
            ctx.mood_estimate = "negative"
        else:
            ctx.mood_estimate = "neutral"

    def get_world_context(self, user_id: str = "") -> str:
        """生成世界感知 prompt 片段"""
        ws = self.world_state
        if ws.last_observed == 0:
            return ""

        parts = ["## 世界感知"]

        if ws.current_time:
            parts.append(f"时间: {ws.current_time}")

        if ws.weather_summary:
            # 取天气摘要的前几行
            weather_lines = ws.weather_summary.split("\n")[:4]
            parts.append("天气: " + " | ".join(l.strip() for l in weather_lines if l.strip()))

        if ws.tech_headlines:
            parts.append("科技热点: " + " | ".join(ws.tech_headlines[:3]))

        if ws.ai_headlines:
            parts.append("AI动态: " + " | ".join(ws.ai_headlines[:2]))

        if ws.market_summary:
            # 精简市场信息
            market_lines = [l.strip() for l in ws.market_summary.split("\n") if "价格:" in l or "🔺" in l or "🔻" in l]
            if market_lines:
                parts.append("市场: " + " | ".join(market_lines[:3]))

        if ws.crypto_summary:
            crypto_lines = [l.strip() for l in ws.crypto_summary.split("\n") if ":" in l and ("$" in l or "¥" in l)]
            if crypto_lines:
                parts.append("加密货币: " + " | ".join(crypto_lines[:3]))

        # 用户情境
        if user_id and user_id in self.user_contexts:
            ctx = self.user_contexts[user_id]
            if ctx.recent_topics:
                parts.append(f"用户近期话题: {', '.join(ctx.recent_topics[-3:])}")
            if ctx.mood_estimate != "neutral":
                parts.append(f"用户情绪估计: {ctx.mood_estimate}")

        return "\n".join(parts)

    def get_user_context(self, user_id: str) -> Optional[UserContext]:
        return self.user_contexts.get(user_id)

    def _extract_headlines(self, news_text: str) -> list[str]:
        """从新闻工具输出中提取标题"""
        headlines = []
        for line in news_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:3]:
                # "1. [Source] Title"
                parts = line.split("]", 1)
                if len(parts) == 2:
                    headlines.append(parts[1].strip()[:80])
                else:
                    headlines.append(line[3:].strip()[:80])
        return headlines

    def get_stats(self) -> dict:
        return {
            "last_observed": self.world_state.last_observed,
            "tracked_users": len(self.user_contexts),
            "has_weather": bool(self.world_state.weather_summary),
            "has_news": bool(self.world_state.tech_headlines),
            "has_market": bool(self.world_state.market_summary),
            "has_crypto": bool(self.world_state.crypto_summary),
        }
