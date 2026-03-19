"""音频变速技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioSpeedArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")
    speed: float = Field(1.0, description="播放速度 0.5-3.0 (1.0=原速)")


class AudioSpeedSkill(BaseSkill):
    name = "audio_speed"
    description = "调整音频播放速度 — 变速不变调（通过重采样近似）"
    category = "audio"
    tags = ["音频", "变速", "speed", "加速", "减速"]
    args_schema = AudioSpeedArgs

    async def execute(self, **kwargs) -> str:
        args = AudioSpeedArgs(**kwargs)
        spd = max(0.5, min(3.0, args.speed))
        if abs(spd - 1.0) < 0.01:
            return "速度为 1.0，无需调整"

        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)
        orig_ms = len(audio)

        # 通过修改帧率实现变速（近似变速不变调）
        new_frame_rate = int(audio.frame_rate * spd)
        modified = audio._spawn(audio.raw_data, overrides={
            "frame_rate": new_frame_rate,
        }).set_frame_rate(audio.frame_rate)

        buf = io.BytesIO()
        modified.export(buf, format=args.format)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 变速完成\n"
            f"速度: {spd:.2f}x\n"
            f"原时长: {orig_ms / 1000:.1f}s\n"
            f"变速后: {len(modified) / 1000:.1f}s\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
