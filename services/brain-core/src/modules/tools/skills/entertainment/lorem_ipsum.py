"""假文生成器 — 中英文 Lorem Ipsum"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random

EN_WORDS = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure in reprehenderit voluptate velit esse cillum fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum".split()

CN_PHRASES = [
    "天地玄黄", "宇宙洪荒", "日月盈昃", "辰宿列张", "寒来暑往", "秋收冬藏",
    "闰余成岁", "律吕调阳", "云腾致雨", "露结为霜", "金生丽水", "玉出昆冈",
    "剑号巨阙", "珠称夜光", "果珍李柰", "菜重芥姜", "海咸河淡", "鳞潜羽翔",
    "龙师火帝", "鸟官人皇", "始制文字", "乃服衣裳", "推位让国", "有虞陶唐",
    "科技创新", "数据驱动", "人工智能", "深度学习", "云端计算", "边缘算力",
    "微服务架构", "容器编排", "持续集成", "敏捷开发", "代码审查", "自动化测试",
]


class LoremSchema(SkillSchema):
    lang: str = Field(default="en", description="语言: en(英文)/cn(中文)")
    paragraphs: int = Field(default=3, description="段落数(1-10)")
    words_per: int = Field(default=50, description="每段词数(英文)或字数(中文)")


class LoremIpsumSkill(BaseSkill):
    name = "lorem_ipsum"
    description = "生成中英文假文/占位文本"
    category = "entertainment"
    args_schema = LoremSchema
    tags = ["假文", "Lorem", "占位", "文本生成"]

    async def execute(self, **kwargs: Any) -> str:
        lang = kwargs.get("lang", "en")
        paras = min(10, max(1, int(kwargs.get("paragraphs", 3))))
        wpp = min(200, max(10, int(kwargs.get("words_per", 50))))

        result = []
        for _ in range(paras):
            if lang == "cn":
                phrases = [random.choice(CN_PHRASES) for _ in range(wpp // 4 + 1)]
                text = "，".join(phrases[:wpp // 4]) + "。"
                result.append(text)
            else:
                words = [random.choice(EN_WORDS) for _ in range(wpp)]
                words[0] = words[0].capitalize()
                # 加句号
                text = ""
                for i, w in enumerate(words):
                    if i > 0 and i % random.randint(8, 15) == 0:
                        text += ". " + w.capitalize()
                    else:
                        text += " " + w if text else w
                text += "."
                result.append(text)

        output = "\n\n".join(result)
        label = "中文" if lang == "cn" else "英文"
        return f"{label}假文 ({paras} 段):\n\n{output}"
