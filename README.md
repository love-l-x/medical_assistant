# 智能医疗助手 - 后端

基于 LangChain 1.0.3 + LangGraph 1.0.2 的多智能体医疗助手系统

## 项目概述

智能医疗助手后端是一个基于 FastAPI 构建的 RESTful API 服务，整合了 LangChain、LangGraph 等 AI 技术，提供多智能体医疗咨询、文档管理、记忆持久化等功能。

## 技术栈

- **LangChain**: 1.0.3
- **LangGraph**: 1.0.2
- **Python**: 3.12.x
- **FastAPI**: 最新
- **MySQL**: 用户认证数据库
- **PostgreSQL**: 记忆系统 + 会话管理（3个独立数据库）
- **Tavily API**: 联网搜索
- **LangSmith**: 可观测性平台

## 项目结构

```
backend/
├── app/
│   ├── agents/              # 智能体模块
│   │   ├── __init__.py
│   │   ├── base.py          # 模型初始化（ChatOpenAI）
│   │   └── multi_agent.py   # 多智能体系统（4个角色）
│   │
│   ├── api/                 # API 接口
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证接口（登录/注册）
│   │   ├── chat.py          # 聊天接口
│   │   ├── conversations.py # 会话管理接口
│   │   ├── documents.py     # 文档上传接口
│   │   └── preferences.py   # 偏好设置接口
│   │
│   ├── mcp/                 # MCP 工具
│   │   ├── __init__.py
│   │   └── mysql_mcp.py     # MySQL 数据查询工具
│   │
│   ├── memory/              # 记忆管理
│   │   ├── __init__.py
│   │   └── memory_manager.py # 记忆系统初始化
│   │
│   ├── rag/                 # RAG 模块
│   │   ├── __init__.py
│   │   └── document_processor.py # 文档处理器
│   │
│   ├── schemas/             # Pydantic 模型
│   │   ├── __init__.py
│   │   └── user.py          # 用户模型
│   │
│   ├── config.py            # 配置管理（读取.env）
│   ├── database.py          # MySQL 数据库连接
│   ├── database_postgres.py # PostgreSQL 数据库连接
│   ├── models.py            # MySQL 数据模型
│   └── models_postgres.py   # PostgreSQL 数据模型
│
├── uploads/                 # 上传的医疗文档
│
├── .env                     # 环境变量（敏感信息）
├── .env.example             # 环境变量示例
├── main.py                  # 应用入口
├── requirements.txt         # Python 依赖
├── database_init.sql        # 数据库初始化脚本
├── start_server.bat         # Windows 启动脚本
└── stop_server.bat          # Windows 停止脚本
```

## 快速开始

### 1. 创建数据库

**MySQL**（用户认证）：
```sql
CREATE DATABASE medical_assistant;
```

**PostgreSQL**（记忆和会话）：
```sql
CREATE DATABASE smart_short;    -- 短记忆（对话历史）
CREATE DATABASE smart_long;     -- 长记忆（用户偏好、医疗记录）
CREATE DATABASE smart_session;  -- 会话管理
```

或执行初始化脚本：
```bash
psql -h localhost -U postgres -f database_init.sql
```

### 2. 配置环境变量

复制示例文件并编辑：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key 和数据库连接信息：

