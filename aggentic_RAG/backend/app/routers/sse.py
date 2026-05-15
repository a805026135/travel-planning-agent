import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.agent_service import get_task_manager


def _json_serializable(obj):
    """递归转换对象为 JSON 可序列化格式"""
    if isinstance(obj, dict):
        return {k: _json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_serializable(v) for v in obj]
    if hasattr(obj, "dict") and callable(obj.dict):
        return _json_serializable(obj.dict())
    if hasattr(obj, "content") and not callable(obj.content):
        return str(obj.content)
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)

router = APIRouter()


@router.get("/stream/{task_id}")
async def stream_progress(task_id: str):
    """
    SSE 端点
    前端通过 EventSource 连接，接收 Agent 实时进度事件
    """
    task_mgr = get_task_manager()
    queue = task_mgr.get_queue(task_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                safe = _json_serializable(event)
                yield f"data: {json.dumps(safe, ensure_ascii=False)}\n\n"
                if event.get("type") in ("complete", "error"):
                    break
        finally:
            # 清理已完成的任务
            task_mgr.cleanup_old_tasks()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    轮询结果接口
    用于不使用 SSE 的场景，轮询获取 Agent 执行结果
    """
    task_mgr = get_task_manager()
    task = task_mgr.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.error:
        return {"status": "error", "error": task.error}

    if task.result is None:
        return {"status": "running"}

    travel_plan = task.result.get("travel_plan")
    state = task.result.get("state", task.result)

    return {
        "status": "complete",
        "travel_plan": travel_plan,
        "meta": {
            "destination": state.get("destination"),
            "origin": state.get("origin"),
            "travel_days": state.get("travel_days"),
            "budget": state.get("budget"),
            "travel_date": state.get("travel_date"),
            "query_mode": state.get("query_mode"),
            "is_complete": state.get("is_complete"),
        },
    }
