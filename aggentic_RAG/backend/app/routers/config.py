from fastapi import APIRouter

# 导入配置（不暴露 API Key）
try:
    from travel_agent.config.settings import (
        QWEN3_MODEL,
        R1_MODEL,
        MCP_CONFIG_PATH,
        CHROMA_PERSIST_DIR,
        RAG_CHUNK_SIZE,
        RAG_SEARCH_K,
        RAG_BATCH_SIZE,
    )
except ImportError:
    QWEN3_MODEL = "unknown"
    R1_MODEL = "unknown"
    MCP_CONFIG_PATH = "unknown"
    CHROMA_PERSIST_DIR = "unknown"
    RAG_CHUNK_SIZE = 500
    RAG_SEARCH_K = 3
    RAG_BATCH_SIZE = 10

router = APIRouter()


@router.get("/config")
async def get_config():
    """获取系统配置（不包含 API Key）"""
    return {
        "llm": {
            "model": QWEN3_MODEL,
            "r1_model": R1_MODEL,
        },
        "rag": {
            "chunk_size": RAG_CHUNK_SIZE,
            "search_k": RAG_SEARCH_K,
            "batch_size": RAG_BATCH_SIZE,
            "persist_dir": str(CHROMA_PERSIST_DIR) if CHROMA_PERSIST_DIR != "unknown" else "unknown",
        },
        "mcp": {
            "config_path": str(MCP_CONFIG_PATH) if MCP_CONFIG_PATH != "unknown" else "unknown",
        },
    }
