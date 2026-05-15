"""
全局配置文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 加载环境变量（明确指定.env文件路径）
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# 阿里云百炼 OpenAI 兼容网关（对话模型、DeepSeek 等均走此 base）
BAILIAN_COMPAT_BASE = os.getenv(
    "BAILIAN_COMPAT_BASE",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# DashScope API Key（Embedding + 默认可用于对话；与百炼控制台 API Key 一致）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# DeepSeek / 百炼对话：未单独配置 DEEPSEEK_API_KEY 时复用 DashScope Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or DASHSCOPE_API_KEY
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", BAILIAN_COMPAT_BASE)

# 主对话 LLM（原 Qwen 槽位，可通过环境变量改为百炼上任意兼容模型）
QWEN3_API_BASE = os.getenv("QWEN3_API_BASE", BAILIAN_COMPAT_BASE)
QWEN3_MODEL = os.getenv("QWEN3_MODEL", "deepseek-v4-flash")
QWEN3_TEMPERATURE = float(os.getenv("QWEN3_TEMPERATURE", "0.7"))

# R1 深度分析（OpenAI 兼容客户端，默认同样使用百炼 deepseek-v4-flash）
R1_MODEL = os.getenv("R1_MODEL", "deepseek-v4-flash")
R1_TEMPERATURE = float(os.getenv("R1_TEMPERATURE", "0.1"))

# LangSmith配置（可选，仅用于调试）
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")

# Embedding模型
EMBEDDING_MODEL = "text-embedding-v4"

# RAG配置
CHROMA_PERSIST_DIR = PROJECT_ROOT / "data" / "travel_vectordb"
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_SEARCH_K = 3
RAG_BATCH_SIZE = 10  # ChromaDB批量载入大小，如遇到API限制可调小

# MCP配置
_mcp_path_env = os.getenv("MCP_CONFIG_PATH", "travel_agent/config/servers_config.json")
# 如果是相对路径，则相对于PROJECT_ROOT解析
if not Path(_mcp_path_env).is_absolute():
    MCP_CONFIG_PATH = str(PROJECT_ROOT / _mcp_path_env)
else:
    MCP_CONFIG_PATH = _mcp_path_env
