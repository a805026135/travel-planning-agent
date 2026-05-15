"""
后端启动脚本 — 请在新的终端窗口中运行:
    python start_backend.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend"
for _p in [_BACKEND, _ROOT]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8765, reload=True)
