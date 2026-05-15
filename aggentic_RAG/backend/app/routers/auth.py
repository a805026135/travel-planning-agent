from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer
from typing import Optional
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserInfo
from app.database import get_db
from app.auth import hash_password, verify_password, create_token, decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_current_user(authorization: Optional[str] = Header(default=None)) -> UserInfo | None:
    """从 Authorization header 解析当前用户，不强制要求登录"""
    if not authorization:
        return None
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        payload = decode_token(token)
        if payload is None:
            return None
        return UserInfo(user_id=payload["user_id"], username=payload["username"])
    except (ValueError, KeyError):
        return None


def require_user(authorization: Optional[str] = Header(default=None)) -> UserInfo:
    """强制要求登录"""
    user = get_current_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def require_admin(authorization: Optional[str] = Header(default=None)) -> UserInfo:
    """强制要求管理员"""
    from app.auth import is_admin
    user = require_user(authorization)
    if not is_admin(user.username):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")
    return user


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    """注册"""
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    if existing:
        return AuthResponse(success=False, message="用户名已存在")

    pw_hash = hash_password(body.password)
    cur = db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                     (body.username, pw_hash))
    db.commit()
    user_id = cur.lastrowid
    token = create_token(user_id, body.username)
    db.close()
    return AuthResponse(success=True, token=token, username=body.username,
                        user_id=user_id, message="注册成功")


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """登录"""
    db = get_db()
    row = db.execute("SELECT id, password_hash FROM users WHERE username = ?",
                     (body.username,)).fetchone()
    db.close()
    if not row:
        return AuthResponse(success=False, message="账号不存在")

    if not verify_password(body.password, row["password_hash"]):
        return AuthResponse(success=False, message="密码错误")

    token = create_token(row["id"], body.username)
    return AuthResponse(success=True, token=token, username=body.username,
                        user_id=row["id"], message="登录成功")


@router.get("/me", response_model=UserInfo)
async def me(user: UserInfo = Depends(require_user)):
    """获取当前用户信息"""
    return user


@router.get("/admin/check")
async def admin_check(user: UserInfo = Depends(require_user)):
    """检查当前用户是否为管理员"""
    from app.auth import is_admin
    return {"is_admin": is_admin(user.username), "username": user.username}
