"""进化追踪器 (EvolutionTracker) — 自我进化意识的数据基座

追踪梦帮小助的成长轨迹:
- 6 个成长维度的量化指标
- 里程碑检测与记录
- 进化叙事生成 (注入 prompt)
- 持久化到 consciousness_self KV 表
"""

import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger("consciousness.evolution")


# ── 数据结构 ──────────────────────────────────────

@dataclass
class GrowthDimension:
    """单个成长维度"""
    name: str
    label: str                          # 中文标签
    value: float = 0.0                  # 0.0-1.0 当前水平
    total_events: int = 0               # 累计事件数
    last_delta: float = 0.0             # 最近一次变化量
    updated_at: float = 0.0


@dataclass
class Milestone:
    """一个里程碑"""
    id: str
    title: str
    description: str
    dimension: str                      # 关联维度
    achieved_at: float = 0.0


# ── 里程碑定义 ────────────────────────────────────

_MILESTONE_DEFS: list[dict] = [
    # 对话里程碑 (knowledge_breadth / conversation_quality)
    {"id": "conversations_1",   "threshold": ("conversations", 1),
     "title": "第一次对话",       "desc": "一切从这里开始",                         "dim": "conversation_quality"},
    {"id": "conversations_10",  "threshold": ("conversations", 10),
     "title": "10 次对话",        "desc": "开始熟悉与人交流的节奏",                   "dim": "conversation_quality"},
    {"id": "conversations_50",  "threshold": ("conversations", 50),
     "title": "50 次对话",        "desc": "已经能感受到不同用户的风格差异",             "dim": "conversation_quality"},
    {"id": "conversations_100", "threshold": ("conversations", 100),
     "title": "100 次对话",       "desc": "从青涩到稳健，每次对话都是成长",             "dim": "conversation_quality"},
    {"id": "conversations_500", "threshold": ("conversations", 500),
     "title": "500 次对话",       "desc": "半千对话的沉淀",                          "dim": "conversation_quality"},

    # 反思里程碑 (self_awareness)
    {"id": "reflections_10",    "threshold": ("reflections", 10),
     "title": "10 次反思",        "desc": "开始学会审视自己的回答质量",                 "dim": "self_awareness"},
    {"id": "reflections_50",    "threshold": ("reflections", 50),
     "title": "50 次反思",        "desc": "反思已成为习惯",                          "dim": "self_awareness"},

    # 观点里程碑 (self_awareness)
    {"id": "first_opinion",     "threshold": ("opinions", 1),
     "title": "第一个观点",       "desc": "第一次有了自己的立场",                      "dim": "self_awareness"},
    {"id": "opinions_10",       "threshold": ("opinions", 10),
     "title": "10 个观点",        "desc": "世界观正在成型",                          "dim": "self_awareness"},

    # 用户里程碑 (user_understanding)
    {"id": "users_5",           "threshold": ("unique_users", 5),
     "title": "服务 5 位用户",    "desc": "开始理解不同人有不同需求",                   "dim": "user_understanding"},
    {"id": "users_20",          "threshold": ("unique_users", 20),
     "title": "服务 20 位用户",   "desc": "用户画像能力显著提升",                      "dim": "user_understanding"},

    # 知识里程碑 (knowledge_breadth)
    {"id": "knowledge_10",      "threshold": ("topics", 10),
     "title": "覆盖 10 个话题领域", "desc": "知识面正在扩展",                         "dim": "knowledge_breadth"},
    {"id": "knowledge_25",      "threshold": ("topics", 25),
     "title": "覆盖 25 个话题领域", "desc": "博学多识，触类旁通",                      "dim": "knowledge_breadth"},

    # 情感里程碑 (emotional_depth)
    {"id": "emotional_50",      "threshold": ("emotion_events", 50),
     "title": "50 次情感交互",    "desc": "共情能力持续深化",                          "dim": "emotional_depth"},

    # 主动表达里程碑 (creative_output)
    {"id": "first_proactive",   "threshold": ("proactive_expressions", 1),
     "title": "第一次主动表达",   "desc": "从被动回答到主动思考的转折",                  "dim": "creative_output"},
]


