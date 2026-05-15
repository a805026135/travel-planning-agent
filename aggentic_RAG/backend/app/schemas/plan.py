from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class PlanRequest(BaseModel):
    """旅行规划请求 - 支持自然语言和结构化输入"""
    query: str = Field(
        default="",
        description="自然语言查询（与结构化字段二选一，优先使用结构化字段）",
    )
    session_id: Optional[int] = Field(default=None, description="会话 ID，不传则自动创建")
    history: Optional[list] = Field(default=None, description="历史消息列表 [{role, content}]")
    origin: Optional[str] = Field(default=None, description="出发城市")
    destination: Optional[str] = Field(default=None, description="目的城市")
    start_date: Optional[str] = Field(default=None, description="出发日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="结束日期 YYYY-MM-DD")
    budget: Optional[float] = Field(default=None, description="预算（元）")
    notes: Optional[str] = Field(default=None, description="备注/偏好说明")

    def build_query(self) -> str:
        """从结构化字段构建查询字符串，用于传给 Agent"""
        parts = []

        if self.destination:
            dest = self.destination.strip()
            if self.origin and self.origin.strip():
                parts.append(f"从{self.origin.strip()}到{dest}旅游")
            else:
                parts.append(f"去{dest}旅游")

            if self.start_date:
                days = None
                if self.end_date:
                    from datetime import datetime
                    try:
                        s = datetime.strptime(self.start_date, "%Y-%m-%d")
                        e = datetime.strptime(self.end_date, "%Y-%m-%d")
                        days = (e - s).days + 1
                    except Exception:
                        pass
                if days:
                    parts.append(f"{days}天")
                parts.append(f"{self.start_date}出发")
                if self.end_date and self.end_date != self.start_date:
                    parts.append(f"到{self.end_date}")

            if self.budget is not None and self.budget > 0:
                parts.append(f"预算{int(self.budget)}元")

            if self.notes and self.notes.strip():
                parts.append(f"备注：{self.notes.strip()}")

        base = "，".join(parts) if parts else self.query

        # 注入历史上下文
        if self.history and len(self.history) > 0:
            ctx_lines = ["\n\n【对话历史 - 请结合上下文理解用户意图】"]
            for h in self.history[-6:]:  # 最近 6 条
                role = "用户" if h.get("role") == "user" else "助手"
                content = (h.get("content") or "")[:300]
                ctx_lines.append(f"{role}: {content}")
            return base + "\n".join(ctx_lines)

        return base


class PlanResponse(BaseModel):
    success: bool = True
    travel_plan: Optional[str] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class StreamStartResponse(BaseModel):
    task_id: str
    session_id: Optional[int] = None
    status: str = "started"
    message: str = "Agent 已启动"
