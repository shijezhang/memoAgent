# MemoAgent 技术报告

## 1. 项目概述

MemoAgent 是一个具备**长期记忆**和**反思学习能力**的智能对话代理系统。其核心创新在于：当用户纠正 AI 的回答时，系统能够自动提取可复用的推理规则（Guidelines），并将其持久化到知识图谱中，在后续对话中优先应用这些规则，从而实现"从错误中学习"的能力。

### 1.1 核心能力

| 能力 | 描述 |
|------|------|
| **语义记忆** | 基于知识图谱的实体-关系存储，支持子图检索 |
| **情节记忆** | 基于 Vector DB 的历史对话向量化存储与相似性检索 |
| **工作记忆** | 当前会话的短时上下文管理，支持滑动窗口 |
| **反思学习** | 检测用户纠正 → 提取规则 → 更新知识图谱 |

### 1.2 技术栈

```
后端: Python 3.11 / FastAPI / LangChain / NetworkX / ChromaDB
前端: React 18 / TypeScript / Tailwind CSS / Framer Motion / Headless UI
模型: DeepSeek (可替换为任意 LangChain 兼容 LLM)
嵌入: SentenceTransformers (all-MiniLM-L6-v2)
```

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ ChatPage │  │Knowledge │  │ Memory   │  │Reflection│  │ Settings │  │
│  └────┬─────┘  │  Page    │  │  Page    │  │  Page    │  │  Modal   │  │
│       │        └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘  │
│       │             │             │             │                       │
│       └─────────────┴─────────────┴─────────────┘                       │
│                           │ Zustand Store │                            │
│                           └───────┬───────┘                            │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ HTTP/WebSocket
┌───────────────────────────────────┼─────────────────────────────────────┐
│                           FastAPI Backend                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      SessionManager                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │ AgentCore   │  │ Reflection  │  │    Memory Layer         │  │   │
│  │  │             │  │  Pipeline   │  │                         │  │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ ┌─────────┐ │  │   │
│  │  │ │Context  │ │  │ │Detector │ │  │ │Semantic │ │Episodic │ │  │   │
│  │  │ │Assembler│ │  │ │Reflector│ │  │ │ (KG)    │ │(Vector) │ │  │   │
│  │  │ └─────────┘ │  │ │KGUpdater│ │  │ └─────────┘ └─────────┘ │  │   │
│  │  │ ┌─────────┐ │  │ └─────────┘ │  │ ┌─────────────────────┐ │  │   │
│  │  │ │Entity   │ │  └─────────────┘  │ │   Working Memory    │ │  │   │
│  │  │ │Extractor│ │                   │ └─────────────────────┘ │  │   │
│  │  │ └─────────┘ │                   └─────────────────────────┘  │   │
│  │  │ ┌─────────┐ │                                                  │   │
│  │  │ │LLMCaller│ │                                                  │   │
│  │  │ └─────────┘ │                                                  │   │
│  │  └─────────────┘                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ LLM (API)   │  │ NetworkX    │  │ ChromaDB    │  │ FileSystem  │    │
│  │ DeepSeek    │  │ (In-Memory) │  │ (Persistent)│  │ JSON/JSONL  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户输入 ──→ ReflectionDetector.check()
                │
                ├── 检测到纠正 ──→ Reflector.reflect() ──→ KGUpdater.apply() ──→ SemanticMemory
                │
                └── 正常提问 ──→ EntityExtractor.extract()
                                      │
                                      └── ContextAssembler.assemble()
                                            │
                                            ├── SemanticMemory.get_guidelines_for()
                                            ├── SemanticMemory.get_subgraph()
                                            ├── EpisodicMemory.search()
                                            └── WorkingMemory.get_full_context()
                                                      │
                                                      └── LLMCaller.invoke()
                                                            │
                                                            └── 响应用户