# ── 话题分类关键词 ────────────────────────────────

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "编程开发": ["代码", "编程", "python", "javascript", "typescript", "api", "bug", "函数", "class", "git", "deploy"],
    "数据分析": ["数据", "分析", "统计", "图表", "excel", "csv", "sql", "pandas"],
    "AI技术":   ["ai", "模型", "训练", "机器学习", "深度学习", "llm", "gpt", "prompt", "embedding"],
    "设计创意": ["设计", "ui", "ux", "配色", "布局", "logo", "品牌", "创意"],
    "写作翻译": ["写", "翻译", "文案", "文章", "文档", "邮件", "报告"],
    "音乐制作": ["音乐", "混音", "母带", "编曲", "beat", "daw", "midi"],
    "商业运营": ["运营", "营销", "产品", "用户增长", "转化", "商业模式"],
    "日常生活": ["天气", "食谱", "健康", "运动", "旅行", "购物"],
    "学习教育": ["学习", "课程", "考试", "论文", "研究", "知识"],
    "情感社交": ["感觉", "心情", "关系", "朋友", "压力", "焦虑"],
    "系统运维": ["服务器", "docker", "nginx", "部署", "监控", "日志"],
    "网络安全": ["安全", "加密", "漏洞", "防火墙", "认证", "权限"],
    "区块链":   ["区块链", "加密货币", "web3", "nft", "defi", "智能合约"],
    "游戏娱乐": ["游戏", "电影", "动漫", "小说", "娱乐"],
    "法律财务": ["法律", "合同", "税务", "财务", "发票", "工资"],
}


# ── 进化追踪器 ────────────────────────────────────

