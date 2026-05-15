"""
局部修改 + 多方案生成端点
"""
from fastapi import APIRouter, HTTPException, Depends
from app.routers.auth import require_user
from app.schemas.auth import UserInfo
from app.database import get_db
from pydantic import BaseModel, Field
from typing import Optional
import json

router = APIRouter()


class ModifyRequest(BaseModel):
    message: str = Field(..., min_length=1, description="修改意见，如：第三天太累了少安排一个景点")
    modify_target: str = Field(default="", description="修改目标，如 day_3 或 budget")


class MultiPlanRequest(BaseModel):
    query: str = ""
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    notes: Optional[str] = None
    num_plans: int = Field(default=3, le=3, ge=2, description="方案数量 2-3")


@router.post("/modify")
async def modify_plan(session_id: int, body: ModifyRequest,
                      user: UserInfo = Depends(require_user)):
    """
    局部修改端点
    基于现有会话的最后一轮计划，仅重新生成受影响部分
    """
    db = get_db()
    # 获取会话的最后一条 assistant 消息
    row = db.execute(
        """SELECT content, meta FROM session_messages
           WHERE session_id = ? AND role = 'assistant'
           ORDER BY created_at DESC LIMIT 1""",
        (session_id,),
    ).fetchone()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="未找到该会话的计划")

    existing_plan = row["content"]
    message = body.message

    # 构建修改 prompt
    modify_prompt = f"""你是一个旅行规划助手。用户对现有旅行方案提出了修改意见，请仅修改受影响的日行程部分。

现有方案：
{existing_plan[:3000]}

用户修改意见：{message}
修改目标：{body.modify_target or '自动检测'}

请只返回修改后的完整方案，保持原方案其他部分不变。标注出修改了哪些部分。"""

    # 调用 Agent
    from app.services.agent_service import get_task_manager
    task_mgr = get_task_manager()
    task_id = await task_mgr.start_plan(modify_prompt,
                                         user_id=user.user_id,
                                         session_id=session_id,
                                         history=history_msgs)
    task = task_mgr.get_task(task_id)
    try:
        await task.task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 获取会话历史
    history_msgs = None
    try:
        db2 = get_db()
        hrows = db2.execute(
            "SELECT role, content FROM session_messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ).fetchall()
        db2.close()
        if hrows:
            history_msgs = [{"role": r["role"], "content": r["content"]} for r in hrows]
    except Exception:
        pass

    task_id = await task_mgr.start_plan(modify_prompt,
                                         user_id=user.user_id,
                                         session_id=session_id,
                                         history=history_msgs)
    task = task_mgr.get_task(task_id)
    try:
        await task.task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    result = task.result or {}
    travel_plan = result.get("travel_plan") or ""
    return {"success": True, "travel_plan": travel_plan, "session_id": session_id}


@router.post("/multi-plan")
async def multi_plan(body: MultiPlanRequest):
    """
    多方案对比生成
    当需求宽泛时，生成 2-3 个差异化方案
    """
    from app.schemas.plan import PlanRequest
    from app.services.agent_service import get_task_manager, build_prefill

    pr = PlanRequest(
        origin=body.origin, destination=body.destination,
        start_date=body.start_date, end_date=body.end_date,
        budget=body.budget, notes=body.notes,
    )
    base_query = pr.build_query() or body.query
    if not base_query:
        raise HTTPException(status_code=400, detail="请提供目的地或查询")

    styles = ["经济实惠游", "舒适品质游", "网红打卡游"]
    plans = []

    for i in range(min(body.num_plans, len(styles))):
        style_query = f"{base_query}，偏好风格：{styles[i]}。请生成一个{styles[i]}方案，与其它方案差异化。"
        prefill = build_prefill(pr.origin, pr.destination, pr.start_date, pr.end_date, pr.budget, pr.notes)
        prefill["preferences"] = (prefill.get("preferences") or []) + [styles[i]]

        task_mgr = get_task_manager()
        task_id = await task_mgr.start_plan(style_query, prefill=prefill)
        task = task_mgr.get_task(task_id)
        try:
            await task.task
        except Exception as e:
            plans.append({"style": styles[i], "error": str(e)})
            continue

        result = task.result or {}
        plans.append({
            "style": styles[i],
            "travel_plan": result.get("travel_plan") or "",
            "meta": {
                "destination": (pr.destination or ""),
                "travel_days": prefill.get("travel_days") or 0,
                "budget": prefill.get("budget") or 0,
            },
        })

    return {"success": True, "plans": plans}
