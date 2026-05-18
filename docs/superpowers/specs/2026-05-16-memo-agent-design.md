# Design Spec: MemoAgent — 终身学习学术 Agent

**Date:** 2026-05-16
**Status:** Approved

## 1. Overview

MemoAgent is a CLI-based academic research assistant with a three-level memory architecture (Working / Episodic / Semantic) and an explicit-feedback-driven reflection mechanism. When the user corrects the Agent's academic reasoning, the system extracts a reusable Guideline, permanently stores it in the knowledge graph, and automatically injects it into future prompts involving the same entities.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM abstraction | LangChain | Portable across providers; mature primitives for embeddings and vector stores |
| Vector DB | ChromaDB | Zero external dependencies; local file persistence; simplest MVP setup |
| Knowledge graph | NetworkX + JSON | Debuggable; inspectable; sufficient for MVP scale (hundreds of entities) |
| Reflection trigger | Keyword + command | Explicit, reliable, low false-positive rate; aligns with PRD's "explicit feedback" philosophy |
| Development cadence | Layer-by-layer with full tests | Each memory layer independently testable before integration |
| Architecture | Custom orchestrator + LangChain primitives | Full control over three-level memory and reflection pipeline; no framework coupling on state management |

## 2. Shared Data Types

```python
@dataclass
class Guideline:
    rule: str                  # The distilled academic reasoning rule
    source_entities: list[str] # Academic entities this rule relates to
    timestamp: str             # ISO 8601 creation time
```

Used by `Reflector` (produces), `KGUpdater` (consumes), and `SemanticMemory` (stores).

## 3. Project Structure

```
memoAgent/
├── src/
│   └── memo_agent/
│       ├── __init__.py
│       ├── cli.py                  # CLI entry point, REPL loop
│       ├── orchestrator.py         # Core orchestrator: manages conversation flow
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── working.py          # Working memory: session-level context
│       │   ├── episodic.py         # Episodic memory: ChromaDB vector store
│       │   └── semantic.py         # Semantic memory: NetworkX KG + JSON persistence
│       ├── reflection/
│       │   ├── __init__.py
│       │   ├── detector.py         # Negation/correction keyword detector
│       │   ├── reflector.py        # Reflection CoT chain, distills Guidelines
│       │   └── kg_updater.py       # Writes Guideline rule nodes into KG
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── entity_extractor.py # Extracts academic entities from user input
│       │   └── context_assembler.py# Fuses three memory layers into prompt
│       └── config.py               # Global config (model names, paths, thresholds)
├── data/                           # Runtime data (gitignored)
│   ├── chroma/                     # ChromaDB persistence
│   └── kg/                         # KG JSON files
├── tests/
│   ├── test_working.py
│   ├── test_episodic.py
│   ├── test_semantic.py
│   ├── test_reflection.py
│   ├── test_retrieval.py
│   └── test_integration.py
├── pyproject.toml
└── .env                            # API keys
```

Module boundaries:
- `memory/` modules are independent, exposing only `save()` / `load()` / `query()` interfaces
- `reflection/` depends only on `semantic.py`'s write interface
- `orchestrator.py` is the sole glue — calls retrieval for context, LLM for generation, detects reflection triggers, calls reflection pipeline

## 3. Three-Level Memory Architecture

### 3.1 Working Memory

```python
class WorkingMemory:
    def add(self, role: str, content: str) -> None
    def get_recent(self, n: int = 3) -> list[dict]
    def get_full_context(self) -> list[dict]
    def clear(self) -> None
```

- Pure in-memory `list[dict]`, each entry `{"role": "user"/"assistant", "content": "..."}`
- `get_recent()` supplies error samples to the reflection pipeline
- `get_full_context()` supplies session context to context assembler
- No persistence; destroyed on process exit

### 3.2 Episodic Memory

```python
class EpisodicMemory:
    def store(self, conversation_id: str, turn: dict, metadata: dict) -> None
    def search(self, query: str, top_k: int = 5) -> list[dict]
    def get_by_conversation(self, conversation_id: str) -> list[dict]
```

- ChromaDB persisted to `data/chroma/`, survives across sessions
- Each conversation turn stored as a document; metadata includes `conversation_id`, `timestamp`, `entities`
- Embedding via LangChain's embedding adapters (configurable in `config.py`)
- `search()` returns `[{"content": "...", "metadata": {...}, "distance": float}]`

### 3.3 Semantic Memory

