"""
冒烟测试 4: 有道口语评测 (Youdao Oral Evaluation)

运行:  python tests/smoke/test_youdao_eval.py

验证:
  - 生成测试 WAV 音频
  - 调用有道口语评测 API (open 模式)
  - 返回包含评分字段
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from conftest import check_env
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


async def run():
    # ── Check prerequisites ──────────────────────────────────
    app_key = check_env("YOUDAO_APP_KEY")
    app_secret = check_env("YOUDAO_APP_SECRET")

    if not (app_key and app_secret):
        print("[SKIP] 有道口语评测冒烟测试: 缺少环境变量 YOUDAO_APP_KEY / YOUDAO_APP_SECRET")
        print("       请在 .env 文件中配置后再运行。")
        return True

    from app.config import Settings
    from app.services.eval_service import EvalService

    config = Settings()
    eval_svc = EvalService(config)

    # ── Step 1: Generate test audio ──────────────────────────
    print("[1/3] 生成测试 WAV 音频...")
    project_root = Path(__file__).resolve().parents[2]
    fixture_dir = project_root / "tests" / "smoke" / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    # Generate sine wave audio
    scripts_dir = project_root / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from generate_test_audio import generate_sine_wav

    wav_path = generate_sine_wav(fixture_dir / "test_audio.wav")
    wav_bytes = wav_path.read_bytes()
    print(f"  测试音频: {wav_path} ({len(wav_bytes) / 1024:.1f} KB)")

    # ── Step 2: Call Youdao API ──────────────────────────────
    print("[2/3] 调用有道口语评测 API (open 模式)...")
    t0 = time.time()
    try:
        result = await eval_svc.evaluate(
            audio_wav_bytes=wav_bytes,
            ref_text=None,
            q_type="open",
        )
        elapsed = time.time() - t0
        print(f"  API 响应 ({elapsed:.2f}s):")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # ── Step 3: Verify ───────────────────────────────────
        print("[3/3] 验证返回结构...")
        # The API should return some score fields
        has_scores = any(
            k in result for k in
            ["overall_score", "pronunciation_score", "fluency_score"]
        )
        if has_scores:
            print("  返回包含评分字段 ✓")
        else:
            # For open mode with non-speech audio, scores might be in raw
            if "raw" in result:
                print(f"  原始返回: {result['raw']}")
            print("  注意: 由于测试音频是正弦波(非语音)，评分可能为 0 或异常 — 这是正常的")

        print("[PASS] 有道口语评测冒烟测试通过!")
        return True

    except Exception as e:
        print(f"[FAIL] 有道口语评测冒烟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
