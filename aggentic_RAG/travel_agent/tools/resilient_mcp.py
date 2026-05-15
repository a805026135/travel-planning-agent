"""
弹性 MCP 工具调用 — 含超时、重试、降级 fallback 策略
"""
from __future__ import annotations
import asyncio
import traceback
from typing import Any, Callable


FALLBACK_MESSAGES = {
    "12306": "暂无法查询火车票，建议您自行查询 12306 或参考高德驾车时间评估出行耗时。",
    "weather": "暂无法获取天气预报，建议您关注当地气象信息。",
    "lucky_day": "未查询到黄历信息。",
    "flight": "航班查询暂不可用，请参考火车或自驾方案。",
    "rag": "知识库检索暂不可用，将基于实时信息规划。",
    "hotel": "酒店搜索暂不可用。",
    "gaode": "高德地图服务暂时不可用。",
}


async def call_mcp_with_resilience(
    tool_name: str,
    category: str,
    call_fn: Callable,
    timeout: float = 15.0,
    max_retries: int = 2,
) -> dict:
    """
    带容错降级的 MCP 工具调用

    Returns:
        {"success": True, "data": ..., "degraded": False}
        {"success": False, "degraded": True, "fallback": str, "error": str}
    """
    last_error = ""

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                await asyncio.sleep(1.0 * attempt)  # 指数退避
            result = await asyncio.wait_for(call_fn(), timeout=timeout)
            return {"success": True, "data": result, "degraded": False, "attempts": attempt + 1}
        except asyncio.TimeoutError:
            last_error = f"超时 ({timeout}s)"
            if attempt < max_retries:
                print(f"  ⏳ {tool_name} 超时，重试 {attempt+2}/{max_retries+1}...")
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                print(f"  ⚠️ {tool_name} 出错: {e}，重试 {attempt+2}/{max_retries+1}...")

    fallback = FALLBACK_MESSAGES.get(category, "该服务暂时不可用。")
    print(f"  ❌ {tool_name} 最终失败: {last_error}，使用降级策略")

    return {
        "success": False,
        "degraded": True,
        "fallback": fallback,
        "error": last_error,
        "attempts": max_retries + 1,
    }
