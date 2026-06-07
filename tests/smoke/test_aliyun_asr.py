"""
冒烟测试 1: 阿里云 ASR (实时语音识别)

运行:  python tests/smoke/test_aliyun_asr.py

验证:
  - 能获取阿里云 NLS Token
  - 能建立 WebSocket 连接
  - 发送 1 秒静音 PCM 后能收到响应（空识别结果也算通过）
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Allow running standalone
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from conftest import check_env, get_config as _get_config
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


async def run():
    # ── Check prerequisites ──────────────────────────────────
    ak_id = check_env("ALIYUN_ACCESS_KEY_ID")
    ak_secret = check_env("ALIYUN_ACCESS_KEY_SECRET")
    appkey = check_env("ALIYUN_NLS_APPKEY")

    if not (ak_id and ak_secret and appkey):
        print("[SKIP] 阿里云 ASR 冒烟测试: 缺少环境变量 ALIYUN_ACCESS_KEY_ID / ALIYUN_ACCESS_KEY_SECRET / ALIYUN_NLS_APPKEY")
        print("       请在 .env 文件中配置后再运行。")
        return True

    from app.config import Settings
    from app.services.asr_service import ASRService

    config = Settings()
    asr = ASRService(config)

    results: list = []

    def on_result(result):
        results.append(result)
        tag = "FINAL" if result.is_final else "PARTIAL"
        print(f"  [ASR {tag}] {result.text!r}")

    try:
        # ── Step 1: Get token ────────────────────────────────
        print("[1/3] 获取阿里云 NLS Token...")
        t0 = time.time()
        token = await asr._fetch_token()
        print(f"  Token obtained in {time.time()-t0:.2f}s  ({token[:20]}...)")
        assert token, "Token 为空"

        # ── Step 2: Connect WebSocket ────────────────────────
        print("[2/3] 连接 ASR WebSocket...")
        await asr.connect(on_result=on_result)
        print("  WebSocket 连接成功")

        # ── Step 3: Send 1 second of silence (PCM 16kHz 16bit mono) ──
        print("[3/3] 发送 1 秒静音 PCM...")
        # 16000 samples/sec * 2 bytes/sample = 32000 bytes
        silence = b"\x00\x00" * 16000
        # Send in 3200-byte chunks (~100ms each)
        chunk_size = 3200
        for offset in range(0, len(silence), chunk_size):
            chunk = silence[offset : offset + chunk_size]
            await asr.send_audio(chunk)
            await asyncio.sleep(0.05)  # simulate real-time pace

        # Wait a moment for any final results
        await asyncio.sleep(1.0)
        await asr.close()

        print(f"  收到 {len(results)} 条识别结果")
        print("[PASS] 阿里云 ASR 冒烟测试通过!")
        return True

    except Exception as e:
        print(f"[FAIL] 阿里云 ASR 冒烟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
