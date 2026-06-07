"""
冒烟测试 3: DeepSeek LLM (对话 + 评分)

运行:  python tests/smoke/test_deepseek.py

验证:
  - 测试1: 发送简单对话消息，收到非空回复
  - 测试2: 用 function calling 发送评分请求，收到结构化 JSON
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


async def test_chat():
    """Test 1: simple chat completion."""
    print("=" * 60)
    print("测试 1: DeepSeek 简单对话")
    print("=" * 60)

    from app.config import Settings
    from app.services.llm_service import LLMService

    config = Settings()
    llm = LLMService(config)

    messages = [
        {"role": "user", "content": "Hello, I'm here for the interview."}
    ]

    print(f'发送: "{messages[0]["content"]}"')
    t0 = time.time()
    full_response = ""
    async for chunk in llm.chat(messages):
        full_response += chunk
        print(chunk, end="", flush=True)
    print()
    elapsed = time.time() - t0

    assert full_response.strip(), "LLM 返回为空"
    print(f"\n回复长度: {len(full_response)} 字符, 耗时 {elapsed:.2f}s")
    print("[PASS] 测试 1 通过: 对话回复非空\n")
    return True


async def test_evaluate():
    """Test 2: structured evaluation via function calling."""
    print("=" * 60)
    print("测试 2: DeepSeek 评分 (Function Calling)")
    print("=" * 60)

    from app.config import Settings
    from app.services.llm_service import LLMService

    config = Settings()
    llm = LLMService(config)

    transcript = (
        "I think the project is very good because it help many people "
        "to learn English. The team work very hard and we finish on time. "
        "I am proud of what we do together."
    )

    print(f"评分文本: {transcript[:80]}...")
    t0 = time.time()
    result = await llm.evaluate(transcript)
    elapsed = time.time() - t0

    print(f"评分结果 ({elapsed:.2f}s):")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Verify structure
    assert "overall_score" in result, "返回 JSON 缺少 overall_score 字段"
    assert isinstance(result["overall_score"], (int, float)), "overall_score 不是数字"
    print(f"\n[PASS] 测试 2 通过: 返回了结构化评分 (overall_score={result['overall_score']})\n")
    return True


async def run():
    api_key = check_env("DEEPSEEK_API_KEY")
    if not api_key:
        print("[SKIP] DeepSeek 冒烟测试: 缺少环境变量 DEEPSEEK_API_KEY")
        return True

    results = []
    try:
        results.append(await test_chat())
    except Exception as e:
        print(f"[FAIL] 测试 1 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_evaluate())
    except Exception as e:
        print(f"[FAIL] 测试 2 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    all_pass = all(results)
    if all_pass:
        print("=" * 60)
        print("[PASS] DeepSeek 冒烟测试全部通过!")
        print("=" * 60)
    return all_pass


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
