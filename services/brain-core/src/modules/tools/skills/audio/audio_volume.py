"""音频音量调节技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioVolumeArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")
    gain_db: float = Field(0, description="增益 dB (正=增大, 负=减小)")
    normalize: bool = Field(False, description="是否标准化到 -1 dBFS")


class AudioVolumeSkill(BaseSkill):
    name = "audio_volume"
    description = "调节音频音量 — 增益/减弱/标准化"
    category = "audio"
    tags = ["音频", "音量", "volume", "增益", "标准化"]
    args_schema = AudioVolumeArgs

    async def execute(self, **kwargs) -> str:
        args = AudioVolumeArgs(**kwargs)
        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)

        orig_dbfs = audio.dBFS

        if args.normalize:
            target_dbfs = -1.0
            change = target_dbfs - audio.dBFS
            audio = audio.apply_gain(change)
            method = f"标准化到 {target_dbfs} dBFS (变化 {change:+.1f} dB)"
        else:
            audio = audio.apply_gain(args.gain_db)
            method = f"增益 {args.gain_db:+.1f} dB"

        buf = io.BytesIO()
        audio.export(buf, format=args.format)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 音量调节完成\n"
            f"方式: {method}\n"
            f"原始音量: {orig_dbfs:.1f} dBFS\n"
            f"调整后: {audio.dBFS:.1f} dBFS\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
