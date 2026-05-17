# MemoAgent 系统级升级设计规格

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 对 MemoAgent 进行核心优化（实体提取、LLM 重试降级、System Prompt、反思完整性）+ API 重构（Orchestrator 拆分 + FastAPI）+ React Web 前端 + Docker 部署

**Architecture:** 面向 API 重构后端，将 Orchestrator 拆分为无状态 AgentCore + 会话管理 SessionManager，暴露 FastAPI REST/WebSocket 端点。React 前端四个页面模块（对话、知识图谱、记忆状态、反思日志）通过 API 交互。Docker Compose 一键部署。

**Tech Stack:** Python 3.9 / FastAPI / Pydantic / React 18 / TypeScript / Vite / Tailwind CSS / react-force-graph-2d / Zustand / Docker Compose

---

## 1. 子项目分解

本次升级拆为两个按序实施的子项目：

**子项目 1：核心优化 + API 重构**（后端）
- 修复实体提取质量
- LLM 重试 + 优雅降级
- System Prompt 与角色定义
- 反思流水线完整性
- Orchestrator 拆分为 AgentCore + SessionManager
- Pydantic API 数据模型
- FastAPI 应用骨架 + WebSocket
- CLI 保留为替代入口

**子项目 2：Web 前端 + Docker**
- React 前端四个页面模块
- FastAPI 完整 API 端点实现
- Docker + docker-compose

---

## 2. 项目结构

```
memoAgent/
├── src/memo_agent/
│   ├── core/                    # 纯逻辑层（Orchestrator 拆分产物）
│   │   ├── __init__.py
│   │   ├── agent.py             # AgentCore - 推理 + 反思 + 检索
│   │   ├── session.py           # SessionManager - 会话生命周期
│   │   ├── llm_caller.py        # LLMCaller - 重试 + 降级封装
│   │   └── system_prompt.py     # System Prompt 模板
│   ├── memory/                  # 三级记忆（已有，修复）
│   │   ├── __init__.py
│   │   ├── working.py           # 加 turn limit
│   │   ├── episodic.py          # 已有
│   │   └── semantic.py          # 已有
│   ├── reflection/              # 反思流水线（已有，增强）
│   │   ├── __init__.py
│   │   ├── detector.py          # 已有
│   │   ├── reflector.py         # 修实体提取：删除 _extract_entities_from_hint
│   │   └── kg_updater.py        # 增强 JSONL 日志
│   ├── retrieval/               # 检索（已有）
│   │   ├── __init__.py
│   │   ├── entity_extractor.py  # 已有
│   │   └── context_assembler.py # 已有，加 System Prompt 插入
│   ├── api/                     # 新增 API 层
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI 应用
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py          # 对话端点 + WebSocket
│   │   │   ├── memory.py        # 记忆状态查询
│   │   │   ├── knowledge.py     # 知识图谱 CRUD
│   │   │   └── reflection.py    # 反思日志查询
│   │   └── schemas.py           # Pydantic 数据模型
│   ├── config.py                # 扩展配置
│   ├── models.py                # 已有
│   └── cli.py                   # 保留 CLI 入口，改用 SessionManager
├── frontend/                    # React 前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   ├── client.ts        # axios 实例 + WebSocket 管理
│       │   └── types.ts         # API 类型定义
│       ├── store/
│       │   └── useStore.ts      # Zustand 全局状态
│       ├── components/
│       │   ├── Layout.tsx        # 左侧导航 + 右侧内容
│       │   ├── Sidebar.tsx
│       │   └── StatusBar.tsx     # 底部状态栏
│       └── pages/
│           ├── ChatPage.tsx      # 对话页面
│           ├── KnowledgePage.tsx # 知识图谱页面
│           ├── MemoryPage.tsx    # 记忆状态页面
│           └── ReflectionPage.tsx # 反思日志页面
├── data/                        # 持久化数据（.gitignore）
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── nginx.conf
├── pyproject.toml
└── tests/                       # 后端测试
    ├── test_core.py
    ├── test_llm_caller.py
    ├── test_system_prompt.py
    ├── test_api/
    │   ├── test_chat.py
    │   ├── test_memory.py
    │   ├── test_knowledge.py
    │   └── test_reflection.py
    └── test_integration.py      # 更新集成测试
```

