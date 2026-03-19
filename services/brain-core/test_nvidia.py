"""快速测试 NVIDIA NIM Provider — 验证 API 连通性"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from modules.llm.providers.nvidia_provider import NvidiaProvider, NVIDIA_MODELS
from modules.llm.types import LLMRequest


# 从 API-KEY.md 读取的 NVIDIA API Key
NVIDIA_API_KEY = "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"


async def test_model(provider: NvidiaProvider, model: str, query: str = "你好，请用一句话介绍你自己。"):
    """测试单个模型"""
    print(f"\n{'='*60}")
    print(f"测试模型: {model}")
    print(f"{'='*60}")

    try:
        request = LLMRequest(
            messages=[{"role": "user", "content": query}],
            model=model,
            temperature=0.7,
            max_tokens=256,
            stream=False,
        )
        response = await provider.complete(request)
        print(f"  ✅ 成功! ({response.latency_ms:.0f}ms)")
        print(f"  回复: {response.content[:150]}...")
        print(f"  用量: {response.usage}")
        if hasattr(response, 'thinking') and response.thinking:
            print(f"  思维链: {response.thinking[:100]}...")
        return True
    except Exception as e:
        print(f"  ❌ 失败: {type(e).__name__}: {e}")
        return False


async def test_stream(provider: NvidiaProvider, model: str):
    """测试流式输出"""
    print(f"\n{'='*60}")
    print(f"流式测试: {model}")
    print(f"{'='*60}")

    try:
        request = LLMRequest(
            messages=[{"role": "user", "content": "用三句话解释什么是人工智能。"}],
            model=model,
            temperature=0.7,
            max_tokens=256,
            stream=True,
        )
        chunks = []
        import json
        async for chunk_json in provider.stream(request):
            data = json.loads(chunk_json)
            if data.get("type") == "chunk":
                chunks.append(data["content"])
                print(data["content"], end="", flush=True)
            elif data.get("type") == "thinking":
                pass  # 忽略思维链
            elif data.get("type") == "done":
                break
        print()
        print(f"  ✅ 流式成功! 共 {len(chunks)} 个 chunk")
        return True
    except Exception as e:
        print(f"  ❌ 流式失败: {type(e).__name__}: {e}")
        return False


async def main():
    print("🚀 NVIDIA NIM Provider 连通性测试")
    print(f"   Base URL: https://integrate.api.nvidia.com/v1")
    print(f"   可用模型: {len(NVIDIA_MODELS)} 个")

    provider = NvidiaProvider(api_key=NVIDIA_API_KEY)

    # 测试关键模型（每个脑区对应的模型）
    test_models = [
        ("qwen/qwen3.5-397b-a17b", "右脑皮层"),
        ("nvidia/nemotron-3-nano-30b-a3b", "海马体/意识核"),
    ]

    results = {}
    for model, role in test_models:
        ok = await test_model(provider, model, f"你好！请用一句话介绍你的能力。（测试 {role} 模型）")
        results[model] = ok

    # 流式测试（用最轻量的模型）
    stream_ok = await test_stream(provider, "nvidia/nemotron-3-nano-30b-a3b")
    results["stream"] = stream_ok

    # 汇总
    print(f"\n{'='*60}")
    print("📊 测试汇总")
    print(f"{'='*60}")
    for key, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {key}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 NVIDIA NIM Provider 全部测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查 API Key 和网络连接。")


if __name__ == "__main__":
    asyncio.run(main())