```

---

## 3. 记忆系统 (Memory System)

记忆系统是 MemoAgent 的核心，采用认知心理学中的**多存储记忆模型**，分为三层：

### 3.1 语义记忆 (Semantic Memory)

**文件**: `src/memo_agent/memory/semantic.py`

**数据结构**: 有向图 (Directed Graph)

**存储引擎**: NetworkX DiGraph + JSON 持久化

#### 3.1.1 节点类型

```python
# 实体节点
{
    "node_id": "entity_Transformer",
    "type": "entity",
    "name": "Transformer",
    "entity_type": "architecture",
    "properties": {...}
}

# 规则节点 (Guideline)
{
    "node_id": "rule_42",
    "type": "rule", 
    "name": "Transformer的自注意力机制不改变序列长度",
    "rule": "Transformer的自注意力机制不改变序列长度"
}
```

#### 3.1.2 边类型

| 边类型 | 含义 | 示例 |
|--------|------|------|
| `governs` | 实体被某规则约束 | `(Transformer) --governs--> [规则42]` |
| 自定义关系 | 实体间关系 | `(BERT) --variant_of--> (Transformer)` |

#### 3.1.3 核心算法

**子图提取 (BFS 扩展)**:
```python
def get_subgraph(self, entity_names: List[str], depth: int = 1) -> Dict:
    """
    从种子实体出发，BFS 扩展 depth 跳，返回相关子图
    
    算法:
    1. 将输入实体转为节点 ID 集合 (seed_ids)
    2. 初始化 frontier = seed_ids
    3. 循环 depth+1 次:
       a. 遍历 frontier 中每个节点的出边和入边
       b. 将相邻节点加入 next_frontier
       c. 记录访问过的节点和边
    4. 返回节点列表和边列表
    """
```

**规则查询**:
```python
def get_guidelines_for(self, entity_name: str) -> List[str]:
    """
    查询某实体关联的所有 Guideline
    
    算法:
    1. 查找实体节点 ID
    2. 遍历该节点的出边
    3. 筛选 type="governs" 的边
    4. 返回目标节点的 rule 字段
    """
```

#### 3.1.4 持久化机制

- 使用 `nx.node_link_data()` 将图序列化为 JSON
- 每次修改自动保存，写入前备份为 `.bak` 文件
- 启动时检测损坏文件，自动回滚备份

---

### 3.2 情节记忆 (Episodic Memory)

**文件**: `src/memo_agent/memory/episodic.py`

**数据结构**: 向量索引 + 元数据

**存储引擎**: ChromaDB + SentenceTransformers

#### 3.2.1 向量化存储

```python
# 初始化
self._embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # 384 维向量
)

# 存储对话轮次
def store(self, conversation_id: str, turn: dict, metadata: dict):
    """
    将对话内容向量化后存入 ChromaDB
    
    参数:
    - conversation_id: 会话 ID
    - turn: {"role": "user/assistant", "content": "..."}
    - metadata: {"timestamp": "...", "entities": [...]}
    
    存储:
    - documents: 对话文本 (用于展示)
    - embeddings: 自动计算的向量 (用于检索)
    - metadatas: 元数据 (用于过滤)
    """
```

#### 3.2.2 相似性检索

```python
def search(self, query: str, top_k: int = 5) -> List[dict]:
    """
    基于向量相似度检索相关历史对话
    
    算法:
    1. 将 query 转为向量 (使用相同 embedding model)
    2. 计算与库中所有向量的余弦相似度
    3. 返回 top_k 个最相似的文档
    4. 附带元数据和距离分数
    """
```

#### 3.2.3 嵌入模型选择

| 模型 | 维度 | 特点 |
|------|------|------|
| `all-MiniLM-L6-v2` | 384 | 轻量、快速，适合原型 |
| `text-embedding-3-small` | 1536 | OpenAI，更高精度 |
| `bge-large-zh-v1.5` | 1024 | 中英双语优化 |

---

### 3.3 工作记忆 (Working Memory)

**文件**: `src/memo_agent/memory/working.py`

**数据结构**: 滑动窗口队列

**存储引擎**: 内存 (无持久化)

#### 3.3.1 实现原理

```python
class WorkingMemory:
    def __init__(self, max_turns: int = 50):
        self._messages: list[dict] = []  # 消息队列
        self._max_turns = max_turns      # 最大轮次

    def add(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})
        # 滑动窗口：超出限制时删除最旧的消息
        while len(self._messages) > self._max_turns * 2:
            self._messages.pop(0)
