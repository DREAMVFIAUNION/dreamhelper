"""摩尔斯电码 — 编码/解码"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

MORSE_MAP = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/', '.': '.-.-.-', ',': '--..--',
    '?': '..--..', '!': '-.-.--', '@': '.--.-.', '&': '.-...',
}

REVERSE_MAP = {v: k for k, v in MORSE_MAP.items()}


class MorseSchema(SkillSchema):
    text: str = Field(description="要编码的文本，或要解码的摩尔斯电码(用空格分隔)")
    mode: str = Field(default="auto", description="encode=编码, decode=解码, auto=自动判断")


class MorseCodeSkill(BaseSkill):
    name = "morse_code"
    description = "摩尔斯电码编码与解码"
    category = "daily"
    args_schema = MorseSchema
    tags = ["摩尔斯", "morse", "编码", "解码"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"].strip()
        mode = kwargs.get("mode", "auto")

        if mode == "auto":
            mode = "decode" if all(c in '.-/ ' for c in text) and ('.' in text or '-' in text) else "encode"

        if mode == "encode":
            result = []
            for ch in text.upper():
                if ch in MORSE_MAP:
                    result.append(MORSE_MAP[ch])
                else:
                    result.append('?')
            return f"摩尔斯编码:\n{text}\n→ {' '.join(result)}"
        else:
            parts = text.split(' ')
            decoded = []
            for p in parts:
                if p in REVERSE_MAP:
                    decoded.append(REVERSE_MAP[p])
                elif p == '/':
                    decoded.append(' ')
                elif p == '':
                    continue
                else:
                    decoded.append('?')
            return f"摩尔斯解码:\n{text}\n→ {''.join(decoded)}"
