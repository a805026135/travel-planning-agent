from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.schemas.knowledge import (
    KnowledgeStatsResponse,
    KnowledgeUploadResponse,
    KnowledgeDeleteRequest,
    KnowledgeBuildRequest,
)
from app.services.knowledge_service import get_kb_service
from app.routers.auth import require_admin, get_current_user
from app.schemas.auth import UserInfo

router = APIRouter()


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_stats():
    """获取系统知识库统计信息（公开）"""
    kb = get_kb_service()
    try:
        stats = kb.get_stats()
        return KnowledgeStatsResponse(
            total=stats.get("total_docs", 0),
            sources=stats.get("sources", []),
        )
    except Exception:
        return KnowledgeStatsResponse(total=0, sources=[])


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: UserInfo = Depends(require_admin),
):
    """上传文档到系统知识库（仅管理员）"""
    kb = get_kb_service()
    try:
        count = await kb.upload_file(file)
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
async def delete_source(
    body: KnowledgeDeleteRequest,
    user: UserInfo = Depends(require_admin),
):
    """删除系统知识库中的指定源（仅管理员）"""
    kb = get_kb_service()
    try:
        deleted = kb.delete_by_source(body.source)
        return {"success": True, "deleted_chunks": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_knowledge_base(
    body: KnowledgeBuildRequest,
    user: UserInfo = Depends(require_admin),
):
    """从目录重建系统知识库（仅管理员）"""
    kb = get_kb_service()
    try:
        kb.build_knowledge_base(
            source_path=body.source_path,
            force_recreate=body.force_recreate,
        )
        stats = kb.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
