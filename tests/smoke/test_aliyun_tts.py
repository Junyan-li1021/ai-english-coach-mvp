"""
冒烟测试 2: 阿里云 TTS (语音合成)

运行:  python tests/smoke/test_aliyun_tts.py

验证:
  - 能建立 TTS WebSocket 连接
  - 发送文本后能收到音频分片
  - 保存为 WAV 文件并验证大小 > 0
"""

from __future__ import annotations

import asyncio
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from conftest import check_env
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM in a WAV header."""
    data_size = len(pcm_bytes)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, 1, sample_rate,
        sample_rate * 2, 2, 16,
        b"data", data_size,
    )
    return header + pcm_bytes


async def run():
    # ── Check prerequisites ──────────────────────────────────
    ak_id = check_env("ALIYUN_ACCESS_KEY_ID")
    ak_secret = check_env("ALIYUN_ACCESS_KEY_SECRET")
    appkey = check_env("ALIYUN_NLS_APPKEY")

    if not (ak_id and ak_secret and appkey):
        print("[SKIP] 阿里云 TTS 冒烟测试: 缺少环境变量 ALIYUN_ACCESS_KEY_ID / ALIYUN_ACCESS_KEY_SECRET / ALIYUN_NLS_APPKEY")
        return True

    from app.config import Settings
    from app.services.tts_service import TTSService

    config = Settings()
    tts = TTSService(config)

    text = "Hello, welcome to your interview."
    output_path = Path(__file__).resolve().parents[2] / "tests" / "smoke" / "fixtures" / "test_output_tts.wav"

    try:
        # ── Step 1: Get token ────────────────────────────────
        print("[1/2] 获取阿里云 NLS Token...")
        t0 = time.time()
        await tts._fetch_token()
        print(f"  Token obtained in {time.time()-t0:.2f}s")

        # ── Step 2: Synthesize ───────────────────────────────
        print(f'[2/2] 合成语音: "{text}"')
        pcm_chunks: list[bytes] = []
        chunk_count = 0
        t1 = time.time()
        async for chunk in tts.synthesize(text, voice="en_us_001"):
            pcm_chunks.append(chunk)
            chunk_count += 1

        elapsed = time.time() - t1
        pcm_data = b"".join(pcm_chunks)
        wav_data = _pcm_to_wav(pcm_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(wav_data)
        size_kb = len(wav_data) / 1024

        print(f"  收到 {chunk_count} 个音频分片, 耗时 {elapsed:.2f}s")
        print(f"  保存到 {output_path}  ({size_kb:.1f} KB)")

        assert len(wav_data) > 44, "WAV 文件过小，可能没有音频数据"
        print("[PASS] 阿里云 TTS 冒烟测试通过!")
        return True

    except Exception as e:
        print(f"[FAIL] 阿里云 TTS 冒烟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
