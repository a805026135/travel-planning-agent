# 智能旅行规划助手

基于 **LangGraph + AgentExecutor + MCP + RAG** 的智能旅行规划系统，使用 **DeepSeek-V4-Flash**（通过阿里云百炼兼容 API）驱动的双实例协作，结合知识检索与实时数据查询，为用户生成完整的旅行方案。

> **架构特点**: 同时支持 LangGraph 有状态工作流和 AgentExecutor 无递归限制编排，适配 Streamlit 调试与 FastAPI 生产部署。

## 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [系统要求](#系统要求)
- [安装部署](#安装部署)
- [使用指南](#使用指南)
- [数据库管理](#数据库管理)
- [项目结构](#项目结构)
- [API 接口](#api-接口)
- [故障排查](#故障排查)

---

## 项目简介

这是一个智能旅行规划系统，支持 **Streamlit UI**（调试/演示）和 **FastAPI + Vue 3**（生产部署）两种运行模式，通过自然语言对话为用户生成完整的旅行方案。系统自动区分简单查询和复杂行程规划，按场景选择合适的处理路径。

### 主要特性

- **双模式查询**：
  - **简单查询模式**：只需目的地，快速获取景点推荐
  - **完整规划模式**：提供详细信息，生成含交通、住宿、天气、黄历的完整方案

- **双实例协作**（同一模型，不同角色）：
  - 两个 LLM 实例均由 **DeepSeek-V4-Flash**（阿里云百炼）驱动
  - **规划/合成实例**（temperature=0.7）：负责信息提取、工具调用决策和方案生成
  - **深度分析实例**（temperature=0.1）：负责复杂推理、多目的地路线优化、预算分配
  - 系统根据场景复杂度自动选择是否启用深度分析

- **实时数据集成**（基于 MCP 协议，ModelScope 托管）：
  - 12306 火车票查询（自动获取站点代码，查询车次时刻表）
  - 高德地图自驾路线（自动计算距离、时间、过路费）
  - 高德地图酒店搜索（根据预算自动筛选）
  - 高德地图天气预报（支持多日预报）
  - 八字黄历查询（农历、宜忌、吉日）
  - 航班查询（可选，长途 >800km 自动触发）
  - 必应搜索（可选，搜索最新旅游资讯）

- **知识库检索（RAG）**：
  - ChromaDB 向量数据库存储旅游攻略
  - 支持 TXT、MD、PDF、CSV 格式导入
  - DashScope text-embedding-v4 生成向量

---

## 核心功能

### 1. 智能信息提取
- 从自然语言对话中提取出发地、目的地、日期、预算等关键信息
- 支持相对日期（"明天"、"下周"）自动转换
- 多轮对话上下文保持

### 2. 交通方案对比
- 自动查询火车票信息（车次、时间、票价）
- 计算自驾路线（距离、时间、过路费）
- 综合对比推荐最优方案

### 3. 住宿推荐
- 根据预算自动选择酒店等级关键词
  - 预算 > 500元：五星/豪华
  - 预算 300-500元：品牌连锁
  - 预算 < 300元：经济型/快捷
- 提供酒店名称、价格、地址信息

### 4. 天气与黄历
- 查询旅行日期的天气预报（最多4天）
- 查询农历黄历，分析是否适合出行
- 展示宜忌事项

### 5. 行程规划
- 结合 RAG 知识库和实时 POI 数据
- 生成每日详细行程
- 计算预算分配（交通、住宿、餐饮、门票）

---

## 技术架构

### Agent 工作流

```
用户查询
├── Planner 节点           # 信息提取（场景检测、多目的地识别）
│   ├── simple_query       # 简单查询：只需景点信息
│   ├── complex_query      # 复杂查询：特殊需求、预算紧张
│   └── multi_destination  # 多目的地：2个以上城市
│
├── [深度分析模式]          # 复杂/多目的地场景
│   ├── r1_strategy_node   # 分解行程、制定 query_plan
│   ├── ReAct Loop          # 按 query_plan 执行工具调用
│   │   ├── train_query     # 12306查询（自动附带自驾路线）
│   │   ├── gaode_weather   # 天气查询
│   │   ├── gaode_hotel     # 酒店搜索
│   │   ├── lucky_day       # 黄历查询
│   │   └── flight_query    # 航班查询（条件触发）
│   ├── r1_optimization     # 二次优化（仅单目的地）
│   └── synthesizer_node    # 生成最终方案
│
└── [普通模式]               # 简单场景
    ├── ReAct Loop           # LLM 自主决策调用工具
    └── synthesizer_node     # 生成最终方案
```

**关键特性**:
- **无递归限制**: AgentExecutor 模式支持任意长度的 query_plan
- **自动重试**: MCP 工具调用失败自动重试 2 次（SSE 连接保护）
- **超时保护**: 12306 查询 90 秒超时，防止长时间阻塞
- **错误恢复**: 单个工具失败不影响整体流程
- **双运行时**: LangGraph 工作流（Streamlit 调试）+ AgentExecutor（FastAPI 后端）

### 核心技术栈

**后端（Python）**：
- **LangGraph**: 有状态工作流编排（ReAct 模式）
- **AgentExecutor**: 无递归限制的替代执行引擎
- **LangChain**: LLM 调用、工具封装
- **ChromaDB**: 向量数据库（存储旅游攻略）
- **DashScope / 百炼**: 阿里云模型服务
  - DeepSeek-V4-Flash（对话 + 推理）
  - text-embedding-v4（文本嵌入）
- **MCP (Model Context Protocol)**: 外部工具集成（ModelScope 托管）
- **Streamlit**: 调试/演示 UI
- **FastAPI**: 生产后端 API
- **SQLite**: 用户账号、会话、历史记录

**前端**：
- **Vue 3 + Vite**: SPA 前端
- **Axios**: HTTP 通信
- **SSE**: 实时计划流

---

## 系统要求

### 运行环境
- Python >= 3.11
- 8GB+ RAM（用于向量数据库和模型推理）
- Windows/Linux/macOS

### API 密钥
- **DashScope / 百炼 API Key**（必填）：用于 DeepSeek-V4-Flash 和 text-embedding-v4
- **MCP 服务器 URL**（ModelScope 公开服务，默认已配置）

---

## API 密钥获取

### DashScope API Key（阿里云百炼）

**用途**：DeepSeek-V4-Flash 对话模型 + text-embedding-v4 文本嵌入

**获取步骤**：
1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 使用阿里云账号登录（需要实名认证）
3. 进入「模型广场」，开通 DeepSeek-V4-Flash 和 text-embedding-v4
4. 进入「API-KEY 管理」，创建新的 API Key
5. 复制生成的 API Key（格式：`sk-xxxxxxxxxxxxxxxx`）

**费用**：按 Token 使用量计费，新用户有免费额度

> **说明**：本项目两个 LLM 实例使用同一模型 `deepseek-v4-flash`，通过百炼 OpenAI 兼容接口调用。不需要单独的 DeepSeek 平台 API Key。

### MCP 服务器配置

项目已预配置 ModelScope 公开 MCP 服务，无需额外获取。如需替换：

编辑 `aggentic_RAG/travel_agent/config/servers_config.json`：

| 服务器 | 功能 | 协议 |
|--------|------|------|
| 12306 Server | 火车票查询 | streamable_http |
| Gaode Server | 地图、天气、酒店 | streamable_http |
| bazi Server | 八字黄历 | streamable_http |
| flight Server | 航班查询（可选） | streamable_http |
| biying Server | 必应搜索（可选） | streamable_http |

---

## 安装部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd travel-planning-agent-main
```

### 2. 后端安装

#### 2.1 安装依赖

**推荐方式**（支持开发模式）：
```bash
cd aggentic_RAG
pip install -e .
```

或者：
```bash
pip install -r aggentic_RAG/requirements.txt
```

#### 2.2 配置环境变量

在 `aggentic_RAG` 目录下创建 `.env` 文件：

```bash
# 百炼 API Key（必填）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here

# 模型配置（默认使用百炼 deepseek-v4-flash，一般无需修改）
# QWEN3_MODEL=deepseek-v4-flash
# R1_MODEL=deepseek-v4-flash

# LangChain 追踪（可选）
LANGCHAIN_TRACING_V2=false

# MCP 配置路径（默认值）
MCP_CONFIG_PATH=travel_agent/config/servers_config.json

# ChromaDB 路径（默认值）
CHROMA_PERSIST_DIR=./data/travel_vectordb
```

#### 2.3 配置 MCP 服务器

`aggentic_RAG/travel_agent/config/servers_config.json` 已预配置 ModelScope 公开服务，默认可用。如需修改，编辑该文件调整服务器 URL。

#### 2.4 启动应用

**方式一：Streamlit UI（调试/演示）**

在项目根目录运行：

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动。

**方式二：FastAPI 后端（生产）**

```bash
cd aggentic_RAG
python backend/run.py
```

API 将在 `http://localhost:8765` 启动，前端静态文件由 FastAPI 托管。

### 3. 健康检查（可选）

```bash
python check_mcp_health.py
```

输出示例：
```
🔍 MCP 服务器健康检查
============================================================

🔧 12306 Server
   状态: ✅ 正常
   工具数: 3

🔧 Gaode Server
   状态: ✅ 正常
   工具数: 5
   ...

✅ 所有 MCP 服务器状态正常！
```

---

## 使用指南

### 简单查询模式

**适用场景**：快速了解某个城市的景点信息

**示例**：
```
用户：苏州有什么好玩的？
用户：推荐一下成都的景点
```

**系统行为**：
- 只调用 RAG 知识库和高德地图 POI 搜索
- 不查询火车票、天气、黄历
- 返回景点列表和简要介绍

### 完整规划模式

**适用场景**：需要完整的旅行方案

**需要提供的信息**：
- 出发地：如"上海"
- 目的地：如"苏州"
- 旅行天数：如"2天"
- 预算：如"1000元"
- 出发日期：如"12月10日" 或 "明天"

**示例**：
```
用户：我想从上海去苏州玩2天，预算1000元，12月10日出发，帮我规划一下
```

**系统行为**：
1. 提取关键信息
2. 查询 RAG 知识库
3. 查询火车票（12306）
4. 计算自驾路线（高德地图）
5. 推荐酒店（高德地图 + 预算过滤）
6. 查询天气预报（高德地图）
7. 查询黄历吉日（八字服务器）
8. 如需复杂优化，调用深度分析实例
9. 合成完整方案

**输出内容**：
- 基本信息（路线、日期、天气、黄历）
- 交通方案对比（自驾 vs 火车）
- 住宿推荐（2-3家酒店）
- 每日行程安排
- 预算分配明细
- 特别建议（老人/儿童友好提示）

### 深度分析触发条件

深度分析仅在**复杂场景**下启用，以控制成本。满足以下**任意一个条件**自动触发：

1. **复杂的多城市路线** — 示例："上海 → 苏州 → 杭州 → 南京，5天"
2. **紧张的预算优化** — 示例："4人去苏州3天，总预算1500元"
3. **多重冲突的约束条件** — 示例："带两个70岁老人和一个5岁孩子，1天去3个景点"
4. **复杂的优化问题** — 示例："最省钱的方案"、"最快到达的路线"

以下场景**不会**触发深度分析：
- 简单查询："苏州有什么好玩的？"
- 单城市、充裕预算："上海去苏州2天，预算3000元"
- 没有特殊约束："两个成年人去杭州3天"

---

## 数据库管理

本项目使用 **ChromaDB** 作为向量数据库，存储旅游攻略文档。

### 数据库位置

```
aggentic_RAG/data/travel_vectordb/
```

### 导入数据

#### 方式1：Streamlit UI 上传（推荐）

1. 启动应用：`streamlit run app.py`
2. 在左侧边栏找到 **"知识库管理"** 区域
3. 上传文档，系统自动分块 → 向量化 → 存入 ChromaDB
4. 实时显示处理进度，自动去重（基于 UUID）

**支持的格式**：`.txt`、`.md`、`.pdf`、`.csv`

#### 方式2：命令行批量导入

```bash
cd aggentic_RAG
mkdir -p data/travel_docs
# 将文档放入 data/travel_docs/
```

```python
from travel_agent.tools.rag_tool import TravelRAG

rag = TravelRAG()
rag.build_knowledge_base(
    data_dir="./data/travel_docs",
    force_recreate=False  # False=追加，True=重建
)
```

#### 方式3：FastAPI 后端上传

通过 API 端点上传文档（需要认证）：
```
POST /api/knowledge/upload
```

### 删除数据

```python
# 删除指定文件
rag.delete_by_source("data/travel_docs/suzhou_guide.txt")

# 重建整个数据库
rag.build_knowledge_base("./data/travel_docs", force_recreate=True)
```

---

## 项目结构

```
travel-planning-agent-main/
├── app.py                              # Streamlit UI 入口
├── check_mcp_health.py                 # MCP 健康检查工具
├── README.md
├── LICENSE
│
├── aggentic_RAG/                       # Python 后端包
│   ├── .env                            # 环境变量（需自行创建）
│   ├── .env.example                    # 环境变量模板
│   ├── requirements.txt                # Python 依赖
│   ├── setup.py                        # 包安装脚本 (pip install -e .)
│   ├── start_backend.py                # FastAPI 启动器
│   │
│   ├── travel_agent/                   # 核心 Agent 代码
│   │   ├── __init__.py
│   │   ├── app.py                      # Agent 入口（run_travel_agent）
│   │   │
│   │   ├── config/                     # 配置
│   │   │   ├── settings.py             # 全局配置（模型、路径、参数）
│   │   │   ├── prompts.py              # 所有 LLM Prompt 模板
│   │   │   └── servers_config.json     # MCP 服务器配置
│   │   │
│   │   ├── core/                       # 核心执行引擎
│   │   │   └── agent_executor.py       # AgentExecutor（无递归限制编排）
│   │   │
│   │   ├── graph/                      # LangGraph 工作流
│   │   │   ├── state.py                # TravelPlanState 类型定义
│   │   │   ├── workflow.py             # StateGraph 构建 + ReAct 路由
│   │   │   └── nodes.py                # 所有节点实现（planner/RAG/tools/synthesizer）
│   │   │
│   │   └── tools/                      # 工具集
│   │       ├── mcp_tools.py            # MCP 工具管理器（连接/重试/SSE）
│   │       ├── rag_tool.py             # ChromaDB RAG 检索
│   │       ├── r1_tool.py              # 深度分析客户端（OpenAI 兼容）
│   │       ├── tool_registry.py        # 工具注册表（JSON Schema）
│   │       ├── tool_cache.py           # 工具调用缓存（MD5 + TTL）
│   │       └── resilient_mcp.py        # 弹性 MCP 调用（超时/重试/降级）
│   │
│   ├── data/                           # 数据目录
│   │   ├── travel_docs/                # 旅游攻略原始文档
│   │   └── travel_vectordb/            # ChromaDB 向量数据库
│   │
│   └── backend/                        # FastAPI 后端
│       ├── requirements.txt
│       ├── run.py                      # Uvicorn 启动入口 (port 8765)
│       └── app/
│           ├── main.py                 # FastAPI 应用工厂
│           ├── database.py             # SQLite 初始化
│           ├── auth.py                 # JWT + PBKDF2 认证
│           ├── schemas/                # Pydantic 数据模型
│           │   ├── plan.py             # 规划请求/响应
│           │   ├── auth.py             # 认证请求/响应
│           │   └── knowledge.py        # 知识库统计
│           ├── services/               # 业务逻辑
│           │   ├── agent_service.py    # Agent 任务管理 + SSE 流
│           │   ├── knowledge_service.py
│           │   ├── profile_service.py  # 用户偏好注入
│           │   └── user_knowledge_service.py
│           └── routers/                # API 路由
│               ├── plan.py             # 规划端点
│               ├── sse.py              # SSE 实时流
│               ├── modify.py           # 方案修改/多方案对比
│               ├── auth.py             # 注册/登录
│               ├── sessions.py         # 会话管理
│               ├── knowledge.py        # 知识库管理
│               ├── user_knowledge.py   # 用户知识库
│               ├── profile.py          # 用户偏好
│               ├── config.py           # 系统配置
│               └── health.py           # 健康检查
│
└── frontend/                           # Vue 3 前端
    ├── package.json
    ├── index.html
    ├── dist/                           # 生产构建（由 FastAPI 托管）
    └── src/                            # Vue 源码
```

**核心文件说明**：
- `app.py`（根目录）：Streamlit UI，适合调试和演示
- `nodes.py`：所有工作流节点实现（planner、RAG、交通、天气、合成器等）
- `mcp_tools.py`：MCP 连接管理，带自动重试和 SSE 中断保护
- `settings.py`：模型配置 — 两个实例均使用 `deepseek-v4-flash`
- `agent_executor.py`：替代编排引擎，用于 FastAPI 后端
- `backend/`：FastAPI 生产后端，含用户系统、SSE 流、会话管理
- `frontend/`：Vue 3 SPA 前端

---

## API 接口

FastAPI 后端提供以下 REST API（端口 8765）：

### 规划
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/plan` | 同步规划 |
| POST | `/api/plan/stream` | 异步规划（返回 task_id） |
| GET | `/api/plan/stream/{task_id}` | SSE 事件流 |
| GET | `/api/plan/result/{task_id}` | 轮询结果 |
| POST | `/api/plan/modify` | 修改方案 |
| POST | `/api/plan/multi-plan` | 多方案对比 |

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户 |

### 会话 & 偏好 & 知识库
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/sessions` | 会话管理 |
| GET/PUT | `/api/profile` | 用户偏好 |
| POST/GET/DELETE | `/api/knowledge` | 系统知识库 |
| POST/GET/DELETE | `/api/user-knowledge` | 用户知识库 |

### 系统
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/config` | 系统配置 |

---

## 故障排查

### 1. 后端启动失败

**问题**：`ModuleNotFoundError: No module named 'travel_agent'`

**解决**：
```bash
cd aggentic_RAG
pip install -e .
```

### 2. 向量数据库为空

**问题**：简单查询返回"未找到相关信息"

**解决**：导入旅游攻略文档
```python
from travel_agent.tools.rag_tool import TravelRAG
rag = TravelRAG()
rag.build_knowledge_base("./data/travel_docs")
```

### 3. MCP 工具调用失败

**问题**：火车票、天气查询返回错误

**解决**：
1. 检查 MCP 服务器是否可访问
2. 运行健康检查：`python check_mcp_health.py`
3. 查看 ModelScope MCP 服务状态
4. 查看终端日志排查具体错误

### 4. Streamlit 启动失败

**问题**：Streamlit 无法启动或报错

**解决**：
1. 确认已安装 Streamlit：`pip install streamlit`
2. 检查端口 8501 是否被占用
3. 尝试指定端口：`streamlit run app.py --server.port 8502`

### 5. Windows 编码问题

**问题**：终端输出 emoji 报 `UnicodeEncodeError`（GBK 编码）

**解决**：FastAPI 后端已内置 UTF-8 编码修复。Streamlit 模式下，设置环境变量：
```bash
set PYTHONIOENCODING=utf-8
streamlit run app.py
```

---

## 开发说明

### 修改 Prompt

编辑 `aggentic_RAG/travel_agent/config/prompts.py`：

```python
PLANNER_SYSTEM_PROMPT = """你的自定义提示词..."""
SYNTHESIZER_PROMPT_TEMPLATE = """你的自定义提示词..."""
```

### 调整模型参数

编辑 `aggentic_RAG/travel_agent/config/settings.py`：

```python
# 切换对话模型（默认为百炼 deepseek-v4-flash）
QWEN3_MODEL = "deepseek-v4-flash"

# 切换深度分析模型
R1_MODEL = "deepseek-v4-flash"

# RAG 参数
RAG_CHUNK_SIZE = 500
RAG_SEARCH_K = 3

# 模型温度
QWEN3_TEMPERATURE = 0.7   # 对话实例
R1_TEMPERATURE = 0.1      # 分析实例
```

### 添加新工具

1. 在 `tool_registry.py` 中注册：
```python
ToolDefinition(
    name="my_new_tool",
    description="新工具的功能描述",
    parameters={...},
    tool_type="mcp",
    server_name="Your Server",
    mcp_tool_name="tool_name_in_mcp"
)
```

2. 如需自定义处理逻辑，在 `nodes.py` 的 `action_node` 中添加分支

---

## 许可证

本项目采用 MIT 许可证。

---

## 联系方式

该项目 Created by Alex，如有问题或建议，请提交 Issue 或联系项目维护者。

**项目地址**: [https://github.com/alexlmoney83-oss/travel-planning-agent](https://github.com/alexlmoney83-oss/travel-planning-agent)
