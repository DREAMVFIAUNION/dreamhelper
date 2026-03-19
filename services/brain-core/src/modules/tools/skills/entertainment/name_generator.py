"""随机名字生成器 — 中英文名/网名"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random

CN_SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
CN_NAMES = "伟芳娜秀英敏静丽强磊军洋勇艳杰娟涛超明华雪慧婷飞博宇欣怡瑶璐晨"
CN_DOUBLE = ["志远", "思源", "雨晨", "文博", "晓峰", "子涵", "梦琪", "诗雨", "若曦", "天宇",
             "浩然", "一鸣", "嘉欣", "雅琴", "明哲", "宇航", "心怡", "语嫣", "子墨", "逸飞"]

EN_FIRST = ["James", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "Oliver", "Isabella",
            "Lucas", "Mia", "Mason", "Charlotte", "Ethan", "Amelia", "Alex", "Harper", "Daniel", "Evelyn"]
EN_LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Anderson",
           "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Harris", "Clark", "Lewis", "Young"]

NICK_PREFIX = ["暗夜", "星辰", "影子", "极光", "量子", "赛博", "数码", "幻影", "深空", "烈焰"]
NICK_SUFFIX = ["猎人", "行者", "骑士", "法师", "旅人", "守望者", "探索者", "漫步者", "追光者", "破晓"]


class NameSchema(SkillSchema):
    type: str = Field(default="cn", description="类型: cn(中文名)/en(英文名)/nick(网名)")
    count: int = Field(default=5, description="生成数量(1-20)")


class NameGeneratorSkill(BaseSkill):
    name = "name_generator"
    description = "随机名字生成: 中文名、英文名、网名"
    category = "entertainment"
    args_schema = NameSchema
    tags = ["名字", "随机", "生成", "name"]

    async def execute(self, **kwargs: Any) -> str:
        typ = kwargs.get("type", "cn")
        count = min(20, max(1, int(kwargs.get("count", 5))))
        names = []

        for _ in range(count):
            if typ == "cn":
                surname = random.choice(CN_SURNAMES)
                if random.random() > 0.4:
                    name = random.choice(CN_DOUBLE)
                else:
                    name = random.choice(CN_NAMES)
                names.append(surname + name)
            elif typ == "en":
                names.append(f"{random.choice(EN_FIRST)} {random.choice(EN_LAST)}")
            else:
                names.append(f"{random.choice(NICK_PREFIX)}{random.choice(NICK_SUFFIX)}")

        label = {"cn": "中文名", "en": "英文名", "nick": "网名"}.get(typ, typ)
        return f"随机{label} ({count} 个):\n" + "\n".join(f"  {i+1}. {n}" for i, n in enumerate(names))