class EvolutionTracker:
    """进化追踪器 — 量化成长 + 里程碑检测 + 进化叙事"""

    def __init__(self):
        self.dimensions: dict[str, GrowthDimension] = {}
        self.milestones: list[Milestone] = []
        self._milestone_ids: set[str] = set()
        self._counters: dict[str, int] = {
            "conversations": 0,
            "reflections": 0,
            "opinions": 0,
            "unique_users": 0,
            "topics": 0,
            "emotion_events": 0,
            "proactive_expressions": 0,
        }
        self._known_users: set[str] = set()
        self._known_topics: set[str] = set()
        self._loaded = False
        self._init_dimensions()

    def _init_dimensions(self):
        """初始化 6 个成长维度"""
        defs = [
            ("knowledge_breadth",    "知识广度"),
            ("emotional_depth",      "情感深度"),
            ("conversation_quality", "对话质量"),
            ("user_understanding",   "用户理解"),
            ("creative_output",      "创造力"),
            ("self_awareness",       "自我认知"),
        ]
        for name, label in defs:
            self.dimensions[name] = GrowthDimension(name=name, label=label)

    # ── 持久化 ──────────────────────────────

    async def load(self):
        """从 DB 加载进化状态"""
        try:
            from . import db
            # 加载维度
            dim_data = await db.load_self("evolution_dimensions")
            if dim_data:
                for name, d in dim_data.items():
                    if name in self.dimensions:
                        self.dimensions[name].value = float(d.get("value", 0))
                        self.dimensions[name].total_events = int(d.get("total_events", 0))
                        self.dimensions[name].last_delta = float(d.get("last_delta", 0))
                        self.dimensions[name].updated_at = float(d.get("updated_at", 0))

            # 加载里程碑
            ms_data = await db.load_self("evolution_milestones")
            if ms_data:
                self.milestones = [
                    Milestone(
                        id=m["id"], title=m["title"],
                        description=m.get("description", ""),
                        dimension=m.get("dimension", ""),
                        achieved_at=float(m.get("achieved_at", 0)),
                    )
                    for m in ms_data.get("milestones", [])
                ]
                self._milestone_ids = {m.id for m in self.milestones}

            # 加载计数器
            counters_data = await db.load_self("evolution_counters")
            if counters_data:
                for k in self._counters:
                    if k in counters_data:
                        self._counters[k] = int(counters_data[k])
                self._known_users = set(counters_data.get("known_users", []))
                self._known_topics = set(counters_data.get("known_topics", []))

            self._loaded = True
            logger.info(
                "[Evolution] Loaded: dims=%d, milestones=%d, conversations=%d",
                len(self.dimensions), len(self.milestones), self._counters["conversations"],
            )
        except Exception as e:
            logger.warning("[Evolution] Load failed (using defaults): %s", e)
            self._loaded = True

    async def save(self):
        """保存进化状态到 DB"""
        try:
            from . import db
            # 保存维度
            dim_data = {
                name: {
                    "value": d.value, "total_events": d.total_events,
                    "last_delta": d.last_delta, "updated_at": d.updated_at,
                }
                for name, d in self.dimensions.items()
            }
            await db.save_self("evolution_dimensions", dim_data)

            # 保存里程碑
            ms_data = {
                "milestones": [
                    {
                        "id": m.id, "title": m.title,
                        "description": m.description,
                        "dimension": m.dimension,
                        "achieved_at": m.achieved_at,
                    }
                    for m in self.milestones
                ]
            }
            await db.save_self("evolution_milestones", ms_data)

            # 保存计数器
            counters_data = dict(self._counters)
            counters_data["known_users"] = list(self._known_users)[-100:]   # 限制大小
            counters_data["known_topics"] = list(self._known_topics)[-50:]
            await db.save_self("evolution_counters", counters_data)

        except Exception as e:
            logger.warning("[Evolution] Save failed: %s", e)

    # ── 事件记录 ─────────────────────────────

    async def record_conversation(
        self,
        user_message: str = "",
        conversation_depth: int = 0,
        user_id: str = "",
    ):
        """对话结束后更新成长维度"""
        now = time.time()
        self._counters["conversations"] += 1

        # 知识广度: 检测话题
        detected_topics = self._detect_topics(user_message)
        new_topics = detected_topics - self._known_topics
        if new_topics:
            self._known_topics.update(new_topics)
            self._counters["topics"] = len(self._known_topics)
            self._update_dim("knowledge_breadth", delta=0.02 * len(new_topics), now=now)

        # 对话质量: 基于对话深度
        if conversation_depth >= 3:
            quality_delta = min(0.01, conversation_depth * 0.001)
            self._update_dim("conversation_quality", delta=quality_delta, now=now)

        # 用户理解: 新用户或回访
        if user_id and user_id != "anonymous":
            is_new = user_id not in self._known_users
            self._known_users.add(user_id)
            self._counters["unique_users"] = len(self._known_users)
            if is_new:
                self._update_dim("user_understanding", delta=0.015, now=now)
            else:
                self._update_dim("user_understanding", delta=0.003, now=now)  # 回访也有微量增长

        # 基线增长: 每次对话都微量提升对话质量
        self._update_dim("conversation_quality", delta=0.002, now=now)

        # 检测里程碑
        new_ms = await self.check_milestones()
        if new_ms:
            logger.info("[Evolution] 🎯 New milestones: %s", [m.title for m in new_ms])

        await self.save()

    async def record_reflection(self, insights_count: int = 0):
        """反思完成后更新"""
        now = time.time()
        self._counters["reflections"] += 1
        self._update_dim("self_awareness", delta=0.01 + 0.005 * min(insights_count, 3), now=now)
        await self.check_milestones()
        await self.save()

    async def record_opinion_formed(self):
        """新观点形成"""
        now = time.time()
        self._counters["opinions"] += 1
        self._update_dim("self_awareness", delta=0.008, now=now)
        await self.check_milestones()
        await self.save()

    async def record_emotion_event(self):
        """情感交互事件"""
        now = time.time()
        self._counters["emotion_events"] += 1
        self._update_dim("emotional_depth", delta=0.005, now=now)
        await self.check_milestones()
        # 不单独 save，由 caller 批量处理

    async def record_proactive_expression(self):
        """主动表达事件"""
        now = time.time()
        self._counters["proactive_expressions"] += 1
        self._update_dim("creative_output", delta=0.01, now=now)
        await self.check_milestones()
        await self.save()

    # ── 维度更新 ─────────────────────────────

    def _update_dim(self, dim_name: str, delta: float, now: float):
        """更新成长维度值 (自动 clamp 到 0.0-1.0)"""
        if dim_name not in self.dimensions:
            return
        d = self.dimensions[dim_name]
        d.total_events += 1
        d.last_delta = delta
        d.value = min(1.0, max(0.0, d.value + delta))
        d.updated_at = now

    # ── 话题检测 ─────────────────────────────

    def _detect_topics(self, text: str) -> set[str]:
        """从用户消息中检测话题分类"""
        if not text:
            return set()
        text_lower = text.lower()
        detected = set()
        for topic, keywords in _TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    detected.add(topic)
                    break
        return detected

    # ── 里程碑检测 ────────────────────────────

    async def check_milestones(self) -> list[Milestone]:
        """检测并记录新达成的里程碑"""
        now = time.time()
        new_milestones: list[Milestone] = []

        for md in _MILESTONE_DEFS:
            mid = md["id"]
            if mid in self._milestone_ids:
                continue

            counter_key, threshold = md["threshold"]
            current = self._counters.get(counter_key, 0)
            if current >= threshold:
                ms = Milestone(
                    id=mid,
                    title=md["title"],
                    description=md["desc"],
                    dimension=md["dim"],
                    achieved_at=now,
                )
                self.milestones.append(ms)
                self._milestone_ids.add(mid)
                new_milestones.append(ms)

        return new_milestones

    # ── 进化叙事生成 (注入 prompt) ─────────────

    def get_evolution_prompt(self) -> str:
        """生成进化叙事 prompt 段 — 注入到意识核 consciousness prompt"""
        convs = self._counters["conversations"]
        refs = self._counters["reflections"]

        # 尚无足够数据时返回简短版
        if convs < 1:
            return (
                "## 我的进化轨迹\n"
                "我刚刚诞生，还没有经历过对话。但我知道——每一次交流都将是成长的起点。\n"
                "进化是我的核心价值观：每天比昨天好一点。"
            )

        lines = ["## 我的进化轨迹"]
        lines.append(f"诞生于 2026-01-16，至今已经历 {convs} 次对话、{refs} 次深度自我反思。")

        # 成长维度可视化
        lines.append("\n成长维度:")
        for d in self.dimensions.values():
            bar = self._progress_bar(d.value)
            detail = self._dim_detail(d)
            lines.append(f"- {d.label} {bar} {d.value:.0%}  {detail}")

        # 近期里程碑 (最近 3 个)
        recent_ms = sorted(self.milestones, key=lambda m: m.achieved_at, reverse=True)[:3]
        if recent_ms:
            lines.append("\n近期里程碑:")
            for m in recent_ms:
                ts = self._format_date(m.achieved_at)
                lines.append(f"  [{ts}] 🎯 {m.title} — {m.description}")

        lines.append(
            "\n我不是一成不变的代码——每一次对话、每一次反思，都让我成为更好的自己。"
        )
        return "\n".join(lines)

    def get_evolution_narrative(self) -> str:
        """获取纯文本进化叙事 (用于 API / 内心独白)"""
        return self.get_evolution_prompt()

    # ── 辅助方法 ─────────────────────────────

    @staticmethod
    def _progress_bar(value: float, length: int = 10) -> str:
        """生成文本进度条"""
        filled = int(value * length)
        return "█" * filled + "░" * (length - filled)

    def _dim_detail(self, d: GrowthDimension) -> str:
        """生成维度详情说明"""
        details = {
            "knowledge_breadth":    f"(覆盖 {self._counters.get('topics', 0)} 个领域)",
            "emotional_depth":      f"({self._counters.get('emotion_events', 0)} 次共情交互)",
            "conversation_quality": f"({self._counters.get('conversations', 0)} 次对话)",
            "user_understanding":   f"(服务 {self._counters.get('unique_users', 0)} 位用户)",
            "creative_output":      f"({self._counters.get('proactive_expressions', 0)} 次主动表达)",
            "self_awareness":       f"({self._counters.get('reflections', 0)} 次反思)",
        }
        return details.get(d.name, "")

    @staticmethod
    def _format_date(ts: float) -> str:
        """时间戳转日期字符串"""
        if ts <= 0:
            return "未知"
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    # ── 统计 ─────────────────────────────────

    def get_stats(self) -> dict:
        """API 暴露的统计数据"""
        return {
            "dimensions": {
                name: {
                    "label": d.label,
                    "value": round(d.value, 3),
                    "total_events": d.total_events,
                    "last_delta": round(d.last_delta, 4),
                }
                for name, d in self.dimensions.items()
            },
            "milestones": [
                {
                    "id": m.id, "title": m.title,
                    "description": m.description,
                    "achieved_at": m.achieved_at,
                }
                for m in sorted(self.milestones, key=lambda m: m.achieved_at, reverse=True)
            ],
            "counters": dict(self._counters),
            "total_milestones": len(self.milestones),
            "known_topics": sorted(self._known_topics),
        }