```

#### 3.3.2 设计考量

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_turns` | 50 | 最大保留对话轮次 |
| 窗口策略 | FIFO | 先进先出，保留最新 |
| 持久化 | 无 | 会话结束即清空 |

---

## 4. 反思系统 (Reflection System)

反思系统是 MemoAgent 的核心创新点，实现从用户纠正中自动提取知识。

### 4.1 系统流程

```
用户输入: "不对，Transformer的自注意力不改变序列长度"
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. ReflectionDetector                                        │
│    - 检测关键词: "不对", "错了", "不是这样的"...             │
│    - 提取纠正内容: "Transformer的自注意力不改变序列长度"    │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Reflector                                                 │
│    - 构造反思 Prompt (包含错误上下文 + 纠正提示)            │
│    - 调用 LLM 分析错误根源                                   │
│    - 解析输出，提取 [Guideline] 规则                        │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. KGUpdater                                                 │
│    - 检查规则是否重复                                        │
│    - 确保相关实体存在                                        │
│    - 创建规则节点，建立 governing 边                        │
│    - 记录反思日志 (JSONL)                                    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 ReflectionDetector

**文件**: `src/memo_agent/reflection/detector.py`

**算法**: 关键词匹配 + 规则提取

```python
class ReflectionDetector:
    def __init__(self, config: Config):
        self._keywords = ["不对", "错了", "不是这样的", "搞反了", ...]
        self._commands = ["/reflect", "/纠错"]

    def check(self, user_input: str) -> bool:
        """检测用户输入是否包含纠正意图"""
        for kw in self._keywords:
            if kw in user_input:
                return True
        return user_input.strip() in self._commands

    def extract_hint(self, user_input: str) -> str:
        """提取纠正内容（去除关键词）"""
        hint = user_input
        for kw in self._keywords:
            hint = hint.replace(kw, "", 1)  # 只替换第一个匹配
        return hint.strip()
```

**设计权衡**:
- ✅ 简单高效，无需 LLM 调用
- ⚠️ 可能产生误判（如用户引用"不对"这个词）
- 💡 可扩展：支持用户自定义关键词和命令

### 4.3 Reflector

**文件**: `src/memo_agent/reflection/reflector.py`

**算法**: LLM Prompt Engineering + 结构化解析

#### 4.3.1 反思 Prompt 模板

```
你是一个学术推理审查器。以下是一个错误的学术推导案例：

【错误上下文】
{error_context}  # AI 之前的错误回答

【用户纠正】
{correction_hint}  # 用户的纠正内容

请分析：
1. 错误根源：Agent 混淆了什么概念？遗漏了什么约束？
2. 正确逻辑：应当如何推导？

基于以上分析，提取一条普适性规则，格式：
[Guideline] {一条具体的、可执行的学术推理规则}
```

#### 4.3.2 规则提取

```python
def _parse_guideline(self, text: str) -> Optional[str]:
    """从 LLM 输出中解析 [Guideline] 规则"""
    marker = "[Guideline]"
    idx = text.find(marker)
    if idx == -1:
        return None
    return text[idx + len(marker):].strip()
```

**示例**:
```
LLM 输出:
分析：
1. 错误根源：混淆了自注意力的输出维度与序列长度
2. 正确逻辑：自注意力计算 Q-K-V，输出序列长度等于输入

[Guideline] Transformer的自注意力机制不改变序列长度，只改变特征维度