```python
class SemanticMemory:
    def add_entity(self, name: str, entity_type: str, properties: dict) -> str
    def add_relation(self, source: str, target: str, relation: str) -> None
    def add_guideline(self, rule: str, related_entities: list[str]) -> str
    def get_entity(self, name: str) -> dict | None
    def get_guidelines_for(self, entity_name: str) -> list[str]
    def get_subgraph(self, entity_names: list[str], depth: int = 1) -> dict
    def save(self) -> None
    def load(self) -> None
```

- NetworkX `DiGraph`; node attributes include `type` (`entity` / `rule`), `properties`
- Guideline nodes have `type="rule"`; connected to entities via edges with `type="governs"`
- `get_guidelines_for()` is the critical retrieval method: finds all rule nodes connected to an entity, returned with highest priority
- `get_subgraph()` returns entity neighborhood for context assembly
- JSON persistence: auto-save after every `add_*` operation; load on startup; `.bak` backup before each save

### 3.4 Memory Collaboration in Retrieval

```
User input
  │
  ├─→ entity_extractor → semantic.get_guidelines_for() → Guidelines list
  ├─→ semantic.get_subgraph() → Entity relation context
  ├─→ episodic.search() → Similar historical conversations
  └─→ working.get_full_context() → Current session context
  │
  ▼
context_assembler merges four info streams → assembled Prompt → LLM
```

Retrieval priority: **Guidelines > Current context > Episodic memory**. Guidelines are the crystallized output of reflection and are always injected first.

## 4. Reflection Pipeline

### 4.1 Reflection Detector

```python
class ReflectionDetector:
    def check(self, user_input: str) -> bool
    def extract_correction(self, user_input: str) -> dict | None
```

- Keyword matching: `不对`, `错了`, `不是这样的`, `搞反了`, `修改学术假设`, etc.
- Explicit command: `/reflect` or `/纠错`
- `extract_correction()` returns `{"trigger": "original text", "hint": "user's implied correct direction"}`
- Keyword list configurable in `config.py`
- Regex + keyword list implementation; no LLM classification

### 4.2 Reflector

```python
class Reflector:
    def reflect(self, error_context: list[dict], correction_hint: dict) -> Guideline | None
```

Reflection flow:
1. Retrieve last 3 turns from `working_memory.get_recent(n=3)` as error sample
2. Assemble reflection prompt and call Critique LLM (same model, independent prompt template):

```
你是一个学术推理审查器。以下是一个错误的学术推导案例：

【错误上下文】
{last 3 turns}

【用户纠正】
{correction_hint}

请分析：
1. 错误根源：Agent 混淆了什么概念？遗漏了什么约束？
2. 正确逻辑：应当如何推导？

基于以上分析，提取一条普适性规则，格式：
[Guideline] {一条具体的、可执行的学术推理规则}
```

3. Parse LLM output, extract content after `[Guideline]` marker
4. Return `Guideline` object: `{"rule": str, "source_entities": list[str], "timestamp": str}`

Error handling: if LLM fails to produce a valid Guideline, log the failure and return `None` — never write garbage to the KG.

### 4.3 KG Updater

```python
class KGUpdater:
    def apply_guideline(self, guideline: Guideline, semantic: SemanticMemory) -> None
```

Write logic:
1. Extract academic entities from `guideline.source_entities`
2. For each entity: fetch node_id if exists, otherwise `add_entity()` to create it
3. `add_guideline(rule, related_entities)` creates the rule node
4. Create `governs` edge from each related entity to the rule node

Dedup check: before writing, compare new Guideline text against existing rule nodes using string containment check. If highly similar, skip and log warning to prevent "memory overfitting".

### 4.4 Full Reflection Flow

```
User: "不对，TARSL 是各向异性的"
  │
  ▼
detector.check() → True
detector.extract_correction() → {"trigger": "...", "hint": "TARSL是各向异性的"}
  │
  ▼
working_memory.get_recent(3) → last 3 turns
  │
  ▼
reflector.reflect(error_context, correction_hint) → Guideline
  │
  ▼
kg_updater.apply_guideline(guideline, semantic_memory)
  │
  ▼
Agent confirms: "已成功提取 Guideline 并绑定至语义记忆。"
```

Observability: every reflection writes to `data/reflection_log.jsonl` with: trigger text, error context, full reflection prompt, KG diff before/after. Enables human review of graph pollution.

## 5. Retrieval & Inference

