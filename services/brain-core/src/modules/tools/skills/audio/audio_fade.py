"""音频淡入淡出技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioFadeArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")
    fade_in_ms: int = Field(0, description="淡入时长 (毫秒)")
    fade_out_ms: int = Field(0, description="淡出时长 (毫秒)")


class AudioFadeSkill(BaseSkill):
    name = "audio_fade"
    description = "为音频添加淡入/淡出效果"
    category = "audio"
    tags = ["音频", "淡入", "淡出", "fade"]
    args_schema = AudioFadeArgs

    async def execute(self, **kwargs) -> str:
        args = AudioFadeArgs(**kwargs)
        if args.fade_in_ms <= 0 and args.fade_out_ms <= 0:
            return "请指定 fade_in_ms 或 fade_out_ms"

        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)
        total = len(audio)

        effects = []
        if args.fade_in_ms > 0:
            fi = min(args.fade_in_ms, total)
            audio = audio.fade_in(fi)
            effects.append(f"淡入 {fi}ms")
        if args.fade_out_ms > 0:
            fo = min(args.fade_out_ms, total)
            audio = audio.fade_out(fo)
            effects.append(f"淡出 {fo}ms")

        buf = io.BytesIO()
        audio.export(buf, format=args.format)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 淡入淡出完成\n"
            f"效果: {', '.join(effects)}\n"
            f"时长: {total / 1000:.1f}s\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