提取结果:
"Transformer的自注意力机制不改变序列长度，只改变特征维度"
```

### 4.4 KGUpdater

**文件**: `src/memo_agent/reflection/kg_updater.py`

**算法**: 图更新 + 重复检测 + 日志记录

#### 4.4.1 更新流程

```python
def apply_guideline(self, guideline: Guideline, semantic: SemanticMemory):
    # 1. 检查重复
    if self._is_duplicate(guideline.rule, semantic):
        return {"skipped": True, "reason": "duplicate"}

    # 2. 确保实体存在
    for entity_name in guideline.source_entities:
        if semantic.get_entity(entity_name) is None:
            semantic.add_entity(entity_name, "concept", {})

    # 3. 添加规则节点
    rule_id = semantic.add_guideline(guideline.rule, guideline.source_entities)

    # 4. 建立 governing 边
    for entity_name in guideline.source_entities:
        entity = semantic.get_entity(entity_name)
        semantic._graph.add_edge(entity["node_id"], rule_id, type="governs")
```

#### 4.4.2 重复检测算法

```python
def _is_duplicate(self, new_rule: str, semantic: SemanticMemory) -> bool:
    """检查新规则是否与已有规则重复或包含"""
    for node_data in semantic._graph.nodes(data=True):
        if node_data.get("type") == "rule":
            existing = node_data.get("rule", "")
            # 双向包含检测
            if existing in new_rule or new_rule in existing:
                return True
    return False
```

---

## 5. 检索系统 (Retrieval System)

检索系统负责从记忆中提取相关信息，组装成 LLM 上下文。

### 5.1 EntityExtractor

**文件**: `src/memo_agent/retrieval/entity_extractor.py`

**算法**: LLM Named Entity Recognition + 缓存

```python
EXTRACTION_PROMPT = """从以下文本中提取学术/技术实体（算法名、方法名、数据集、领域术语）。
仅返回实体列表，每行一个，不要解释。如果没有学术实体，返回空。

文本：{text}"""

class EntityExtractor:
    def __init__(self, llm):
        self._llm = llm
        self._cache: dict = {}  # MD5(text) -> entities

    def extract(self, text: str) -> List[str]:
        # 1. 检查缓存
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. 调用 LLM 提取实体
        response = self._llm.invoke(EXTRACTION_PROMPT.format(text=text))
        entities = [line.strip() for line in response.split("\n") if line.strip()]

        # 3. 缓存结果
        self._cache[cache_key] = entities
        return entities
```

**缓存策略**:
- 使用 MD5 哈希作为缓存键
- 避免对相同文本重复调用 LLM
- 内存缓存，进程结束时清空

### 5.2 ContextAssembler

**文件**: `src/memo_agent/retrieval/context_assembler.py`

**算法**: 优先级分层组装 + Token 预算分配

#### 5.2.1 优先级体系

```
Priority 1: System Prompt     ─── 固定，不裁剪
Priority 2: Guidelines        ─── 最高优先级，不裁剪
Priority 3: Knowledge Subgraph ─── 按预算裁剪
Priority 4: Episodic Memory   ─── 按预算裁剪
Priority 5: Working Memory    ─── 按剩余预算裁剪
Priority 6: User Input        ─── 固定，不裁剪
```

#### 5.2.2 组装算法

```python
def assemble(self, user_input: str, working, episodic, semantic) -> str:
    sections = []

    # 1. 提取实体
    entities = self._entity_extractor.extract(user_input)

    # 2. System Prompt (不裁剪)
    sections.append(("system", self._system_prompt))

    # 3. Guidelines (不裁剪)
    guidelines = []
    for entity in entities:
        guidelines.extend(semantic.get_guidelines_for(entity))
    if guidelines:
        sections.append(("guidelines", format_guidelines(guidelines)))

    # 4. Knowledge Subgraph (按预算裁剪)
    subgraph = semantic.get_subgraph(entities, depth=1)
    knowledge = format_subgraph(subgraph)
    knowledge = truncate(knowledge, max_subgraph_tokens)
    sections.append(("subgraph", knowledge))

    # 5. Episodic Memory (按预算裁剪)
    history = episodic.search(user_input, top_k=3)
    history_text = format_history(history)
    history_text = truncate(history_text, max_episodic_tokens)
    sections.append(("episodic", history_text))

    # 6. Working Memory (按剩余预算裁剪)
    context = working.get_full_context()
    remaining = self._remaining_budget(sections)
    context_text = truncate_list(context, remaining)
    sections.append(("context", context_text))

    # 7. User Input (不裁剪)
    sections.append(("user", user_input))

    return "\n\n".join(text for _, text in sections)
