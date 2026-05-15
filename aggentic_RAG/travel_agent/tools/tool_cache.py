"""
工具结果缓存 — 同一会话内按 (tool, params_hash) 缓存 MCP 调用结果
"""
from __future__ import annotations
import hashlib
import json
import time
from typing import Any, Dict


class ToolCache:
    """内存级工具结果缓存，key = (tool_name, params_json_hash)"""

    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, tuple[Any, float]] = {}  # key -> (result, timestamp)
        self._ttl = ttl

    @staticmethod
    def _make_key(tool_name: str, params: dict) -> str:
        raw = json.dumps(params, sort_keys=True, ensure_ascii=False)
        h = hashlib.md5(raw.encode()).hexdigest()
        return f"{tool_name}:{h}"

    def get(self, tool_name: str, params: dict) -> Any | None:
        key = self._make_key(tool_name, params)
        entry = self._cache.get(key)
        if entry is None:
            return None
        result, ts = entry
        if time.time() - ts > self._ttl:
            del self._cache[key]
            return None
        return result

    def set(self, tool_name: str, params: dict, result: Any):
        key = self._make_key(tool_name, params)
        self._cache[key] = (result, time.time())

    def clear(self):
        self._cache.clear()


# 全局单例
_cache: ToolCache | None = None


def get_tool_cache() -> ToolCache:
    global _cache
    if _cache is None:
        _cache = ToolCache()
    return _cache
