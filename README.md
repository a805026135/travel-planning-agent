# ✈️ 智能旅行规划助手

基于 **Vue3 + FastAPI + LangGraph Agent** 的智能旅行规划系统。支持用户注册登录、多轮对话、偏好学习、实时 MCP 工具调用（12306 火车票 / 高德地图 / 航班 / 黄历）和 ChromaDB 知识库检索。

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│  Vue3 前端 (:5173)                                           │
│  ┌──────────┬──────────┬──────────┬──────────┐              │
│  │ 旅行规划  │ 我的规划  │ 知识库   │ 系统配置  │              │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┘              │
│       │ HTTP/SSE │          │          │                    │
├───────┴──────────┴──────────┴──────────┴────────────────────┤
│  FastAPI 后端 (:8765)                                        │
│  ┌─────────┬──────────┬───────────┬──────────────────────┐  │
│  │ /auth   │ /plan    │ /sessions │ /knowledge           │  │
│  │ JWT认证 │ /stream  │ 会话管理   │ 系统+个人知识库       │  │
│  │         │ /modify  │ /profile  │ /config              │  │
│  └─────────┴──────────┴───────────┴──────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────────────┐   │
│  │  AgentService → LangGraph                            │   │
│  │  Planner →  Strategy → ReAct Loop → Synthesizer    │   │
│  └──────────────────────────────────────────────────────┘   │
│          │          │          │           │                │
│  ┌───────┴──┐ ┌────┴────┐ ┌──┴─────┐ ┌──┴──────────┐      │
│  │ 12306    │ │ 高德地图 │ │ 黄历   │ │ 航班查询     │      │
│  │ (火车票) │ │(天气/酒店│ │(吉日)  │ │             │      │
│  │          │ │ /路线)    │ │        │ │             │      │
│  └──────────┘ └─────────┘ └────────┘ └─────────────┘      │
│           MCP 工具 (Model Context Protocol)                  │
├─────────────────────────────────────────────────────────────┤
│  数据层: SQLite(用户/会话/画像) + ChromaDB(知识库) + 内存缓存 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 功能清单

### 🔐 用户系统
- JWT 认证（注册 / 登录 / 用户信息）
- 管理员权限控制（`ADMIN_USERS` 环境变量）
- 演示账号快速登录 + 密码强度指示

### ✈️ 旅行规划
- **结构化输入**：600+ 城市选择器、日历日期、预算、备注
- **SSE 实时进度**：图标化时间轴（🤖/🚆/☀️/🏨）+ 状态标记（✅/⚠️）
- **双模型协作**：主模型提取需求 + DeepSeek R1 深度推理
- **预填数据注入**：结构化输入直接注入 Agent state，跳过 LLM 提取
- **多轮对话**：会话历史自动传递，新消息结合上文生成更新方案

### 📋 会话管理
- 卡片网格列表 + 搜索排序
- 继续上次规划（自动恢复表单和结果）
- 上下文感知增量修改

### 📚 知识库
- 系统知识库（公开）+ 个人知识库（ChromaDB 按用户隔离）
- 拖拽上传（TXT/MD/PDF/CSV）+ 进度条
- 按来源删除 + 预览

### 👤 用户画像
- 自动学习：交通方式 / 酒店等级 / 景点类型 / 预算范围 / 旅行风格 / 常住城市
- 偏好注入：新规划时自动应用到方案生成

### 🛠️ 工具增强
- **缓存**：同一会话内 `(tool, params_hash)` 缓存
- **降级**：MCP 超时重试 → Fallback → 不阻断流程
- **并行**：无依赖工具并发调用 (`asyncio.gather`)

### 🎨 UI/UX
- 现代设计系统（CSS 变量、毛玻璃导航栏、响应式布局）
- Toast 全局通知 + EmptyState 统一组件
- 每日行程折叠卡片 + 多方案对比标签页
- 移动端底部标签栏

---

## 🚀 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 18

### 1. 安装后端

```bash
cd travel-planning-agent-main/aggentic_RAG
pip install -r requirements.txt
pip install -e .
```

### 2. 配置环境变量

在 `aggentic_RAG/` 目录创建 `.env` 文件：

```env
# 必填：阿里云百炼 API Key
DASHSCOPE_API_KEY=sk-your-key-here

# 可选
JWT_SECRET=your-secret-key
ADMIN_USERS=admin,your-username
CORS_ORIGINS=http://localhost:5173
```

