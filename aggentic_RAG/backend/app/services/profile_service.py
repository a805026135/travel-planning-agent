"""
用户长期记忆服务 — 偏好提取、注入和检索
"""
from __future__ import annotations
import json
from app.database import get_db


def get_profile(user_id: int) -> dict | None:
    """获取用户画像"""
    db = get_db()
    row = db.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    if not row:
        return None
    d = dict(row)
    for key in ("preferred_attraction_types", "budget_range", "travel_style_tags"):
        try:
            d[key] = json.loads(d[key]) if isinstance(d[key], str) else d[key]
        except Exception:
            d[key] = [] if key != "budget_range" else {"min": 0, "max": 0}
    return d


def create_or_update_profile(user_id: int, updates: dict):
    """创建或更新用户画像"""
    db = get_db()
    existing = db.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()

    def to_json(v):
        return json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v

    if existing:
        # 合并更新
        cur = db.execute(
            """UPDATE user_profile SET
               preferred_transport = CASE WHEN ? != '' THEN ? ELSE preferred_transport END,
               preferred_hotel_level = CASE WHEN ? != '' THEN ? ELSE preferred_hotel_level END,
               preferred_attraction_types = ?,
               budget_range = ?,
               travel_style_tags = ?,
               common_departure_city = CASE WHEN ? != '' THEN ? ELSE common_departure_city END,
               profile_summary = ?,
               updated_at = CURRENT_TIMESTAMP
               WHERE user_id = ?""",
            (
                updates.get("preferred_transport", ""),
                updates.get("preferred_transport", ""),
                updates.get("preferred_hotel_level", ""),
                updates.get("preferred_hotel_level", ""),
                to_json(updates.get("preferred_attraction_types", [])),
                to_json(updates.get("budget_range", {"min": 0, "max": 0})),
                to_json(updates.get("travel_style_tags", [])),
                updates.get("common_departure_city", ""),
                updates.get("common_departure_city", ""),
                updates.get("profile_summary", ""),
                user_id,
            ),
        )
    else:
        db.execute(
            """INSERT INTO user_profile
               (user_id, preferred_transport, preferred_hotel_level,
                preferred_attraction_types, budget_range, travel_style_tags,
                common_departure_city, profile_summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                updates.get("preferred_transport", ""),
                updates.get("preferred_hotel_level", ""),
                to_json(updates.get("preferred_attraction_types", [])),
                to_json(updates.get("budget_range", {"min": 0, "max": 0})),
                to_json(updates.get("travel_style_tags", [])),
                updates.get("common_departure_city", ""),
                updates.get("profile_summary", ""),
            ),
        )
    db.commit()
    db.close()


def build_profile_prompt(user_id: int) -> str:
    """构建注入到 planner prompt 的用户偏好摘要"""
    profile = get_profile(user_id)
    if not profile:
        return ""

    parts = []
    if profile.get("preferred_transport"):
        parts.append(f"偏好交通方式：{profile['preferred_transport']}")
    if profile.get("preferred_hotel_level"):
        parts.append(f"住宿标准：{profile['preferred_hotel_level']}")
    if profile.get("common_departure_city"):
        parts.append(f"常住城市：{profile['common_departure_city']}")
    tags = profile.get("travel_style_tags") or []
    if tags:
        parts.append(f"旅行风格：{'、'.join(tags)}")
    attrs = profile.get("preferred_attraction_types") or []
    if attrs:
        parts.append(f"偏好景点类型：{'、'.join(attrs)}")
    br = profile.get("budget_range") or {}
    if br.get("min") or br.get("max"):
        parts.append(f"历史预算范围：{br.get('min', 0)}-{br.get('max', 0)} 元")

    if not parts:
        return ""

    return "【该用户历史偏好】" + "；".join(parts) + "。请优先推荐符合此类偏好的方案。"


def search_similar_session(user_id: int, hint: str) -> dict | None:
    """根据模糊意图检索相似历史会话"""
    db = get_db()
    # 按标题模糊匹配
    rows = db.execute(
        """SELECT id, title, updated_at FROM sessions
           WHERE user_id = ? AND (title LIKE ? OR title LIKE ?)
           ORDER BY updated_at DESC LIMIT 3""",
        (user_id, f"%{hint}%", f"%{hint[:2]}%"),
    ).fetchall()
    db.close()
    if rows:
        return dict(rows[0])
    return None
