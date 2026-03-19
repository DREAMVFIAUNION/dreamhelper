"""音频技能测试"""

import asyncio
import base64
import io
import struct
import pytest


def _make_test_wav(duration_ms=500, sample_rate=44100) -> str:
    """生成一个简单的 WAV 测试文件 (纯正弦波)"""
    import math
    n_samples = int(sample_rate * duration_ms / 1000)
    freq = 440.0  # A4
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        val = int(32767 * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack('<h', val))

    raw = b''.join(samples)
    buf = io.BytesIO()
    # WAV header
    buf.write(b'RIFF')
    data_size = len(raw)
    buf.write(struct.pack('<I', 36 + data_size))
    buf.write(b'WAVE')
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16))  # chunk size
    buf.write(struct.pack('<H', 1))   # PCM
    buf.write(struct.pack('<H', 1))   # mono
    buf.write(struct.pack('<I', sample_rate))
    buf.write(struct.pack('<I', sample_rate * 2))  # byte rate
    buf.write(struct.pack('<H', 2))   # block align
    buf.write(struct.pack('<H', 16))  # bits per sample
    buf.write(b'data')
    buf.write(struct.pack('<I', data_size))
    buf.write(raw)
    return base64.b64encode(buf.getvalue()).decode()


TEST_WAV = None

def get_test_wav():
    global TEST_WAV
    if TEST_WAV is None:
        TEST_WAV = _make_test_wav()
    return TEST_WAV


class TestAudioInfo:
    def test_basic_info(self):
        from src.modules.tools.skills.audio.audio_info import AudioInfoSkill
        skill = AudioInfoSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(audio_b64=get_test_wav(), format="wav")
        )
        assert "音频信息" in result
        assert "44100" in result
        assert "单声道" in result


class TestAudioTrim:
    def test_trim(self):
        from src.modules.tools.skills.audio.audio_trim import AudioTrimSkill
        skill = AudioTrimSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(audio_b64=get_test_wav(), format="wav", start_ms=0, end_ms=200)
        )
        assert "裁剪完成" in result

    def test_invalid_range(self):
        from src.modules.tools.skills.audio.audio_trim import AudioTrimSkill
        skill = AudioTrimSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(audio_b64=get_test_wav(), format="wav", start_ms=1000, end_ms=500)
        )
        assert "无效" in result


class TestAudioVolume:
    def test_gain(self):
        from src.modules.tools.skills.audio.audio_volume import AudioVolumeSkill
        skill = AudioVolumeSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(audio_b64=get_test_wav(), format="wav", gain_db=-6)
        )
        assert "音量调节完成" in result
        assert "-6.0 dB" in result

    def test_normalize(self):
        from src.modules.tools.skills.audio.audio_volume import AudioVolumeSkill
        skill = AudioVolumeSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(audio_b64=get_test_wav(), format="wav", normalize=True)
        )
        assert "标准化" in result


class TestAudioReverse:
    def test_reverse(self):
        from src.modules.tools.skills.audio.audio_reverse import AudioReverseSkill
        skill = AudioReverseSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(audio_b64=get_test_wav(), format="wav")
        )
        assert "反转完成" in result