---

## 3. 核心优化

### 3.1 实体提取质量修复

**问题：** `Reflector._extract_entities_from_hint()` 对中文做词分割，产生垃圾实体（如"药物重定位在我"）。

**方案：**
- 删除 `Reflector._extract_entities_from_hint()` 方法
- `Reflector.reflect()` 签名改为 `reflect(correction_hint: str, source_entities: List[str]) -> Guideline`，实体由外部传入
- `AgentCore` 在反思流程中先调用 `EntityExtractor.extract()` 从用户纠正文本提取实体，再传给 `Reflector.reflect()`
- `KGUpdater.apply_guideline()` 不再自动创建缺失实体节点（删除现有自动创建逻辑），实体必须由 `EntityExtractor` 预先提取并通过 `SemanticMemory.add_entity()` 创建
- 清理现有 `data/kg/semantic.json` 中的垃圾实体数据

### 3.2 LLM 重试与降级

**问题：** LLM 调用失败只返回静态错误消息，无重试。

**方案：** 新增 `core/llm_caller.py`，封装 `LLMCaller` 类：

```python
class LLMCaller:
    def __init__(self, llm: BaseChatModel, max_retries: int = 3, base_delay: float = 1.0):
        ...

    def invoke(self, messages: list, fallback: str = "") -> str:
        """调用 LLM，失败时指数退避重试，耗尽后返回 fallback 并标记降级"""
        for attempt in range(self.max_retries):
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.base_delay * (2 ** attempt))
                else:
                    return fallback  # 降级

    def stream(self, messages: list):
        """流式调用 LLM，逐 token 返回生成器"""
        for chunk in self.llm.stream(messages):
            if chunk.content:
                yield chunk.content
```

- 替换 `AgentCore`、`Reflector`、`EntityExtractor` 中的直接 `llm.invoke()` 调用
- 降级时在返回消息中标注 `[降级]` 前缀，让用户知道回复可能不可靠

### 3.3 System Prompt 与角色定义

**问题：** 无 System Prompt，LLM 不知道自己的角色。

**方案：** 新增 `core/system_prompt.py`：

```python
SYSTEM_PROMPT_TEMPLATE = """你是一个学术研究助手，具备长期记忆和反思能力。

核心行为：
- 回答学术问题时，优先参考上下文中的 Guidelines（已验证的规则）
- 如果 Guidelines 与你的判断冲突，以 Guidelines 为准
- 当用户纠正你的回答时，你会反思并沉淀新的 Guideline
- 回复语言与用户输入语言一致
- 回复应当准确、结构化，适当引用来源

上下文结构说明：
[Guidelines] - 从过去反思中沉淀的规则，最高优先级
[Knowledge]  - 知识图谱中的实体关系
[History]    - 相关的历史对话
[Current]    - 当前会话内容
"""
```

- `ContextAssembler.assemble()` 在组装消息列表时，将 System Prompt 作为第一条 `SystemMessage` 插入
- `Config` 新增 `system_prompt_template: str` 字段，允许用户自定义覆盖

### 3.4 反思流水线完整性

**问题 1：** 反思结果不写入 Episodic Memory。

**方案：** `SessionManager` 在反思完成后，将用户纠正消息和 Guideline 确认消息存入 Episodic Memory：
```python
episodic.store(content=correction_text, metadata={"type": "reflection", "conversation_id": conv_id})
episodic.store(content=f"沉淀 Guideline: {guideline.rule}", metadata={"type": "guideline", "conversation_id": conv_id})
```

**问题 2：** JSONL 日志缺少错误上下文和 KG diff。

**方案：** `KGUpdater.apply_guideline()` 增强 `_write_log()` 方法，新增字段：
- `error_context: str` — 触发纠正的原始 Agent 回复（由 AgentCore 传入）
- `kg_diff: dict` — `{"added_nodes": [...], "added_edges": [...]}` KG 变更记录
- `reflection_prompt: str` — 完整的反思提示词（由 Reflector 传入）

`KGUpdater.apply_guideline()` 签名改为：
```python
def apply_guideline(self, guideline: Guideline, error_context: str = "", reflection_prompt: str = "") -> None:
```

---

