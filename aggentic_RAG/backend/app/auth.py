"""JWT 认证工具"""
import hashlib
import secrets
import os
from datetime import datetime, timedelta
import jwt

SECRET_KEY = os.environ.get("JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
ADMIN_USERS = set(
    u.strip() for u in os.environ.get("ADMIN_USERS", "admin").split(",") if u.strip()
)


def is_admin(username: str) -> bool:
    return username in ADMIN_USERS


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"pbkdf2:{salt}:{h.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    parts = password_hash.split(":")
    if len(parts) != 3 or parts[0] != "pbkdf2":
        return False
    _, salt, h_hex = parts
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return secrets.compare_digest(h.hex(), h_hex)


def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