### 5.1 Entity Extractor

```python
class EntityExtractor:
    def extract(self, text: str) -> list[str]
```

- LLM-based extraction with prompt template
- Caching: same input hash extracts only once; cache valid within working memory lifetime

### 5.2 Context Assembler

```python
class ContextAssembler:
    def assemble(self, user_input: str, working: WorkingMemory,
                 episodic: EpisodicMemory, semantic: SemanticMemory) -> str
```

Assembly flow:
1. `entity_extractor.extract(user_input)` → entity list
2. If entities found:
   - `semantic.get_guidelines_for(each entity)` → Guidelines list (highest priority)
   - `semantic.get_subgraph(entities, depth=1)` → entity relation context
3. `episodic.search(user_input, top_k=3)` → similar historical conversations
4. `working.get_full_context()` → current session context

Prompt template:

```
【学术审查规则 - 你必须严格遵守】
{guidelines list, one per line; section omitted if empty}

【相关知识】
{entity subgraph description; section omitted if empty}

【相关历史讨论】
{episodic memory fragments with conversation_id and timestamp; section omitted if empty}

【当前对话】
{working memory conversation history}

【用户最新输入】
{user_input}
```

Token budget control (total prompt ≤ 80% of model context window):
- Guidelines: never truncated
- Knowledge subgraph: max 1000 tokens
- Historical discussions: max 1500 tokens
- Current conversation: truncate oldest turns first

### 5.3 Orchestrator Main Loop

```python
class Orchestrator:
    def __init__(self, config): ...
    def run_turn(self, user_input: str) -> str
    def start_session(self) -> None
```

`run_turn` logic:

1. `working_memory.add("user", user_input)`
2. If `reflection_detector.check(user_input)`:
   - Extract correction hint
   - Run reflection → guideline extraction → KG update
   - Return confirmation message (skip normal inference)
3. `context = context_assembler.assemble(...)` → `response = llm.invoke(context)`
4. `working_memory.add("assistant", response)`
5. `episodic.store(conversation_id, current_turn, metadata={entities, timestamp})`
6. Return response

When reflection is triggered, the agent returns a confirmation message. The next user input (e.g., "重新分析") will automatically carry the newly written Guideline.

## 6. CLI Interface

REPL built on `prompt_toolkit`:

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/quit` | Exit and save |
| `/reflect` | Manually trigger reflection |
| `/memory status` | Show three-level memory stats (entity count, conversation count, guideline count) |
| `/memory clear episodic` | Clear episodic memory |
| `/guidelines` | List all deposited Guidelines |

## 7. Error Handling

| Scenario | Strategy |
|----------|----------|
| LLM API call failure | Retry once; if still fails, return "推理暂时不可用", do not crash session |
| ChromaDB read/write error | Degrade to working memory only; notify user episodic memory unavailable |
| KG JSON file corruption | Load from `.bak` backup; if no backup, initialize empty graph |
| Reflection Guideline extraction failure | Log failure, do not write to KG, return "未能提取有效规则" |
| Token limit exceeded | Context assembler progressively truncates low-priority sections |
| Guideline dedup/conflict | String containment check + warning log; skip write |

Global principle: any storage layer failure must not crash the session; degrade to available memory layers.

## 8. Test Strategy (Layer-by-Layer)

**Layer 1: Three-level memory — independent tests**

- `test_working.py`: add / get_recent / clear correctness
- `test_episodic.py`: store / search vector recall accuracy (pre-seed documents, verify hits)
- `test_semantic.py`: add_entity / add_relation / add_guideline / get_guidelines_for correctness; JSON save/load consistency

**Layer 2: Retrieval chain**

- `test_entity_extractor.py`: correct entity extraction from input (mock LLM)
- `test_context_assembler.py`: mock memory returns, verify assembled prompt contains all sections with correct priority; verify token truncation logic

**Layer 3: Reflection pipeline**

- `test_reflection_detector.py`: negation trigger correctness; extract_correction correctness; no false positives on normal input
- `test_reflector.py`: mock LLM return, verify Guideline parsing; invalid output does not write
- `test_kg_updater.py`: apply_guideline creates rule node and governs edges; dedup logic

**Layer 4: Integration**

- `test_integration.py`: end-to-end scenario — normal conversation → trigger reflection → next conversation auto-carries Guideline; verify full memory evolution loop

All tests use pytest; LLM calls uniformly mocked; no external API dependencies.
