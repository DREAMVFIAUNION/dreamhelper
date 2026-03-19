"""ASCII 艺术 — 文字转 ASCII 艺术字"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

# 简单的 5x5 字母表 (大写)
FONT = {
    'A': ["  #  ", " # # ", "#####", "#   #", "#   #"],
    'B': ["#### ", "#   #", "#### ", "#   #", "#### "],
    'C': [" ####", "#    ", "#    ", "#    ", " ####"],
    'D': ["#### ", "#   #", "#   #", "#   #", "#### "],
    'E': ["#####", "#    ", "###  ", "#    ", "#####"],
    'F': ["#####", "#    ", "###  ", "#    ", "#    "],
    'G': [" ####", "#    ", "# ###", "#   #", " ### "],
    'H': ["#   #", "#   #", "#####", "#   #", "#   #"],
    'I': ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    'J': ["#####", "    #", "    #", "#   #", " ### "],
    'K': ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    'L': ["#    ", "#    ", "#    ", "#    ", "#####"],
    'M': ["#   #", "## ##", "# # #", "#   #", "#   #"],
    'N': ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    'O': [" ### ", "#   #", "#   #", "#   #", " ### "],
    'P': ["#### ", "#   #", "#### ", "#    ", "#    "],
    'Q': [" ### ", "#   #", "# # #", "#  # ", " ## #"],
    'R': ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    'S': [" ####", "#    ", " ### ", "    #", "#### "],
    'T': ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    'U': ["#   #", "#   #", "#   #", "#   #", " ### "],
    'V': ["#   #", "#   #", " # # ", " # # ", "  #  "],
    'W': ["#   #", "#   #", "# # #", "## ##", "#   #"],
    'X': ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    'Y': ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    'Z': ["#####", "   # ", "  #  ", " #   ", "#####"],
    ' ': ["     ", "     ", "     ", "     ", "     "],
    '!': ["  #  ", "  #  ", "  #  ", "     ", "  #  "],
    '0': [" ### ", "#   #", "#   #", "#   #", " ### "],
    '1': ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
}


class AsciiSchema(SkillSchema):
    text: str = Field(description="要转换的文本(英文字母+数字)")
    char: str = Field(default="#", description="填充字符(默认#)")


class AsciiArtSkill(BaseSkill):
    name = "ascii_art"
    description = "将文字转换为 ASCII 艺术字"
    category = "entertainment"
    args_schema = AsciiSchema
    tags = ["ASCII", "艺术", "字体", "art"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"].upper()[:20]
        char = kwargs.get("char", "#")[0] if kwargs.get("char") else "#"

        lines = ["", "", "", "", ""]
        for c in text:
            glyph = FONT.get(c, FONT.get(' ', ["     "] * 5))
            for i in range(5):
                row = glyph[i] if i < len(glyph) else "     "
                lines[i] += row.replace("#", char) + " "

        result = "\n".join(lines)
        return f"ASCII Art:\n{result}"