```env
# API Keys
DASHSCOPE_API_KEY=your_api_key
LANGCHAIN_API_KEY=your_langsmith_key
TAVILY_API_KEY=your_tavily_key

# Model Settings
MODEL_NAME=qwen-plus
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# MySQL（用户认证）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=medical_assistant

# PostgreSQL（短记忆）
POSTGRES_SHORT_HOST=localhost
POSTGRES_SHORT_PORT=5432
POSTGRES_SHORT_USER=postgres
POSTGRES_SHORT_PASSWORD=your_password
POSTGRES_SHORT_DB=smart_short

# PostgreSQL（长记忆）
POSTGRES_LONG_HOST=localhost
POSTGRES_LONG_PORT=5432
POSTGRES_LONG_USER=postgres
POSTGRES_LONG_PASSWORD=your_password
POSTGRES_LONG_DB=smart_long

# PostgreSQL（会话管理）
POSTGRES_SESSION_HOST=localhost
POSTGRES_SESSION_PORT=5432
POSTGRES_SESSION_USER=postgres
POSTGRES_SESSION_PASSWORD=your_password
POSTGRES_SESSION_DB=smart_session

# JWT Settings
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 启动服务

```bash
python main.py
```

或使用 Windows 批处理脚本：
```bash
start_server.bat
```

服务将在 http://localhost:8000 启动

访问 http://localhost:8000/docs 查看 API 文档

## 核心功能

### 1. 多智能体系统

**架构**：hub-and-spoke（中心辐射型）

**智能体角色**：

1. **私人医疗顾问**（supervisor）
   - 中心节点，负责路由判断
   - 检查用户基本信息
   - 引导就诊流程
   - 整合其他智能体结果

2. **主治医生**（doctor）
   - 诊断和治疗方案制定
   - 分析体检报告和症状
   - 开具处方和治疗建议

3. **体检员**（examiner）
   - 收集用户健康信息
   - 生成体检报告
   - 建议用户上传医疗文档

4. **药师**（pharmacist）
   - 药品信息咨询
   - 用药指导
   - 处方安全审核

**工作流程**：
```
用户消息 → 私人医疗顾问（LLM 路由判断） → 
  ├→ 体检员（健康信息收集）
  ├→ 主治医生（诊断治疗）
  └→ 药师（用药指导）
```

### 2. 记忆系统

**短记忆（PostgresSaver）**：
- 数据库：`smart_short`
- 用途：保存当前会话的对话历史
- 实现：`langgraph.checkpoint.postgres.PostgresSaver`
- 特点：每个会话独立 thread_id，支持会话切换

**长记忆（PostgresStore）**：
- 数据库：`smart_long`
- 用途：保存用户偏好、医疗记录
- 实现：`langgraph.store.postgres.PostgresStore`
- 命名空间：
  - `user_preferences/{user_id}`：用户偏好
  - `user_medical_history/{user_id}`：医疗历史
  - `user_medical_records/{user_id}`：医疗文档记录

**记忆协同**：
- 短记忆用于当前会话的上下文保持
- 长记忆用于跨会话的个性化服务
- 两者使用不同的 PostgreSQL 数据库，互不干扰

### 3. 医疗文档管理

**上传流程**：
1. 接收 PDF 文件（`POST /documents/upload`）
2. 保存原始文件到 `./uploads/` 目录
3. 使用 LLM 提取结构化医疗信息
4. 保存到长记忆（PostgresStore）
5. 保存文档元数据到 `smart_session.medical_documents` 表

**信息提取**：
- 使用 `document_extractor.py` 中的 LLM 提取器
- 提取字段：
  - 基本信息（姓名、年龄、性别、联系方式）
  - 医疗历史（既往病史、手术史）
  - 过敏史（药物、食物）
  - 家族史
  - 生活习惯（吸烟、饮酒、运动等）
- 支持中英文键名映射
- 智能过滤 None 值

**AI 自动感知**：
- 文档上传后，前端自动发送消息给 AI
- 后端检测到文档上传消息
- supervisor 优先路由至体检员
- 体检员读取长记忆中的文档信息
- AI 基于文档内容提供个性化回复

### 4. 用户认证

**JWT Token 认证**：
- 用户登录返回 JWT Token
- Token 包含用户 ID 和过期时间
- 后续请求在 Header 中携带 Token

**数据库**：
- MySQL 存储用户账号信息
- 密码使用 bcrypt 加密

### 5. 会话管理

**功能**：
- 创建新会话
- 获取会话列表
- 获取会话详情（包含历史消息）
- 删除会话

**存储**：
- PostgreSQL `smart_session` 数据库
- 表：`conversations`、`messages`

## API 接口

### 认证接口

#### POST /auth/token

用户登录

**请求**：
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

#### POST /auth/register

用户注册

**请求**：
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com"
}
```

### 聊天接口

#### POST /chat/send

发送消息，获取 AI 回复（非流式）

**请求**：
```json
{
  "user_id": "user_1",
  "message": "我最近总是头疼",
  "conversation_id": "conv_abc123"
}
```

**响应**：
```json
{
  "reply": "您好！请问您的头疼持续多久了？...",
  "conversation_id": "conv_abc123"
}
```

### 会话管理接口

#### GET /conversations/list

获取会话列表

**请求**：
```
GET /conversations/list?user_id=user_1
```

**响应**：
```json
[
  {
    "id": "conv_abc123",
    "title": "头疼咨询",
    "created_at": "2026-04-14T10:00:00"
  }
]
```

