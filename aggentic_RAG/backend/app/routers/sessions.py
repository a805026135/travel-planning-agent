"""用户会话管理"""
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.routers.auth import require_user
from app.schemas.auth import UserInfo
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()


class CreateSessionRequest(BaseModel):
    title: str = Field(default="新规划", max_length=100)


class SessionResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


def _row_to_dict(row) -> dict:
    return dict(row) if row else {}


@router.get("", response_model=list[SessionResponse])
async def list_sessions(user: UserInfo = Depends(require_user)):
    """列出当前用户的所有会话"""
    db = get_db()
    rows = db.execute(
        """SELECT s.*, (SELECT COUNT(*) FROM session_messages WHERE session_id = s.id) as message_count
           FROM sessions s WHERE s.user_id = ? ORDER BY s.updated_at DESC""",
        (user.user_id,),
    ).fetchall()
    db.close()
    return [_row_to_dict(r) for r in rows]


@router.post("")
async def create_session(body: CreateSessionRequest,
                         user: UserInfo = Depends(require_user)):
    """创建新会话"""
    db = get_db()
    cur = db.execute(
        "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
        (user.user_id, body.title),
    )
    db.commit()
    sid = cur.lastrowid
    db.close()
    return {"id": sid, "title": body.title}


@router.get("/{session_id}")
async def get_session(session_id: int, user: UserInfo = Depends(require_user)):
    """获取会话详情（含消息列表）"""
    db = get_db()
    session = db.execute(
        "SELECT * FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user.user_id),
    ).fetchone()
    if not session:
        db.close()
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = db.execute(
        "SELECT * FROM session_messages WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    db.close()
    return {
        **_row_to_dict(session),
        "messages": [_row_to_dict(m) for m in messages],
    }


@router.patch("/{session_id}")
async def update_session(session_id: int, body: CreateSessionRequest,
                         user: UserInfo = Depends(require_user)):
    """更新会话标题"""
    db = get_db()
    cur = db.execute(
        "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (body.title, session_id, user.user_id),
    )
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"ok": True}


@router.delete("/{session_id}")
async def delete_session(session_id: int, user: UserInfo = Depends(require_user)):
    """删除会话"""
    db = get_db()
    cur = db.execute(
        "DELETE FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user.user_id),
    )
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"ok": True}
