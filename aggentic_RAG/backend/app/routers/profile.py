"""用户画像 API"""
from fastapi import APIRouter, Depends
from app.routers.auth import require_user
from app.schemas.auth import UserInfo
from app.services.profile_service import get_profile, create_or_update_profile

router = APIRouter()


@router.get("")
async def get_my_profile(user: UserInfo = Depends(require_user)):
    """获取当前用户的旅行画像"""
    prof = get_profile(user.user_id)
    if not prof:
        # 返回空画像
        return {
            "user_id": user.user_id,
            "preferred_transport": "",
            "preferred_hotel_level": "",
            "preferred_attraction_types": [],
            "budget_range": {"min": 0, "max": 0},
            "travel_style_tags": [],
            "common_departure_city": "",
            "profile_summary": "",
        }
    return prof


@router.put("")
async def update_my_profile(body: dict, user: UserInfo = Depends(require_user)):
    """手动更新用户画像"""
    create_or_update_profile(user.user_id, body)
    return {"ok": True, "profile": get_profile(user.user_id)}