#### GET /conversations/get

获取会话详情

**请求**：
```
GET /conversations/get?conversation_id=conv_abc123
```

**响应**：
```json
{
  "id": "conv_abc123",
  "title": "头疼咨询",
  "messages": [
    {
      "role": "user",
      "content": "我最近总是头疼",
      "timestamp": "2026-04-14T10:00:00"
    },
    {
      "role": "assistant",
      "content": "您好！请问您的头疼持续多久了？...",
      "timestamp": "2026-04-14T10:00:05"
    }
  ]
}
```

#### POST /conversations/create

创建新会话

**请求**：
```json
{
  "user_id": "user_1",
  "title": "新会话"
}
```

#### DELETE /conversations/delete

删除会话

**请求**：
```
DELETE /conversations/delete?conversation_id=conv_abc123
```

### 文档管理接口

#### POST /documents/upload

上传医疗文档

**请求**：
```
Content-Type: multipart/form-data

file: <PDF文件>
document_type: 病历本
user_id: user_1
```

**响应**：
```json
{
  "filename": "medical_report.pdf",
  "document_type": "病历本",
  "upload_time": "2026-04-14T10:00:00",
  "status": "processed",
  "extracted_fields": 6
}
```

### 偏好设置接口

#### POST /preferences/save

保存用户偏好

**请求**：
```json
{
  "user_id": "user_1",
  "key": "preferred_style",
  "value": "简洁"
}
```

#### GET /preferences/get

获取用户偏好

**请求**：
```
GET /preferences/get?user_id=user_1
```

**响应**：
```json
{
  "preferred_style": "简洁",
  "preferred_address": "北京市"
}
```

## 开发说明

### 添加新的 API 接口

1. 在 `app/api/` 目录创建新文件（如 `new_api.py`）
2. 在 `main.py` 中注册路由：
   ```python
   from app.api.new_api import router as new_api_router
   app.include_router(new_api_router, prefix="/new", tags=["New"])
   ```

### 添加新的智能体

1. 在 `app/agents/multi_agent.py` 中定义节点函数：
   ```python
   def new_agent_node(state):
       # 实现智能体逻辑
       return {"messages": [AIMessage(content="...")]}
   ```

2. 在 `create_medical_agent_system()` 中添加节点和边：
   ```python
   workflow.add_node("new_agent", new_agent_node)
   workflow.add_conditional_edges("supervisor", route_message, {"new_agent": "new_agent"})
   ```

### 配置管理

- 所有配置在 `.env` 文件
- 通过 `app/config.py` 读取
- 使用 `from app.config import settings` 导入

### 数据库模型

**MySQL 模型**（`app/models.py`）：
- `User`：用户账号信息

**PostgreSQL 模型**（`app/models_postgres.py`）：
- `Conversation`：会话信息
- `Message`：消息记录
- `MedicalDocument`：文档元数据

## 故障排查

### 常见问题

1. **端口 8000 被占用**
   ```bash
   # 查看占用端口的进程
   netstat -ano | findstr :8000
   # 结束进程
   taskkill /F /PID <进程ID>
   ```

2. **数据库连接失败**
   - 检查 MySQL 和 PostgreSQL 服务是否启动
   - 检查 `.env` 文件中的数据库连接信息
   - 确认数据库已创建

3. **长记忆读取失败**
   - 检查 `smart_long` 数据库是否可访问
   - 查看记忆系统初始化日志
   - 确认 user_id 格式正确

4. **文档提取失败**
   - 检查 PDF 文件是否损坏
   - 查看 LLM API 调用日志
   - 确认 Tavily API Key 有效

## 测试

### 单元测试

运行测试：
```bash
pytest tests/
```

### API 测试

使用 Postman 或 curl 测试 API：
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 部署

### 生产环境部署

1. **使用 Gunicorn + Uvicorn**
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker -w 4 main:app
   ```

2. **配置 Nginx 反向代理**
   ```nginx
   location /api/ {
       proxy_pass http://localhost:8000/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

3. **启用 HTTPS**
   - 使用 Let's Encrypt 免费证书
   - 配置 SSL/TLS

4. **数据库优化**
   - 配置连接池
   - 定期备份
   - 监控性能

## 许可证

MIT License

---

**版本**：v2.0  
**更新日期**：2026-04-14