## 4. Orchestrator 拆分

### 4.1 AgentCore

无状态的纯推理逻辑，所有依赖通过构造函数注入：

```python
class AgentCore:
    def __init__(self, llm_caller: LLMCaller, entity_extractor: EntityExtractor,
                 context_assembler: ContextAssembler, reflector: Reflector,
                 kg_updater: KGUpdater, semantic: SemanticMemory, episodic: EpisodicMemory):
        ...

    def infer(self, user_input: str, working_memory: WorkingMemory) -> str:
        """组装上下文 + 调用 LLM 返回回复"""
        entities = self.entity_extractor.extract(user_input)
        context = self.context_assembler.assemble(
            user_input, entities, working_memory.get_full_context(),
            self.semantic, self.episodic
        )
        return self.llm_caller.invoke(context)

    def reflect(self, user_input: str, correction_hint: str,
                error_context: str, working_memory: WorkingMemory) -> Guideline:
        """反思流程：提取实体 → LLM 反思 → KG 更新"""
        source_entities = self.entity_extractor.extract(user_input + " " + correction_hint)
        for entity in source_entities:
            if not self.semantic.get_entity(entity):
                self.semantic.add_entity(entity)
        guideline = self.reflector.reflect(correction_hint, source_entities)
        self.kg_updater.apply_guideline(guideline, error_context=error_context,
                                        reflection_prompt=self.reflector.last_prompt)
        return guideline
```

### 4.2 SessionManager

会话生命周期管理，CLI 和 API 统一调用入口：

```python
@dataclass
class TurnResult:
    response: str
    is_reflection: bool
    guideline: Optional[Guideline] = None
    entities: List[str] = field(default_factory=list)
    guidelines_used: List[str] = field(default_factory=list)

class SessionManager:
    def __init__(self, config: Config, agent_core: AgentCore,
                 working: WorkingMemory, episodic: EpisodicMemory,
                 semantic: SemanticMemory, detector: ReflectionDetector):
        ...

    def start_session(self) -> str:
        """启动新会话，返回 session_id"""
        self._conversation_id = uuid4().hex
        self.working.clear()
        return self._conversation_id

    def process_turn(self, user_input: str) -> TurnResult:
        """处理一轮对话，返回结构化结果"""
        is_reflection, hint = self.detector.check(user_input)
        if is_reflection:
            return self._handle_reflection(user_input, hint)
        else:
            return self._handle_inference(user_input)

    def _handle_inference(self, user_input: str) -> TurnResult:
        self.working.add("user", user_input)
        response = self.agent_core.infer(user_input, self.working)
        self.working.add("assistant", response)
        self.episodic.store(content=f"User: {user_input}", metadata={...})
        self.episodic.store(content=f"Agent: {response}", metadata={...})
        return TurnResult(response=response, is_reflection=False, ...)

    def _handle_reflection(self, user_input: str, hint: str) -> TurnResult:
        # 先获取 error_context（上一条 assistant 回复），再添加 user 消息
        recent = self.working.get_recent(2)
        error_context = ""
        for msg in recent:
            if msg["role"] == "assistant":
                error_context = msg["content"]
                break
        self.working.add("user", user_input)
        guideline = self.agent_core.reflect(user_input, hint, error_context, self.working)
        response = f"已沉淀 Guideline: {guideline.rule}"
        self.working.add("assistant", response)
        # 存入 Episodic Memory
        self.episodic.store(content=user_input, metadata={"type": "reflection", ...})
        self.episodic.store(content=response, metadata={"type": "guideline", ...})
        return TurnResult(response=response, is_reflection=True, guideline=guideline, ...)
```

### 4.3 CLI 适配

`cli.py` 改用 `SessionManager`，行为不变：

```python
def main():
    config = Config()
    llm = _create_llm(config)
    llm_caller = LLMCaller(llm, max_retries=config.llm_max_retries)
    agent_core = AgentCore(llm_caller, ...)
    session = SessionManager(config, agent_core, ...)
    session.start_session()
    # REPL 循环调用 session.process_turn()
```

---

## 5. API 层设计

### 5.1 Pydantic 数据模型（api/schemas.py）