```

#### 5.2.3 Token 估算

```python
# 混合文本估算：中文约 1.5 字/token
def _truncate(text: str, max_tokens: int) -> str:
    max_chars = int(max_tokens * 1.5)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

def _remaining_budget(self, sections) -> int:
    used = sum(len(text) / 1.5 for _, text in sections)
    return max(self._max_context_tokens - used, 2000)  # 最少保留 2000 tokens
```

#### 5.2.4 组装结果示例

```
你是一个学术研究助手，具备长期记忆和反思能力。
...

【学术审查规则 - 你必须严格遵守】
- Transformer的自注意力机制不改变序列长度
- BERT 使用双向编码，GPT 使用单向解码

【相关知识】
  Transformer (architecture)
  BERT (model)
  GPT (model)
  Transformer --variant_of--> BERT
  Transformer --variant_of--> GPT

【相关历史讨论】
[abc123 @ 2024-01-15] 用户问过 Transformer 的并行计算能力...

【当前对话】
user: Transformer 和 RNN 的区别是什么？
assistant: Transformer 与 RNN 的核心区别在于...

【用户最新输入】
那 Transformer 的自注意力计算复杂度是多少？
```

---

## 6. 核心 Agent

### 6.1 AgentCore

**文件**: `src/memo_agent/core/agent.py`

**职责**: 协调推理和反思流程

```python
class AgentCore:
    def infer(self, user_input: str, working_memory: WorkingMemory) -> str:
        """正常推理流程"""
        # 1. 提取实体
        entities = self._entity_extractor.extract(user_input)
        
        # 2. 组装上下文
        context = self._context_assembler.assemble(
            user_input, working_memory, self._episodic, self._semantic
        )
        
        # 3. 调用 LLM
        return self._llm_caller.invoke(context)

    def reflect(self, user_input, correction_hint, error_context, working_memory):
        """反思流程"""
        # 1. 提取相关实体
        entities = self._entity_extractor.extract(user_input + " " + correction_hint)
        
        # 2. 确保实体存在于 KG
        for entity in entities:
            if self._semantic.get_entity(entity) is None:
                self._semantic.add_entity(entity, "concept", {})
        
        # 3. 反思并生成 Guideline
        guideline = self._reflector.reflect_with_context(
            error_context, correction_hint, entities
        )
        
        # 4. 更新知识图谱
        if guideline:
            self._kg_updater.apply_guideline(guideline, self._semantic, ...)
        
        return guideline
```

### 6.2 LLMCaller

**文件**: `src/memo_agent/core/llm_caller.py`

**职责**: LLM 调用封装，支持重试和降级

```python
class LLMCaller:
    def __init__(self, llm, max_retries=3, base_delay=1.0):
        self._llm = llm
        self._max_retries = max_retries
        self._base_delay = base_delay  # 指数退避基准延迟

    def invoke(self, messages, fallback="推理暂时不可用") -> str:
        for attempt in range(self._max_retries):
            try:
                response = self._llm.invoke(messages)
                return response.content
            except Exception as e:
                if attempt < self._max_retries - 1:
                    # 指数退避: 1s, 2s, 4s
                    delay = self._base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    # 最终失败，返回降级响应
                    return f"[降级] {fallback}"
```

**重试策略**: 指数退避 (Exponential Backoff)
```
Attempt 1: 立即重试
Attempt 2: 等待 1s
Attempt 3: 等待 2s
最终失败: 返回降级响应
```

### 6.3 SessionManager

**文件**: `src/memo_agent/core/session.py`

**职责**: 会话生命周期管理

```python
@dataclass
class TurnResult:
    response: str
    is_reflection: bool
    guideline: Optional[Guideline]
    entities: List[str]
    guidelines_used: List[str]

