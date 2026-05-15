"""
异步 Agent 任务管理器
负责在后台运行旅行规划 Agent，通过 asyncio.Queue 向 SSE 推送实时进度。
"""
from __future__ import annotations
import asyncio
import uuid
import traceback
from datetime import datetime, date
from typing import Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class AgentTask:
    """单个 Agent 执行任务"""
    task_id: str
    query: str
    prefill: dict | None = None
    user_id: int | None = None
    session_id: int | None = None
    history: list | None = None
    task: asyncio.Task | None = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentTaskManager:
    """管理多个 Agent 后台任务，每个任务有独立的 SSE 进度队列"""

    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}

    async def start_plan(self, query: str, prefill: dict | None = None,
                         user_id: int | None = None, session_id: int | None = None,
                         history: list | None = None) -> str:
        """启动后台 Agent，立即返回 task_id"""
        task_id = str(uuid.uuid4())
        queue: asyncio.Queue = asyncio.Queue()

        # 注入用户画像到查询
        enhanced_query = query
        if user_id:
            try:
                from app.services.profile_service import build_profile_prompt, search_similar_session
                profile_prompt = build_profile_prompt(user_id)
                if profile_prompt:
                    enhanced_query = query + "\n\n" + profile_prompt
                    await queue.put({
                        "type": "progress", "step": "profile", "status": "已加载您的历史偏好",
                        "timestamp": datetime.now().isoformat(),
                    })
            except Exception:
                pass

        atask = AgentTask(task_id=task_id, query=enhanced_query, prefill=prefill,
                          user_id=user_id, session_id=session_id, history=history,
                          queue=queue)
        self._tasks[task_id] = atask

        async def _run():
            try:
                # 优先使用 AgentExecutor（支持 status_callback，进度粒度更细）
                try:
                    from travel_agent.core.agent_executor import AgentExecutor

                    async def _cb(step_name: str, status: str, result: Any):
                        event = {
                            "type": "progress",
                            "step": step_name,
                            "status": status,
                            "timestamp": datetime.now().isoformat(),
                        }
                        # 检测降级标记
                        if isinstance(result, dict):
                            if result.get("degraded"):
                                event["degraded"] = True
                                event["fallback"] = result.get("fallback", "")
                            if "parallel" in result:
                                event["parallel"] = result["parallel"]
                                event["parallel_id"] = result.get("parallel_id", "")
                        elif isinstance(result, str) and "⚠️" in result:
                            event["degraded"] = True
                        await queue.put(event)

                    executor = AgentExecutor(max_iterations=50, status_callback=_cb)
                    final = await executor.execute(query, conversation_history=atask.history, prefill=prefill)

                except ImportError:
                    # 回退: 使用 run_travel_agent（无逐步骤进度）
                    await queue.put({
                        "type": "progress",
                        "step": "agent",
                        "status": "Agent 正在运行...",
                        "timestamp": datetime.now().isoformat(),
                    })
                    from travel_agent.app import run_travel_agent
                    final = await run_travel_agent(query, prefill=prefill, history=atask.history)

            except Exception as exc:
                traceback.print_exc()
                atask.error = str(exc)
                await queue.put({"type": "error", "error": str(exc), "step": "error"})
                return

            # 清理工具缓存
            try:
                from travel_agent.tools.tool_cache import get_tool_cache
                get_tool_cache().clear()
            except Exception:
                pass

            # 提取并更新用户画像
            if atask.user_id:
                try:
                    from app.services.profile_service import create_or_update_profile
                    state = final.get("state", final)
                    dest = state.get("destination") or (atask.prefill or {}).get("destination") or ""
                    origin = state.get("origin") or (atask.prefill or {}).get("origin") or ""
                    prof = {}
                    if origin:
                        prof["common_departure_city"] = origin
                    # 从 prefill 推断偏好
                    pf = atask.prefill or {}
                    budget = pf.get("budget") or state.get("budget") or 0
                    if budget:
                        br = {"min": max(0, int(budget * 0.6)), "max": int(budget * 1.5)}
                        prof["budget_range"] = br
                    prefs = pf.get("preferences") or state.get("preferences") or []
                    if prefs:
                        prof["travel_style_tags"] = prefs if isinstance(prefs, list) else [prefs]
                    if dest:
                        prof["profile_summary"] = f"最近一次规划: {origin} → {dest}"
                    if prof:
                        create_or_update_profile(atask.user_id, prof)
                except Exception:
                    pass

            atask.result = final
            # 保存到会话
            if atask.user_id:
                try:
                    from app.database import get_db
                    import json as _json
                    db = get_db()
                    if not atask.session_id:
                        dest = (atask.prefill or {}).get("destination") or "新规划"
                        cur = db.execute(
                            "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
                            (atask.user_id, dest + " 规划"),
                        )
                        atask.session_id = cur.lastrowid
                    else:
                        db.execute(
                            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                            (atask.session_id, atask.user_id),
                        )
                    travel_plan = final.get("travel_plan") or ""
                    state = final.get("state", final)
                    meta = {
                        "destination": state.get("destination") or "",
                        "origin": state.get("origin") or "",
                        "travel_days": state.get("travel_days") or 0,
                    }
                    db.execute(
                        "INSERT INTO session_messages (session_id, role, content, meta) VALUES (?, 'user', ?, ?)",
                        (atask.session_id, atask.query, _json.dumps(meta, ensure_ascii=False)),
                    )
                    db.execute(
                        "INSERT INTO session_messages (session_id, role, content, meta) VALUES (?, 'assistant', ?, ?)",
                        (atask.session_id, travel_plan, _json.dumps(meta, ensure_ascii=False)),
                    )
                    db.commit()
                    db.close()
                except Exception:
                    pass  # 保存失败不影响主流程

            await queue.put({"type": "complete", "result": final, "session_id": atask.session_id})

        atask.task = asyncio.create_task(_run())
        return task_id

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._tasks.get(task_id)

    def get_queue(self, task_id: str) -> Optional[asyncio.Queue]:
        task = self._tasks.get(task_id)
        return task.queue if task else None

    def cleanup_old_tasks(self, max_age_minutes: int = 30):
        """清理超过指定时间的已完成任务"""
        now = datetime.now()
        to_delete = []
        for tid, task in self._tasks.items():
            if task.result is not None or task.error is not None:
                try:
                    created = datetime.fromisoformat(task.created_at)
                    if (now - created).total_seconds() > max_age_minutes * 60:
                        to_delete.append(tid)
                except ValueError:
                    to_delete.append(tid)
        for tid in to_delete:
            del self._tasks[tid]


def build_prefill(origin: str | None, destination: str | None,
                  start_date: str | None, end_date: str | None,
                  budget: float | None, notes: str | None) -> dict:
    """从结构化输入构建 prefill dict，用于跳过 planner LLM 提取"""
    prefill: dict = {}

    if destination and destination.strip():
        prefill["destination"] = destination.strip()
    if origin and origin.strip():
        prefill["origin"] = origin.strip()

    if start_date:
        prefill["travel_date"] = start_date.strip()

    if budget is not None and budget > 0:
        prefill["budget"] = float(budget)

    # 计算天数
    if start_date and end_date:
        try:
            s = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            e = datetime.strptime(end_date.strip(), "%Y-%m-%d")
            days = (e - s).days + 1
            if days > 0:
                prefill["travel_days"] = days
        except ValueError:
            pass

    # 备注作为偏好
    prefs = []
    if notes and notes.strip():
        prefs.append(notes.strip())
    if prefs:
        prefill["preferences"] = prefs

    return prefill


# 全局单例
_manager: Optional[AgentTaskManager] = None


def get_task_manager() -> AgentTaskManager:
    global _manager
    if _manager is None:
        _manager = AgentTaskManager()
    return _manager
