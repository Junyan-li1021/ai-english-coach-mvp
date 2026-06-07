"""
冒烟测试 5: 全链路串联测试

运行:  python tests/smoke/test_full_chain.py

链路: 文字输入 → DeepSeek 对话 → (可选) TTS 合成 → (可选) ASR 识别
打印每一步的耗时和结果。
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from conftest import check_env
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


async def run():
    from app.config import Settings

    config = Settings()
    print("=" * 60)
    print("全链路冒烟测试")
    print("=" * 60)

    results = {}

    # ── Step 1: DeepSeek Chat ────────────────────────────────
    print("\n[Step 1] DeepSeek 对话...")
    api_key = check_env("DEEPSEEK_API_KEY")
    if api_key:
        from app.services.llm_service import LLMService
        llm = LLMService(config)

        messages = [
            {"role": "user", "content": "Tell me about yourself in two sentences."}
        ]
        t0 = time.time()
        full = ""
        async for chunk in llm.chat(messages):
            full += chunk
        elapsed = time.time() - t0

        results["llm_chat"] = {
            "status": "PASS",
            "time": elapsed,
            "response_len": len(full),
        }
        print(f"  回复 ({elapsed:.2f}s, {len(full)} chars): {full[:100]}...")
    else:
        results["llm_chat"] = {"status": "SKIP", "reason": "DEEPSEEK_API_KEY 未配置"}
        print("  [SKIP] DEEPSEEK_API_KEY 未配置")

    # ── Step 2: DeepSeek Evaluation ──────────────────────────
    print("\n[Step 2] DeepSeek 评分...")
    if api_key:
        from app.services.llm_service import LLMService
        llm = LLMService(config)
        t0 = time.time()
        eval_result = await llm.evaluate(
            "I am a software engineer. I work on many project and I like to coding."
        )
        elapsed = time.time() - t0
        results["llm_eval"] = {
            "status": "PASS",
            "time": elapsed,
            "overall_score": eval_result.get("overall_score"),
        }
        print(f"  评分 ({elapsed:.2f}s): overall={eval_result.get('overall_score')}")
    else:
        results["llm_eval"] = {"status": "SKIP", "reason": "DEEPSEEK_API_KEY 未配置"}
        print("  [SKIP] DEEPSEEK_API_KEY 未配置")

    # ── Step 3: Aliyun TTS ──────────────────────────────────
    print("\n[Step 3] 阿里云 TTS 合成...")
    ak_id = check_env("ALIYUN_ACCESS_KEY_ID")
    ak_secret = check_env("ALIYUN_ACCESS_KEY_SECRET")
    appkey = check_env("ALIYUN_NLS_APPKEY")

    if ak_id and ak_secret and appkey:
        from app.services.tts_service import TTSService
        tts = TTSService(config)
        try:
            t0 = time.time()
            audio_bytes = b""
            chunk_count = 0
            async for chunk in tts.synthesize("Welcome to the interview practice session."):
                audio_bytes += chunk
                chunk_count += 1
            elapsed = time.time() - t0
            results["tts"] = {
                "status": "PASS",
                "time": elapsed,
                "audio_bytes": len(audio_bytes),
                "chunks": chunk_count,
            }
            print(f"  合成 ({elapsed:.2f}s, {chunk_count} chunks, {len(audio_bytes)} bytes)")
        except Exception as e:
            results["tts"] = {"status": "FAIL", "reason": str(e)}
            print(f"  [FAIL] {e}")
    else:
        results["tts"] = {"status": "SKIP", "reason": "阿里云配置未完成"}
        print("  [SKIP] 阿里云配置未完成")

    # ── Step 4: Aliyun ASR ──────────────────────────────────
    print("\n[Step 4] 阿里云 ASR 识别...")
    if ak_id and ak_secret and appkey:
        from app.services.asr_service import ASRService
        asr = ASRService(config)
        try:
            asr_results = []

            def on_result(r):
                asr_results.append(r)

            t0 = time.time()
            await asr.connect(on_result=on_result)
            # Send 0.5 second of silence
            silence = b"\x00\x00" * 8000
            await asr.send_audio(silence)
            await asyncio.sleep(1.0)
            await asr.close()
            elapsed = time.time() - t0
            results["asr"] = {
                "status": "PASS",
                "time": elapsed,
                "results_count": len(asr_results),
            }
            print(f"  ASR ({elapsed:.2f}s, {len(asr_results)} results)")
        except Exception as e:
            results["asr"] = {"status": "FAIL", "reason": str(e)}
            print(f"  [FAIL] {e}")
    else:
        results["asr"] = {"status": "SKIP", "reason": "阿里云配置未完成"}
        print("  [SKIP] 阿里云配置未完成")

    # ── Step 5: Youdao Eval ──────────────────────────────────
    print("\n[Step 5] 有道口语评测...")
    yd_key = check_env("YOUDAO_APP_KEY")
    yd_secret = check_env("YOUDAO_APP_SECRET")
    if yd_key and yd_secret:
        from app.services.eval_service import EvalService
        from scripts.generate_test_audio import generate_sine_wav
        eval_svc = EvalService(config)
        try:
            fixture_dir = Path(__file__).resolve().parents[1] / "fixtures"
            wav_path = generate_sine_wav(fixture_dir / "test_audio.wav")
            wav_bytes = wav_path.read_bytes()

            t0 = time.time()
            eval_out = await eval_svc.evaluate(wav_bytes, q_type="open")
            elapsed = time.time() - t0
            results["youdao_eval"] = {
                "status": "PASS",
                "time": elapsed,
            }
            print(f"  评测 ({elapsed:.2f}s)")
        except Exception as e:
            results["youdao_eval"] = {"status": "FAIL", "reason": str(e)}
            print(f"  [FAIL] {e}")
    else:
        results["youdao_eval"] = {"status": "SKIP", "reason": "有道配置未完成"}
        print("  [SKIP] 有道配置未完成")

    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("测试汇总:")
    print("-" * 60)
    pass_count = 0
    skip_count = 0
    fail_count = 0
    for step, info in results.items():
        status = info["status"]
        if status == "PASS":
            pass_count += 1
            extra = f" ({info.get('time', 0):.2f}s)" if "time" in info else ""
            print(f"  {step:15s} ✓ PASS{extra}")
        elif status == "SKIP":
            skip_count += 1
            print(f"  {step:15s} ◌ SKIP  {info.get('reason', '')}")
        else:
            fail_count += 1
            print(f"  {step:15s} ✗ FAIL  {info.get('reason', '')}")

    print("-" * 60)

    if fail_count > 0:
        print(f"全链路冒烟测试: {pass_count} 通过, {fail_count} 失败, {skip_count} 跳过")
        print("❌ 全链路冒烟测试未通过")
        return False
    else:
        print(f"全链路冒烟测试: {pass_count} 通过, {skip_count} 跳过")
        print("✅ 全链路冒烟测试通过!")
        return True


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
