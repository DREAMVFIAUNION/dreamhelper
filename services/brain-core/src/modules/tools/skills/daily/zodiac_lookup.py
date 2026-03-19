"""星座查询 — 根据生日查星座+性格"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

ZODIAC = [
    (1, 20, "水瓶座", "独立创新、人道主义、思维前卫"),
    (2, 19, "双鱼座", "敏感浪漫、富有同情心、直觉强"),
    (3, 21, "白羊座", "热情冲动、勇敢直率、行动力强"),
    (4, 20, "金牛座", "稳重踏实、耐心持久、重视安全感"),
    (5, 21, "双子座", "聪明灵活、善于沟通、好奇心强"),
    (6, 22, "巨蟹座", "温柔体贴、重视家庭、情感丰富"),
    (7, 23, "狮子座", "自信大方、领导力强、热情慷慨"),
    (8, 23, "处女座", "细致完美、分析力强、勤劳务实"),
    (9, 23, "天秤座", "优雅和谐、社交能力强、追求公平"),
    (10, 24, "天蝎座", "深沉专注、洞察力强、意志坚定"),
    (11, 22, "射手座", "乐观自由、爱冒险、哲学思维"),
    (12, 22, "摩羯座", "坚韧务实、自律上进、责任心强"),
]


class ZodiacSchema(SkillSchema):
    month: int = Field(description="出生月份(1-12)")
    day: int = Field(description="出生日期(1-31)")


class ZodiacLookupSkill(BaseSkill):
    name = "zodiac_lookup"
    description = "根据生日查询星座及性格特征"
    category = "daily"
    args_schema = ZodiacSchema
    tags = ["星座", "生日", "zodiac", "性格"]

    async def execute(self, **kwargs: Any) -> str:
        month = int(kwargs["month"])
        day = int(kwargs["day"])

        if not (1 <= month <= 12) or not (1 <= day <= 31):
            return "请输入有效的月份(1-12)和日期(1-31)"

        for i, (m, d, name, traits) in enumerate(ZODIAC):
            if (month == m and day >= d) or (month == (m % 12) + 1 and day < ZODIAC[(i + 1) % 12][1]):
                return f"星座查询结果:\n  生日: {month}月{day}日\n  星座: {name}\n  性格: {traits}"

        # fallback
        idx = month - 1
        _, _, name, traits = ZODIAC[idx]
        return f"星座查询结果:\n  生日: {month}月{day}日\n  星座: {name}\n  性格: {traits}"