class SessionManager:
    def process_turn(self, user_input: str) -> TurnResult:
        # 1. 检测是否为反思
        is_reflection, hint = self._detector.check_and_extract(user_input)
        
        if is_reflection:
            # 反思流程
            return self._handle_reflection(user_input, hint)
        else:
            # 正常推理流程
            return self._handle_inference(user_input)
```

---

## 7. 前端架构

### 7.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.3 | UI 框架 |
| TypeScript | 5.4 | 类型安全 |
| Tailwind CSS | 3.4 | 样式系统 |
| Zustand | 4.5 | 状态管理 |
| Framer Motion | 11.0 | 动画 |
| Headless UI | 2.0 | 无障碍组件 |
| Lucide React | 0.400 | 图标库 |
| React Markdown | 9.0 | Markdown 渲染 |

### 7.2 组件架构

```
src/
├── components/
│   ├── Layout.tsx          # 布局容器
│   ├── Header.tsx          # 顶部导航 (Logo + ThemeToggle + Settings)
│   ├── Sidebar.tsx         # 左侧导航 (对话/知识/记忆/反思)
│   ├── StatusBar.tsx       # 底部状态栏 (模型/实体数/Guidelines)
│   ├── ThemeToggle.tsx     # 主题切换
│   ├── SettingsModal.tsx   # 设置弹窗
│   ├── MessageBubble.tsx   # 消息气泡 (Markdown + 流式光标)
│   ├── CodeBlock.tsx       # 代码块 (语法高亮 + 复制)
│   └── ui/                 # 通用组件
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Badge.tsx
│       └── Input.tsx
├── pages/
│   ├── ChatPage.tsx        # 对话页 (流式输出 + 打字机效果)
│   ├── KnowledgePage.tsx   # 知识图谱 (Obsidian 风格 + Force Graph)
│   ├── MemoryPage.tsx      # 记忆状态 (三列卡片)
│   └── ReflectionPage.tsx  # 反思日志 (时间线布局)
├── hooks/
│   ├── useTheme.ts         # 主题管理 (localStorage + 系统偏好)
│   └── useWebSocket.ts     # WebSocket 流式 (预留)
├── store/
│   └── useStore.ts         # Zustand 全局状态
└── lib/
    └── cn.ts               # className 合并工具
```

### 7.3 状态管理 (Zustand)

```typescript
interface Store {
  // Chat state
  messages: Message[]
  sessionId: string
  isLoading: boolean

  // Memory state
  memoryStatus: MemoryStatus | null

  // Knowledge graph state
  knowledgeGraph: KnowledgeGraph | null
  selectedNode: string | null

  // Reflection state
  reflections: ReflectionLogEntry[]

  // Actions
  addMessage: (message: Message) => void
  clearMessages: () => void
  fetchMemoryStatus: () => Promise<void>
  fetchKnowledgeGraph: () => Promise<void>
  fetchReflections: (limit?: number, entity?: string) => Promise<void>
}
```

### 7.4 主题系统

```typescript
// useTheme.ts
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // 1. 检查 localStorage
    const stored = localStorage.getItem('theme')
    if (stored) return stored
    
    // 2. 检测系统偏好
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark' : 'light'
  })

  useEffect(() => {
    // 应用主题类
    document.documentElement.classList.toggle('dark', theme === 'dark')
    // 持久化
    localStorage.setItem('theme', theme)
  }, [theme])

  return { theme, toggleTheme: () => setTheme(prev => prev === 'light' ? 'dark' : 'light') }
}
```

**Tailwind 配置**:
```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',  // 使用 .dark 类切换
  theme: {
    extend: {
      colors: {
        primary: { /* blue-500 系列 */ },
        dark: {
          bg: '#1a1a2e',
          'bg-secondary': '#16213e',
          'bg-sidebar': '#0f0f23',
          'bg-graph': '#0d1117',  // Obsidian 风格
        }
      }
    }
  }
}
```

### 7.5 知识图谱可视化

**技术**: react-force-graph-2d + Canvas

**Obsidian 风格实现**:
```typescript
// 节点绘制
const paintNode = (node, ctx, globalScale) => {
  const size = getNodeSize(node)  // 基于连接数计算大小
  
  // 发光效果
  ctx.shadowBlur = isSelected ? 20 : 12
  ctx.shadowColor = node.type === 'rule' ? '#fb923c' : '#60a5fa'
  
  // 绘制圆点
  ctx.beginPath()
  ctx.arc(node.x, node.y, size, 0, 2 * Math.PI)
  ctx.fillStyle = node.type === 'rule' ? '#fb923c' : '#60a5fa'
  ctx.fill()
  
  // 选中时显示标签
  if (isSelected && globalScale > 0.5) {
    ctx.fillText(node.name, node.x, node.y + size + 14)
  }
}
```

---

## 8. API 接口

### 8.1 REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/chat` | POST | 发送消息，返回响应 |
| `/api/memory/status` | GET | 获取记忆状态 |
| `/api/memory/episodic` | DELETE | 清空情节记忆 |
| `/api/knowledge/graph` | GET | 获取知识图谱 |
| `/api/knowledge/entities` | POST | 添加实体 |
| `/api/knowledge/entities/{id}` | DELETE | 删除实体 |
| `/api/reflection/guidelines` | GET | 获取所有 Guidelines |
| `/api/reflection/logs` | GET | 获取反思日志 |