```python
from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    entities: List[str] = []
    guidelines_used: List[str] = []
    is_reflection: bool = False
    guideline: Optional[str] = None

class ReflectionLogEntry(BaseModel):
    id: str
    rule: str
    source_entities: List[str]
    error_context: str
    reflection_prompt: str
    kg_diff: dict
    timestamp: str

class KGNode(BaseModel):
    id: str
    type: str  # "entity" | "rule"
    name: Optional[str] = None
    rule: Optional[str] = None

class KGEdge(BaseModel):
    source: str
    target: str
    relation: str

class KnowledgeGraph(BaseModel):
    nodes: List[KGNode]
    edges: List[KGEdge]

class MemoryStatus(BaseModel):
    semantic: dict  # {"entities": int, "guidelines": int}
    episodic: dict  # {"conversations": int}
    working: dict   # {"turns": int}

class EntityCreate(BaseModel):
    name: str

class EntityDelete(BaseModel):
    id: str
```

### 5.2 API 端点

| 方法 | 路径 | 功能 | 请求 | 响应 |
|------|------|------|------|------|
| POST | `/api/chat` | 发送消息 | ChatRequest | ChatResponse |
| WS | `/api/chat/ws` | WebSocket 流式对话 | text frames | text frames (streamed) |
| GET | `/api/memory/status` | 三级记忆状态 | - | MemoryStatus |
| DELETE | `/api/memory/episodic` | 清空情节记忆 | - | `{"status": "ok"}` |
| GET | `/api/knowledge/graph` | 完整知识图谱 | - | KnowledgeGraph |
| GET | `/api/knowledge/subgraph` | 实体子图 | `?entity=X` | KnowledgeGraph |
| POST | `/api/knowledge/entity` | 添加实体 | EntityCreate | KGNode |
| DELETE | `/api/knowledge/entity/{id}` | 删除实体 | - | `{"status": "ok"}` |
| GET | `/api/reflections` | 反思日志列表 | `?limit=50&entity=X` | List[ReflectionLogEntry] |
| GET | `/api/guidelines` | Guidelines 列表 | - | List[KGNode] |

### 5.3 FastAPI 应用（api/app.py）

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from memo_agent.config import Config

def create_app() -> FastAPI:
    config = Config()
    # 初始化所有组件...
    app = FastAPI(title="MemoAgent API", version="0.2.0")
    app.add_middleware(CORSMiddleware, allow_origins=config.api_cors_origins,
                       allow_methods=["*"], allow_headers=["*"])
    # 注册路由...
    return app
```

### 5.4 WebSocket 流式响应

WebSocket 端点支持流式输出，实现方式：
- FastAPI 接收 WebSocket 连接
- 调用 LLM 的 `stream()` 方法获取 token 流
- 逐个 token 发送给前端
- 完成时发送 `[DONE]` 标记

```python
@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        request = ChatRequest(message=data)
        # 流式调用 LLM
        async for chunk in llm_caller.stream(request.message):
            await websocket.send_text(chunk)
        await websocket.send_text("[DONE]")
