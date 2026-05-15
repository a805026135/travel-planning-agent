"""
FastAPI 后端入口
sys.path 已在 app.main 中自动配置，直接启动 uvicorn

用法:
    python backend/run.py
"""
from __future__ import annotations
import os
import sys
import io

# Windows 控制台编码修复: 防止 agent 中 print(emoji) 导致 GBK 报错
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8765,
        reload=False,
    )
