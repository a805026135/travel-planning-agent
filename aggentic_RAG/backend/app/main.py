"""
FastAPI 应用工厂
"""
from __future__ import annotations

# 必须先设置编码，再导入其他模块
import sys as _sys
import io as _io
if hasattr(_sys.stdout, 'reconfigure'):
    try:
        _sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(_sys.stderr, 'reconfigure'):
    try:
        _sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os as _os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 将 backend/ 和 aggentic_RAG/ 加入 sys.path
# 确保在 uvicorn reload 子进程中也正确加载
_BACKEND = Path(__file__).resolve().parent.parent  # backend/
_PROJECT = _BACKEND.parent  # aggentic_RAG/
for _p in [_BACKEND, _PROJECT]:
    if str(_p) not in _sys.path:
        _sys.path.insert(0, str(_p))

from app.routers import health, plan, sse, config, knowledge, auth, sessions, user_knowledge, profile, modify


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期
    MCP 管理器在 travel_agent 内部按需创建，这里无需额外初始化
    """
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="智能旅行规划 API",
        description="基于 LangChain Agent 的智能旅行规划系统后端",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS 配置
    cors_origins = _os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载路由
    app.include_router(health.router, prefix="/api", tags=["健康检查"])
    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(plan.router, prefix="/api/plan", tags=["规划接口"])
    app.include_router(sse.router, prefix="/api/plan", tags=["SSE 推送"])
    app.include_router(config.router, prefix="/api", tags=["系统配置"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["系统知识库"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["会话管理"])
    app.include_router(user_knowledge.router, prefix="/api/user/knowledge", tags=["个人知识库"])
    app.include_router(profile.router, prefix="/api/profile", tags=["用户画像"])
    app.include_router(modify.router, prefix="/api/plan", tags=["修改与多方案"])

    # 生产环境: 挂载前端静态文件
    static_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")

    return app


app = create_app()