```

---

## 6. React 前端设计

### 6.1 页面布局

左侧固定导航栏 + 右侧内容区 + 底部状态栏：

```
┌──────────────────────────────────────────────────┐
│  MemoAgent                           [Settings]  │
├──────┬───────────────────────────────────────────┤
│      │                                           │
│ 对话  │         [当前选中页面的内容区]              │
│ 知识  │                                           │
│ 记忆  │                                           │
│ 反思  │                                           │
│      │                                           │
├──────┴───────────────────────────────────────────┤
│  Status: DeepSeek | KG: 8 entities | 3 guidelines│
└──────────────────────────────────────────────────┘
```

### 6.2 对话页面（ChatPage）

- 消息列表：用户消息靠右（蓝色气泡），Agent 消息靠左（灰色气泡）
- Guideline 标签：当 Agent 回复使用了 Guideline 时，在气泡下方显示橙色标签 `Guideline: xxx`
- 输入区域：文本框 + 发送按钮
- 命令支持：`/reflect`、`/help` 等命令在输入时显示自动补全提示
- WebSocket 流式显示：Agent 回复逐字显示（打字机效果）

### 6.3 知识图谱页面（KnowledgePage）

- 力导向图可视化（react-force-graph-2d）
- 节点颜色：实体=蓝色，Guideline=橙色
- 节点大小：按连接数缩放
- 点击节点：高亮子图，右侧弹出详情面板（节点属性 + 关联节点列表）
- 搜索框：按实体名搜索，搜索结果在图中高亮
- 操作按钮：添加实体、删除实体

### 6.4 记忆状态页面（MemoryPage）

- 三列卡片布局
- 语义记忆卡片：实体列表 + Guidelines 列表，支持搜索过滤
- 情节记忆卡片：按会话分组的历史对话摘要，支持搜索
- 工作记忆卡片：当前会话实时轮次数，刷新按钮

### 6.5 反思日志页面（ReflectionPage）

- 时间线布局，每条反思记录为一条
- 折叠/展开：默认显示 Guideline 摘要，展开显示完整信息：
  - 触发文本（error_context）
  - 反思提示词（reflection_prompt）
  - Guideline 结果（rule）
  - KG 变更（kg_diff: 新增节点 + 新增边）
- 过滤：按实体名、时间范围

### 6.6 技术选型

| 层 | 技术 | 版本 |
|---|------|------|
| 框架 | React + TypeScript | 18.x |
| 构建 | Vite | 5.x |
| 样式 | Tailwind CSS | 3.x |
| 图谱可视化 | react-force-graph-2d | 1.x |
| 状态管理 | Zustand | 4.x |
| HTTP 客户端 | axios | 1.x |
| WebSocket | 原生 WebSocket API | - |

---

## 7. Docker 部署

### 7.1 容器架构

```
docker-compose.yml
├── backend (FastAPI)
│   ├── 镜像: Python 3.9-slim + memo-agent
│   ├── 挂载: ./data → /app/data (持久化)
│   ├── 环境变量: DEEPSEEK_API_KEY
│   └── 端口: 8000 (内部)
├── frontend (React → nginx)
│   ├── 镜像: Node 20-alpine (构建) + nginx:alpine (运行)
│   ├── 构建: npm run build → /usr/share/nginx/html
│   ├── nginx 代理: /api/* → http://backend:8000
│   └── 端口: 80 (映射到宿主机 3000)
```

### 7.2 docker-compose.yml

```yaml
version: "3.9"
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### 7.3 Dockerfile.backend

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir -e .
EXPOSE 8000
CMD ["uvicorn", "memo_agent.api.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
```

### 7.4 Dockerfile.frontend

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Runtime stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 7.5 nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/chat/ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 8. 配置扩展

### 8.1 新增配置项

```python
# config.py 扩展
@dataclass
class Config:
    # ... 保留已有字段 ...

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])

    # System Prompt
    system_prompt_template: str = SYSTEM_PROMPT_TEMPLATE  # 默认值来自 system_prompt.py

    # LLM 重试
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0

    # Working Memory 限制
    working_memory_max_turns: int = 50
```

### 8.2 依赖更新（pyproject.toml）

新增后端依赖：
```
"fastapi>=0.110.0",
"uvicorn>=0.29.0",
"websockets>=12.0",
"pydantic>=2.0",
```

### 8.3 前端依赖（frontend/package.json）

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-force-graph-2d": "^1.25.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0"
  }
}
```

---

## 9. 测试策略

### 9.1 后端测试

- **test_llm_caller.py**: 重试逻辑（mock 抛异常，验证退避和降级）
- **test_system_prompt.py**: System Prompt 模板渲染、自定义覆盖
- **test_core.py**: AgentCore.infer() 和 AgentCore.reflect() 的单元测试（mock LLM）
- **test_api/**: FastAPI TestClient 端点测试
  - test_chat.py: POST /api/chat、WebSocket /api/chat/ws
  - test_memory.py: GET /api/memory/status、DELETE /api/memory/episodic
  - test_knowledge.py: GET/POST/DELETE 知识图谱端点
  - test_reflection.py: GET /api/reflections、GET /api/guidelines
- **test_integration.py**: 更新现有集成测试，改用 SessionManager

### 9.2 测试原则

- 所有 LLM 调用均 mock
- API 测试使用 FastAPI TestClient
- 集成测试覆盖完整 turn 流程（普通推理 + 反思）
- Working Memory 测试验证 turn limit 生效
