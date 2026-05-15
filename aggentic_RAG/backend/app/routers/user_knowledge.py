"""
用户个人知识库管理 — 每个用户有独立的 ChromaDB collection
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.routers.auth import require_user
from app.schemas.auth import UserInfo
from app.schemas.knowledge import (KnowledgeStatsResponse, KnowledgeUploadResponse,
                                   KnowledgeDeleteRequest)
from app.services.user_knowledge_service import get_user_kb_service

router = APIRouter()


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_user_kb_stats(user: UserInfo = Depends(require_user)):
    """获取个人知识库统计"""
    kb = get_user_kb_service()
    stats = kb.get_stats(user.user_id)
    return KnowledgeStatsResponse(**stats)


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_user_doc(file: UploadFile = File(...),
                          user: UserInfo = Depends(require_user)):
    """上传文档到个人知识库"""
    kb = get_user_kb_service()
    try:
        count = await kb.upload_file(user.user_id, file)
        return KnowledgeUploadResponse(
            success=count > 0,
            message=f"成功导入 {count} 个文本块",
            chunks_imported=count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.delete("/source")
async def delete_user_source(body: KnowledgeDeleteRequest,
                             user: UserInfo = Depends(require_user)):
    """删除个人知识库中的指定源"""
    kb = get_user_kb_service()
    try:
        deleted = kb.delete_by_source(user.user_id, body.source)
        return {"success": True, "deleted_chunks": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