> **获取 API Key**: [阿里云百炼控制台](https://dashscope.aliyun.com/)

### 3. 配置 MCP 服务器

编辑 `travel_agent/config/servers_config.json`：

```json
{
  "mcp_servers": [
    {"name": "12306 Server", "url": "https://your-12306-mcp/sse", "transport": "streamable_http"},
    {"name": "Gaode Server", "url": "https://your-gaode-mcp/sse", "transport": "streamable_http"},
    {"name": "bazi Server", "url": "https://your-bazi-mcp/sse", "transport": "streamable_http"},
    {"name": "flight Server", "url": "https://your-flight-mcp/sse", "transport": "streamable_http"}
  ]
}
```

### 4. 安装前端

```bash
cd frontend
npm install
```

### 5. 启动服务

**终端 1 — 后端（端口 8765）：**
```bash
cd aggentic_RAG
python start_backend.py
```

**终端 2 — 前端（端口 5173）：**
```bash
cd aggentic_RAG/frontend
npm run dev
```

浏览器访问 **`http://localhost:5173`**

---

## 📡 API 文档

启动后端后访问 Swagger：**`http://localhost:8765/docs`**

### 认证

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/api/auth/register` | POST | - | 注册 |
| `/api/auth/login` | POST | - | 登录，返回 JWT |
| `/api/auth/me` | GET | Bearer | 当前用户信息 |
| `/api/auth/admin/check` | GET | Bearer | 是否管理员 |

### 规划

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/api/plan` | POST | 可选 | 同步规划 |
| `/api/plan/stream` | POST | 可选 | 流式规划，返回 task_id |
| `/api/plan/stream/{task_id}` | GET | - | SSE 实时进度 |
| `/api/plan/result/{task_id}` | GET | - | 轮询结果 |
| `/api/plan/modify` | POST | Bearer | 局部修改 |
| `/api/plan/multi-plan` | POST | - | 多方案对比 |

### 会话

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/api/sessions` | GET | Bearer | 列出我的会话 |
| `/api/sessions` | POST | Bearer | 创建会话 |
| `/api/sessions/{id}` | GET/PATCH/DELETE | Bearer | 详情/重命名/删除 |

### 知识库

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/api/knowledge/stats` | GET | - | 系统知识库统计（公开） |
| `/api/knowledge/upload` | POST | Admin | 上传到系统知识库 |
| `/api/knowledge/source` | DELETE | Admin | 删除系统知识库源 |
| `/api/user/knowledge/stats` | GET | Bearer | 个人知识库统计 |
| `/api/user/knowledge/upload` | POST | Bearer | 上传到个人知识库 |
| `/api/user/knowledge/source` | DELETE | Bearer | 删除个人知识库源 |

### 其他

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/api/profile` | GET/PUT | Bearer | 用户画像 |
| `/api/config` | GET | - | 系统配置（不含 API Key） |
| `/api/health` | GET | - | 健康检查 |

---

## 📁 项目结构

```
aggentic_RAG/
├── start_backend.py              # 后端启动脚本（热重载）
├── requirements.txt
├── .env                          # 环境变量（API Key 等）
│
├── backend/
│   ├── run.py                    # 后端入口
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI 应用工厂 + 路由挂载
│       ├── database.py           # SQLite (users/sessions/messages/plans/profile)
│       ├── auth.py               # JWT + PBKDF2 密码哈希
│       ├── routers/              # API 路由层
│       │   ├── auth.py           # 注册/登录/管理员检查
│       │   ├── plan.py           # 同步+流式规划
│       │   ├── sse.py            # SSE 事件流
│       │   ├── modify.py         # 局部修改+多方案
│       │   ├── sessions.py       # 会话 CRUD
│       │   ├── knowledge.py      # 系统知识库
│       │   ├── user_knowledge.py # 个人知识库
│       │   ├── profile.py        # 用户画像
│       │   ├── config.py         # 系统配置
│       │   └── health.py         # 健康检查
│       ├── schemas/              # Pydantic 数据模型
│       └── services/             # 业务逻辑层
│           ├── agent_service.py       # Agent 任务管理+SSE队列+画像注入
│           ├── knowledge_service.py   # 系统知识库服务
│           ├── user_knowledge_service.py
│           └── profile_service.py     # 偏好学习+注入+会话检索
│
├── travel_agent/                 # LangGraph Agent 核心
│   ├── app.py                    # run_travel_agent 入口（支持 prefill/history）
│   ├── core/
│   │   └── agent_executor.py     # Agent 执行引擎（5阶段+ReAct循环）
│   ├── graph/
│   │   ├── state.py              # TravelPlanState (85字段 TypedDict)
│   │   ├── workflow.py           # LangGraph 工作流 DAG
│   │   └── nodes.py              # 所有节点 (~3100行): planner/R1/react/synthesizer
│   ├── config/
│   │   ├── prompts.py            # Prompt 模板（中文+结构化输出）
│   │   ├── settings.py           # 全局配置（env变量）
│   │   └── servers_config.json   # MCP 服务器配置
│   └── tools/
│       ├── mcp_tools.py          # MCP 连接管理（SSE/HTTP）
│       ├── tool_registry.py      # 工具注册表（11个工具定义）
│       ├── rag_tool.py           # ChromaDB 向量检索
│       ├── tool_cache.py         # 工具结果缓存（内存）
│       └── resilient_mcp.py      # 弹性MCP调用（超时+重试+降级）
│
├── frontend/                     # Vue3 前端
│   ├── package.json
│   ├── vite.config.js            # 代理 /api → :8765
│   └── src/
│       ├── App.vue               # 根组件（路由+Toast+移动导航）
│       ├── main.js               # 应用入口+Router挂载
│       ├── assets/main.css       # 设计系统（CSS变量/组件/动画）
│       ├── router/index.js       # 6条路由
│       ├── services/api.js       # Axios实例+SSE helper+Auth拦截器
│       ├── composables/          # 状态管理
│       │   ├── useAuth.js        # 认证+管理员检查
│       │   ├── useSSE.js         # SSE生命周期
│       │   ├── useToast.js       # Toast通知
│       │   └── useProfile.js     # 用户画像
│       ├── views/                # 页面
│       │   ├── HomeView.vue      # 旅行规划（表单+SSE+结果+修改气泡）
│       │   ├── SessionsView.vue  # 我的规划（卡片网格+搜索排序）
│       │   ├── KnowledgeBaseView.vue
│       │   ├── ConfigView.vue    # 系统配置
│       │   ├── LoginView.vue     # 登录（演示账号）
│       │   └── RegisterView.vue  # 注册（密码强度）
│       └── components/
│           ├── AppHeader.vue     # 导航栏（毛玻璃+图标+头像）
│           ├── CityPicker.vue    # 城市选择器（600+城市×省份分组）
│           ├── QueryInput.vue    # 结构化表单
│           ├── StatusTimeline.vue# SSE进度时间轴
│           ├── PlanMeta.vue      # 行程摘要
│           ├── PlanDayCards.vue  # 每日折叠卡片+修改弹窗
│           ├── MultiPlanView.vue # 多方案对比标签页
│           ├── EmptyState.vue    # 空状态统一组件
│           └── ToastContainer.vue# 全局Toast通知
│
└── data/
    ├── travel_docs/              # 旅游攻略文档
    └── travel_vectordb/          # ChromaDB 持久化
```

---

## 🗄️ 数据库

SQLite `backend/data/app.db`：

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `users` | 用户 | id, username, password_hash |
| `sessions` | 会话 | id, user_id, title, updated_at |
| `session_messages` | 消息 | id, session_id, role, content, meta |
| `plans` | 规划记录 | id, user_id, session_id, query, travel_plan |
| `user_profile` | 用户画像 | user_id, preferred_transport, preferred_hotel_level, budget_range, travel_style_tags, common_departure_city |

---

## ⚙️ 环境变量

在 `aggentic_RAG/.env` 中配置：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DASHSCOPE_API_KEY` | 是 | - | 阿里云百炼 API Key |
| `QWEN3_MODEL` | 否 | `deepseek-v4-flash` | 主模型 |
| `R1_MODEL` | 否 | `deepseek-v4-flash` | 深度推理模型 |
| `JWT_SECRET` | 否 | 随机生成 | JWT 签名密钥 |
| `ADMIN_USERS` | 否 | `admin` | 管理员用户列表 |
| `CORS_ORIGINS` | 否 | `localhost:5173` | CORS 来源 |

---

## 🧠 Agent 工作流

```
用户输入
  │
  ├── prefill 检测 → 有结构化数据 → 跳过 LLM 提取
  │
  ├── Planner 节点 → 提取 destination/origin/days/budget/date/preferences
  │                     └── 判断 query_mode: "simple" | "full"
  │
  ├── [简单查询] → RAG/POI → Synthesizer → 景点推荐
  │
  └── [完整规划]
        │
        ├── inject_profile → 注入用户画像偏好
        │
        ├── R1 Strategy → 生成 query_plan（多步工具调用计划）
        │
        ├── ReAct Loop (≤15步)
        │   ├── Thought → 决策下一步工具
        │   ├── Action → 调用 MCP（含缓存+降级+并行优化）
        │   └── Observation → 评估结果
        │
        ├── R1 Optimization → 预算/风险/替代方案
        │
        └── Synthesizer → Markdown 旅行方案
              │
              ├── update_profile → 学习偏好
              └── save_session → 保存会话消息
```

---

## 🛠️ 常见问题

### MCP 工具调用失败

检查 MCP 服务器状态：
```bash
python check_mcp_health.py
```

### 知识库为空

系统知识库需要管理员在后台上传文档，或通过前端知识库页面上传。

### Windows GBK 编码

后端已内置 `sys.stdout.reconfigure(encoding='utf-8')` 修复。如仍有问题：
```bash
set PYTHONIOENCODING=utf-8 && python start_backend.py
```

### 端口冲突

修改 `start_backend.py` 和 `frontend/vite.config.js` 中的端口号。

---
