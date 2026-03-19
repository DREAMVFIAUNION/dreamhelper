"""音频反转技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioReverseArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")


class AudioReverseSkill(BaseSkill):
    name = "audio_reverse"
    description = "反转音频 — 倒放播放"
    category = "audio"
    tags = ["音频", "反转", "reverse", "倒放"]
    args_schema = AudioReverseArgs

    async def execute(self, **kwargs) -> str:
        args = AudioReverseArgs(**kwargs)
        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)

        reversed_audio = audio.reverse()

        buf = io.BytesIO()
        reversed_audio.export(buf, format=args.format)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 音频反转完成\n"
            f"时长: {len(audio) / 1000:.1f}s\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