### 8.2 请求/响应示例

**POST /api/chat**
```json
// Request
{
  "message": "Transformer 和 RNN 有什么区别？",
  "session_id": "abc12345"  // 可选
}

// Response
{
  "response": "Transformer 和 RNN 的核心区别...",
  "session_id": "abc12345",
  "entities": ["Transformer", "RNN"],
  "guidelines_used": ["Transformer 使用自注意力机制"],
  "is_reflection": false
}
```

---

## 9. 数据持久化

### 9.1 文件结构

```
data/
├── kg/
│   ├── semantic.json      # 知识图谱
│   └── semantic.json.bak  # 备份
├── chroma/                 # ChromaDB 向量库
│   └── chroma.sqlite3
└── reflection_log.jsonl   # 反思日志
```

### 9.2 反思日志格式

```json
{
  "rule": "Transformer的自注意力机制不改变序列长度",
  "source_entities": ["Transformer", "自注意力"],
  "timestamp": "2024-01-15T10:30:00Z",
  "error_context": "AI 之前的错误回答...",
  "reflection_prompt": "反思 Prompt...",
  "kg_diff": {
    "added_nodes": [...],
    "added_edges": [...]
  }
}
```

---

## 10. 扩展性与优化建议

### 10.1 当前限制

| 限制 | 原因 | 解决方案 |
|------|------|----------|
| 实体提取依赖 LLM | Prompt-based NER | 可替换为 spaCy/GLiNER |
| 反思检测基于关键词 | 简单规则 | 可用分类模型替代 |
| 知识图谱内存加载 | NetworkX 限制 | 大规模可用 Neo4j |
| 无多用户支持 | 单进程设计 | 添加认证与会话隔离 |

### 10.2 优化方向

1. **流式输出**: 使用 WebSocket 实现真正的 LLM 流式响应
2. **增量嵌入**: 只对新对话计算向量，避免重复计算
3. **图数据库**: 大规模知识图谱迁移到 Neo4j
4. **规则冲突检测**: 当多条 Guideline 矛盾时的处理策略
5. **多模态支持**: 扩展到图像、表格等非文本知识

---

## 11. 总结

MemoAgent 实现了一个具备**长期记忆**和**反思学习**能力的智能对话系统。其核心创新包括：

1. **三层记忆架构**: 工作记忆、情节记忆、语义记忆的有机结合
2. **反思学习机制**: 从用户纠正中自动提取知识规则
3. **优先级上下文组装**: 确保 Guideline 在推理中具有最高优先级
4. **现代前端界面**: 主题切换、流式输出、知识图谱可视化

该系统可应用于学术研究辅助、领域知识问答、智能客服等场景，通过持续学习用户反馈，逐步提升回答准确性。
