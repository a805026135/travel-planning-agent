import json
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from app.schemas.plan import PlanRequest, PlanResponse, StreamStartResponse
from app.services.agent_service import get_task_manager, build_prefill
from app.routers.auth import get_current_user

router = APIRouter()


def _build_meta(state: dict, body: PlanRequest) -> dict:
    return {
        "destination": state.get("destination") or body.destination or "",
        "origin": state.get("origin") or body.origin or "",
        "travel_days": state.get("travel_days") or 0,
        "budget": state.get("budget") or body.budget or 0,
        "travel_date": state.get("travel_date") or body.start_date or "",
        "end_date": body.end_date or "",
        "query_mode": state.get("query_mode"),
        "is_complete": state.get("is_complete"),
    }


def _resolve_session(db, user_id: int, session_id: int | None, title_hint: str) -> int:
    """解析或创建会话，返回 session_id"""
    if session_id:
        row = db.execute("SELECT id FROM sessions WHERE id = ? AND user_id = ?",
                         (session_id, user_id)).fetchone()
        if row:
            db.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
            db.commit()
            return session_id
    cur = db.execute("INSERT INTO sessions (user_id, title) VALUES (?, ?)",
                     (user_id, (title_hint or "新规划") + " 规划"))
    db.commit()
    return cur.lastrowid


def _save_messages(session_id: int, query: str, travel_plan: str, meta: dict):
    """不依赖 db 参数，内部获取"""
    from app.database import get_db as _get_db
    db = _get_db()
    db.execute(
        "INSERT INTO session_messages (session_id, role, content, meta) VALUES (?, 'user', ?, ?)",
        (session_id, query, json.dumps(meta, ensure_ascii=False)),
    )
    db.execute(
        "INSERT INTO session_messages (session_id, role, content, meta) VALUES (?, 'assistant', ?, ?)",
        (session_id, travel_plan or "", json.dumps(meta, ensure_ascii=False)),
    )
    db.commit()
    db.close()


@router.post("", response_model=PlanResponse)
async def create_plan(body: PlanRequest,
                      authorization: Optional[str] = Header(default=None)):
    query = body.build_query()
    if not query:
        raise HTTPException(status_code=400, detail="请填写至少一个目的地或查询描述")

    user = get_current_user(authorization)
    user_id = user.user_id if user else None
    prefill = build_prefill(
        origin=body.origin, destination=body.destination,
        start_date=body.start_date, end_date=body.end_date,
        budget=body.budget, notes=body.notes,
    )

    # 创建/解析会话
    session_id = None
    if user_id:
        from app.database import get_db as _get_db
        db = _get_db()
        session_id = _resolve_session(db, user_id, body.session_id,
                                       body.destination or "")
        db.close()

    task_mgr = get_task_manager()
    task_id = await task_mgr.start_plan(query, prefill=prefill,
                                        user_id=user_id, session_id=session_id,
                                        history=body.history)
    task = task_mgr.get_task(task_id)
    try:
        await task.task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if task.error:
        raise HTTPException(status_code=500, detail=task.error)

    result = task.result or {}
    travel_plan = result.get("travel_plan") or ""
    state = result.get("state", result)
    meta = _build_meta(state, body)

    # 若非 stream 模式且之前没有保存过（agent_service 中会保存），这里做 fallback
    if user_id and session_id and (not travel_plan or travel_plan == result.get("travel_plan", "")):
        try:
            _save_messages(session_id, query, travel_plan, meta)
        except Exception:
            pass

    return PlanResponse(
        success=True,
        travel_plan=travel_plan,
        meta={**meta, "session_id": session_id},
    )


@router.post("/stream", response_model=StreamStartResponse)
async def create_plan_stream(body: PlanRequest,
                             authorization: Optional[str] = Header(default=None)):
    query = body.build_query()
    if not query:
        raise HTTPException(status_code=400, detail="请填写至少一个目的地或查询描述")

    user = get_current_user(authorization)
    user_id = user.user_id if user else None
    prefill = build_prefill(
        origin=body.origin, destination=body.destination,
        start_date=body.start_date, end_date=body.end_date,
        budget=body.budget, notes=body.notes,
    )

    # 创建/解析会话
    session_id = body.session_id
    if user_id and not session_id:
        from app.database import get_db as _get_db
        db = _get_db()
        session_id = _resolve_session(db, user_id, None, body.destination or "")
        db.close()

    task_mgr = get_task_manager()
    task_id = await task_mgr.start_plan(query, prefill=prefill,
                                        user_id=user_id, session_id=session_id,
                                        history=body.history)
    return StreamStartResponse(task_id=task_id, session_id=session_id)
