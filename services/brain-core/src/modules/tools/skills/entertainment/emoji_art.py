"""Emoji 艺术 — Emoji 组合画"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

TEMPLATES = {
    "heart": [
        " 💗💗  💗💗 ",
        "💗💗💗💗💗💗💗",
        "💗💗💗💗💗💗💗",
        " 💗💗💗💗💗 ",
        "  💗💗💗  ",
        "   💗💗   ",
        "    💗    ",
    ],
    "star": [
        "    ⭐    ",
        "   ⭐⭐   ",
        "⭐⭐⭐⭐⭐⭐⭐",
        " ⭐⭐⭐⭐⭐ ",
        "  ⭐⭐⭐  ",
        " ⭐  ⭐  ⭐",
    ],
    "cat": [
        " 😺😺   😺😺 ",
        "😺😺😺😺😺😺😺😺",
        "😺⬛😺😺😺⬛😺",
        "😺😺😺🔴😺😺😺",
        "😺😺😺😺😺😺😺😺",
        " 😺😺😺😺😺😺 ",
    ],
    "tree": [
        "     🌟     ",
        "    🎄🎄    ",
        "   🎄🎄🎄   ",
        "  🎄🎄🎄🎄  ",
        " 🎄🎄🎄🎄🎄 ",
        "🎄🎄🎄🎄🎄🎄",
        "    🪵🪵    ",
    ],
    "rocket": [
        "    🔺    ",
        "   🚀🚀   ",
        "  🚀🚀🚀  ",
        "   🚀🚀   ",
        "  🔥🔥🔥  ",
        " 🔥🔥🔥🔥 ",
    ],
}


class EmojiSchema(SkillSchema):
    template: str = Field(default="heart", description=f"模板: {', '.join(TEMPLATES.keys())}")


class EmojiArtSkill(BaseSkill):
    name = "emoji_art"
    description = "Emoji 组合画: 爱心、星星、猫咪、圣诞树、火箭"
    category = "entertainment"
    args_schema = EmojiSchema
    tags = ["emoji", "艺术", "画", "表情"]

    async def execute(self, **kwargs: Any) -> str:
        tpl = kwargs.get("template", "heart").lower()
        if tpl not in TEMPLATES:
            return f"可用模板: {', '.join(TEMPLATES.keys())}"

        art = "\n".join(TEMPLATES[tpl])
        return f"Emoji Art [{tpl}]:\n\n{art}"
