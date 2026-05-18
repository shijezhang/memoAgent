# MemoAgent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI-based academic research agent with three-level memory and explicit-feedback-driven reflection.

**Architecture:** Custom orchestrator coordinates independent memory modules (Working/Episodic/Semantic), a reflection pipeline (detector → reflector → KG updater), and a retrieval chain (entity extractor → context assembler). LangChain provides LLM and embedding primitives only; no framework state management.

**Tech Stack:** Python 3.10+, LangChain, ChromaDB, NetworkX, prompt_toolkit, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/memo_agent/__init__.py` | Package init, version |
| `src/memo_agent/config.py` | Global config dataclass (paths, model names, keyword lists, token budgets) |
| `src/memo_agent/memory/__init__.py` | Package init |
| `src/memo_agent/memory/working.py` | WorkingMemory — in-memory session context |
| `src/memo_agent/memory/episodic.py` | EpisodicMemory — ChromaDB vector store |
| `src/memo_agent/memory/semantic.py` | SemanticMemory — NetworkX KG + JSON persistence |
| `src/memo_agent/reflection/__init__.py` | Package init |
| `src/memo_agent/reflection/detector.py` | ReflectionDetector — keyword/command trigger |
| `src/memo_agent/reflection/reflector.py` | Reflector — CoT reflection, Guideline extraction |
| `src/memo_agent/reflection/kg_updater.py` | KGUpdater — write Guideline nodes into KG |
| `src/memo_agent/retrieval/__init__.py` | Package init |
| `src/memo_agent/retrieval/entity_extractor.py` | EntityExtractor — LLM-based entity extraction with cache |
| `src/memo_agent/retrieval/context_assembler.py` | ContextAssembler — fuse memories into prompt |
| `src/memo_agent/orchestrator.py` | Orchestrator — main conversation loop |
| `src/memo_agent/cli.py` | CLI REPL entry point |
| `tests/test_working.py` | WorkingMemory tests |
| `tests/test_episodic.py` | EpisodicMemory tests |
| `tests/test_semantic.py` | SemanticMemory tests |
| `tests/test_reflection.py` | ReflectionDetector, Reflector, KGUpdater tests |
| `tests/test_retrieval.py` | EntityExtractor, ContextAssembler tests |
| `tests/test_integration.py` | End-to-end integration test |
| `pyproject.toml` | Project metadata and dependencies |
| `.env` | API keys (gitignored) |

---

## Task 1: Project Scaffolding & Config

**Files:**
- Create: `pyproject.toml`
- Create: `src/memo_agent/__init__.py`
- Create: `src/memo_agent/config.py`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "memo-agent"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "chromadb>=0.5.0",
    "networkx>=3.2",
    "prompt-toolkit>=3.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[project.scripts]
memo-agent = "memo_agent.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create package init**

`src/memo_agent/__init__.py`:
```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create config.py**

`src/memo_agent/config.py`:
```python
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@dataclass
class Config:
    llm_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "all-MiniLM-L6-v2"
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    chroma_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "chroma")
    kg_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "kg")
    kg_file: Path = field(default_factory=lambda: BASE_DIR / "data" / "kg" / "semantic.json")
    reflection_log: Path = field(default_factory=lambda: BASE_DIR / "data" / "reflection_log.jsonl")
    negation_keywords: list[str] = field(default_factory=lambda: [
        "不对", "错了", "不是这样的", "搞反了", "修改学术假设",
        "不正确", "你说错了", "搞错了", "反了",
    ])
    reflection_commands: list[str] = field(default_factory=lambda: [
        "/reflect", "/纠错",
    ])
    max_context_tokens: int = 160000
    context_usage_ratio: float = 0.8
    guideline_max_tokens: int = 0  # 0 = no limit
    subgraph_max_tokens: int = 1000
    episodic_max_tokens: int = 1500
    episodic_top_k: int = 3
    reflection_recent_turns: int = 3

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.kg_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Create .gitignore**

```
__pycache__/
*.pyc
.env
data/
.pytest_cache/
*.egg-info/
dist/
```

- [ ] **Step 5: Create tests/__init__.py**

Empty file.

- [ ] **Step 6: Install and verify**

Run: `pip install -e ".[dev]"`
Expected: successful installation, no errors.

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml src/ tests/__init__.py .gitignore
git commit -m "feat: project scaffolding, config, and dependencies"
```

---

## Task 2: Shared Data Types

**Files:**
- Create: `src/memo_agent/models.py`

- [ ] **Step 1: Write failing test for Guideline dataclass**

`tests/test_models.py`:
```python
from memo_agent.models import Guideline


def test_guideline_creation():
    g = Guideline(
        rule="MAGCN cross-network attention must align features first",
        source_entities=["MAGCN", "cross-network attention"],
        timestamp="2026-05-16T10:00:00",
    )
    assert g.rule == "MAGCN cross-network attention must align features first"
    assert len(g.source_entities) == 2
    assert g.timestamp == "2026-05-16T10:00:00"


def test_guideline_is_dataclass():
    from dataclasses import is_dataclass
    assert is_dataclass(Guideline)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `cannot import name 'Guideline'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/models.py`:
```python
from dataclasses import dataclass, field


@dataclass
class Guideline:
    rule: str
    source_entities: list[str] = field(default_factory=list)
    timestamp: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/models.py tests/test_models.py
git commit -m "feat: add Guideline shared data type"
```

---

## Task 3: Working Memory

**Files:**
- Create: `src/memo_agent/memory/__init__.py`
- Create: `src/memo_agent/memory/working.py`
- Create: `tests/test_working.py`

- [ ] **Step 1: Write failing tests**

`tests/test_working.py`:
```python
from memo_agent.memory.working import WorkingMemory


def test_add_and_get_full_context():
    wm = WorkingMemory()
    wm.add("user", "hello")
    wm.add("assistant", "hi there")
    ctx = wm.get_full_context()
    assert len(ctx) == 2
    assert ctx[0] == {"role": "user", "content": "hello"}
    assert ctx[1] == {"role": "assistant", "content": "hi there"}


def test_get_recent():
    wm = WorkingMemory()
    for i in range(5):
        wm.add("user", f"msg {i}")
    recent = wm.get_recent(3)
    assert len(recent) == 3
    assert recent[0]["content"] == "msg 2"
    assert recent[2]["content"] == "msg 4"


def test_get_recent_more_than_available():
    wm = WorkingMemory()
    wm.add("user", "only one")
    recent = wm.get_recent(5)
    assert len(recent) == 1


def test_clear():
    wm = WorkingMemory()
    wm.add("user", "hello")
    wm.clear()
    assert wm.get_full_context() == []


def test_empty_context():
    wm = WorkingMemory()
    assert wm.get_full_context() == []
    assert wm.get_recent(3) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_working.py -v`
Expected: FAIL — `cannot import name 'WorkingMemory'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/memory/__init__.py`:
```python
```

`src/memo_agent/memory/working.py`:
```python
class WorkingMemory:
    def __init__(self):
        self._messages: list[dict] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def get_recent(self, n: int = 3) -> list[dict]:
        return self._messages[-n:] if n > 0 else []

    def get_full_context(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_working.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/memory/ tests/test_working.py
git commit -m "feat: add WorkingMemory with session-level context storage"
```

---

## Task 4: Semantic Memory (NetworkX KG + JSON)

**Files:**
- Create: `src/memo_agent/memory/semantic.py`
- Create: `tests/test_semantic.py`

- [ ] **Step 1: Write failing tests**

`tests/test_semantic.py`:
```python
import json
import tempfile
from pathlib import Path

import pytest

from memo_agent.memory.semantic import SemanticMemory


@pytest.fixture
def sm(tmp_path):
    kg_file = tmp_path / "semantic.json"
    return SemanticMemory(kg_file=kg_file)


def test_add_and_get_entity(sm):
    node_id = sm.add_entity("MAGCN", "algorithm", {"description": "Multi-modal Graph Convolutional Network"})
    entity = sm.get_entity("MAGCN")
    assert entity is not None
    assert entity["type"] == "entity"
    assert entity["entity_type"] == "algorithm"


def test_get_entity_not_found(sm):
    assert sm.get_entity("NONEXISTENT") is None


def test_add_entity_duplicate_returns_same_id(sm):
    id1 = sm.add_entity("MAGCN", "algorithm", {})
    id2 = sm.add_entity("MAGCN", "algorithm", {})
    assert id1 == id2


def test_add_relation(sm):
    sm.add_entity("MAGCN", "algorithm", {})
    sm.add_entity("cross-network attention", "mechanism", {})
    sm.add_relation("MAGCN", "cross-network attention", "uses")
    sub = sm.get_subgraph(["MAGCN"], depth=1)
    assert "nodes" in sub
    assert any(n["name"] == "cross-network attention" for n in sub["nodes"])


def test_add_guideline(sm):
    sm.add_entity("MAGCN", "algorithm", {})
    sm.add_entity("cross-network attention", "mechanism", {})
    rule_id = sm.add_guideline(
        "MAGCN cross-network attention must align features first",
        related_entities=["MAGCN", "cross-network attention"],
    )
    guidelines = sm.get_guidelines_for("MAGCN")
    assert len(guidelines) == 1
    assert "align features first" in guidelines[0]


def test_get_guidelines_for_no_rules(sm):
    sm.add_entity("MAGCN", "algorithm", {})
    assert sm.get_guidelines_for("MAGCN") == []


def test_get_guidelines_for_nonexistent_entity(sm):
    assert sm.get_guidelines_for("NONEXISTENT") == []


def test_get_subgraph_depth1(sm):
    sm.add_entity("A", "concept", {})
    sm.add_entity("B", "concept", {})
    sm.add_relation("A", "B", "relates_to")
    sub = sm.get_subgraph(["A"], depth=1)
    assert len(sub["nodes"]) == 2
    assert any(n["name"] == "B" for n in sub["nodes"])


def test_get_subgraph_empty_entities(sm):
    sub = sm.get_subgraph([], depth=1)
    assert sub["nodes"] == []
    assert sub["edges"] == []


def test_save_and_load(sm):
    sm.add_entity("MAGCN", "algorithm", {})
    sm.add_guideline("test rule", related_entities=["MAGCN"])
    sm.save()

    sm2 = SemanticMemory(kg_file=sm._kg_file)
    sm2.load()
    assert sm2.get_entity("MAGCN") is not None
    assert len(sm2.get_guidelines_for("MAGCN")) == 1


def test_load_from_nonexistent_file(sm):
    sm.load()  # should not raise, just init empty graph
    assert sm.get_entity("ANYTHING") is None


def test_backup_on_save(sm):
    sm.add_entity("X", "concept", {})
    sm.save()
    sm.add_entity("Y", "concept", {})
    sm.save()
    bak_file = Path(str(sm._kg_file) + ".bak")
    assert bak_file.exists()
    bak_data = json.loads(bak_file.read_text())
    assert any(n[1].get("name") == "X" for n in bak_data["nodes"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_semantic.py -v`
Expected: FAIL — `cannot import name 'SemanticMemory'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/memory/semantic.py`:
```python
import json
import logging
from pathlib import Path

import networkx as nx

logger = logging.getLogger(__name__)


class SemanticMemory:
    def __init__(self, kg_file: Path):
        self._kg_file = Path(kg_file)
        self._graph = nx.DiGraph()

    def add_entity(self, name: str, entity_type: str, properties: dict) -> str:
        existing = self.get_entity(name)
        if existing is not None:
            return existing["node_id"]
        node_id = f"entity_{name}"
        self._graph.add_node(node_id, type="entity", name=name,
                             entity_type=entity_type, properties=properties)
        self.save()
        return node_id

    def add_relation(self, source: str, target: str, relation: str) -> None:
        src_id = self._ensure_entity(source)
        tgt_id = self._ensure_entity(target)
        self._graph.add_edge(src_id, tgt_id, type=relation)
        self.save()

    def add_guideline(self, rule: str, related_entities: list[str]) -> str:
        entity_ids = [self._ensure_entity(e) for e in related_entities]
        rule_id = f"rule_{len(self._graph.nodes)}"
        self._graph.add_node(rule_id, type="rule", name=rule, rule=rule)
        for eid in entity_ids:
            self._graph.add_edge(eid, rule_id, type="governs")
        self.save()
        return rule_id

    def get_entity(self, name: str) -> dict | None:
        for node_id, data in self._graph.nodes(data=True):
            if data.get("name") == name and data.get("type") == "entity":
                return {"node_id": node_id, **data}
        return None

    def get_guidelines_for(self, entity_name: str) -> list[str]:
        entity = self.get_entity(entity_name)
        if entity is None:
            return []
        eid = entity["node_id"]
        guidelines = []
        for _, target, edge_data in self._graph.out_edges(eid, data=True):
            if edge_data.get("type") == "governs":
                node_data = self._graph.nodes[target]
                if node_data.get("type") == "rule":
                    guidelines.append(node_data["rule"])
        return guidelines

    def get_subgraph(self, entity_names: list[str], depth: int = 1) -> dict:
        if not entity_names:
            return {"nodes": [], "edges": []}
        seed_ids = set()
        for name in entity_names:
            entity = self.get_entity(name)
            if entity:
                seed_ids.add(entity["node_id"])
        if not seed_ids:
            return {"nodes": [], "edges": []}
        visited_nodes = set()
        visited_edges = []
        frontier = seed_ids
        for _ in range(depth + 1):
            next_frontier = set()
            for nid in frontier:
                if nid in visited_nodes:
                    continue
                visited_nodes.add(nid)
                for src, tgt, edata in self._graph.edges(nid, data=True):
                    visited_edges.append({
                        "source": self._graph.nodes[src].get("name", src),
                        "target": self._graph.nodes[tgt].get("name", tgt),
                        "relation": edata.get("type", ""),
                    })
                    if tgt not in visited_nodes:
                        next_frontier.add(tgt)
                for src, tgt, edata in self._graph.in_edges(nid, data=True):
                    visited_edges.append({
                        "source": self._graph.nodes[src].get("name", src),
                        "target": self._graph.nodes[tgt].get("name", tgt),
                        "relation": edata.get("type", ""),
                    })
                    if src not in visited_nodes:
                        next_frontier.add(src)
            frontier = next_frontier
        nodes = [{"name": self._graph.nodes[nid].get("name", nid),
                   "type": self._graph.nodes[nid].get("type", ""),
                   **self._graph.nodes[nid]}
                  for nid in visited_nodes]
        return {"nodes": nodes, "edges": visited_edges}

    def save(self) -> None:
        self._kg_file.parent.mkdir(parents=True, exist_ok=True)
        bak_file = Path(str(self._kg_file) + ".bak")
        if self._kg_file.exists():
            bak_file.write_text(self._kg_file.read_text())
        data = nx.node_link_data(self._graph)
        self._kg_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load(self) -> None:
        if not self._kg_file.exists():
            self._graph = nx.DiGraph()
            return
        try:
            data = json.loads(self._kg_file.read_text())
            self._graph = nx.node_link_graph(data, directed=True)
        except (json.JSONDecodeError, KeyError):
            logger.warning("KG file corrupted, loading backup")
            bak_file = Path(str(self._kg_file) + ".bak")
            if bak_file.exists():
                data = json.loads(bak_file.read_text())
                self._graph = nx.node_link_graph(data, directed=True)
            else:
                self._graph = nx.DiGraph()

    def _ensure_entity(self, name: str) -> str:
        existing = self.get_entity(name)
        if existing:
            return existing["node_id"]
        return self.add_entity(name, "concept", {})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_semantic.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/memory/semantic.py tests/test_semantic.py
git commit -m "feat: add SemanticMemory with NetworkX KG and JSON persistence"
```

---

## Task 5: Episodic Memory (ChromaDB)

**Files:**
- Create: `src/memo_agent/memory/episodic.py`
- Create: `tests/test_episodic.py`

- [ ] **Step 1: Write failing tests**

`tests/test_episodic.py`:
```python
import tempfile
from pathlib import Path

import pytest

from memo_agent.memory.episodic import EpisodicMemory


@pytest.fixture
def em(tmp_path):
    return EpisodicMemory(persist_dir=tmp_path, embedding_model_name="all-MiniLM-L6-v2")


def test_store_and_search(em):
    em.store("conv1", {"role": "user", "content": "HGNN uses heterogeneous graph structures for drug-disease prediction"},
             metadata={"conversation_id": "conv1", "timestamp": "2026-01-01", "entities": ["HGNN"]})
    em.store("conv1", {"role": "assistant", "content": "Graph neural networks process node features via message passing"},
             metadata={"conversation_id": "conv1", "timestamp": "2026-01-01", "entities": ["GNN"]})
    results = em.search("heterogeneous graph drug prediction", top_k=1)
    assert len(results) >= 1
    assert "HGNN" in results[0]["content"] or "heterogeneous" in results[0]["content"].lower()


def test_search_returns_metadata(em):
    em.store("conv2", {"role": "user", "content": "MAGCN feature fusion"},
             metadata={"conversation_id": "conv2", "timestamp": "2026-01-02", "entities": ["MAGCN"]})
    results = em.search("MAGCN", top_k=1)
    assert len(results) >= 1
    assert "conversation_id" in results[0]["metadata"]


def test_get_by_conversation(em):
    em.store("conv3", {"role": "user", "content": "msg1"},
             metadata={"conversation_id": "conv3", "timestamp": "2026-01-03", "entities": []})
    em.store("conv3", {"role": "assistant", "content": "msg2"},
             metadata={"conversation_id": "conv3", "timestamp": "2026-01-03", "entities": []})
    em.store("conv4", {"role": "user", "content": "msg3"},
             metadata={"conversation_id": "conv4", "timestamp": "2026-01-04", "entities": []})
    results = em.get_by_conversation("conv3")
    assert len(results) == 2


def test_search_empty_db(em):
    results = em.search("anything", top_k=5)
    assert results == []


def test_persistence(tmp_path):
    em1 = EpisodicMemory(persist_dir=tmp_path, embedding_model_name="all-MiniLM-L6-v2")
    em1.store("conv1", {"role": "user", "content": "test persistence"},
              metadata={"conversation_id": "conv1", "timestamp": "2026-01-01", "entities": []})
    del em1
    em2 = EpisodicMemory(persist_dir=tmp_path, embedding_model_name="all-MiniLM-L6-v2")
    results = em2.search("persistence", top_k=1)
    assert len(results) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_episodic.py -v`
Expected: FAIL — `cannot import name 'EpisodicMemory'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/memory/episodic.py`:
```python
import logging
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class EpisodicMemory:
    def __init__(self, persist_dir: Path, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self._persist_dir = str(persist_dir)
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        self._collection = self._client.get_or_create_collection(
            name="episodic",
            embedding_function=self._embedding_fn,
        )

    def store(self, conversation_id: str, turn: dict, metadata: dict) -> None:
        doc_id = f"{conversation_id}_{self._collection.count()}"
        content = turn.get("content", "")
        meta = {
            "conversation_id": metadata.get("conversation_id", conversation_id),
            "timestamp": metadata.get("timestamp", ""),
            "entities": ",".join(metadata.get("entities", [])),
        }
        try:
            self._collection.add(doc_id, document=content, metadata=meta)
        except Exception as e:
            logger.error(f"EpisodicMemory store failed: {e}")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        try:
            results = self._collection.query(query_texts=[query], n_results=top_k)
        except Exception as e:
            logger.error(f"EpisodicMemory search failed: {e}")
            return []
        if not results["documents"] or not results["documents"][0]:
            return []
        items = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0.0
            entities_str = meta.get("entities", "")
            meta["entities"] = [e for e in entities_str.split(",") if e]
            items.append({"content": doc, "metadata": meta, "distance": dist})
        return items

    def get_by_conversation(self, conversation_id: str) -> list[dict]:
        try:
            results = self._collection.get(
                where={"conversation_id": conversation_id},
            )
        except Exception as e:
            logger.error(f"EpisodicMemory get_by_conversation failed: {e}")
            return []
        if not results["documents"]:
            return []
        items = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            entities_str = meta.get("entities", "")
            meta["entities"] = [e for e in entities_str.split(",") if e]
            items.append({"content": doc, "metadata": meta})
        return items

    def clear(self) -> None:
        self._client.delete_collection("episodic")
        self._collection = self._client.get_or_create_collection(
            name="episodic",
            embedding_function=self._embedding_fn,
        )
```

- [ ] **Step 4: Install sentence-transformers dependency and run test**

Run: `pip install sentence-transformers && pytest tests/test_episodic.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/memory/episodic.py tests/test_episodic.py pyproject.toml
git commit -m "feat: add EpisodicMemory with ChromaDB vector store"
```

---

## Task 6: Reflection Detector

**Files:**
- Create: `src/memo_agent/reflection/__init__.py`
- Create: `src/memo_agent/reflection/detector.py`
- Create: `tests/test_reflection.py` (detector section)

- [ ] **Step 1: Write failing tests**

`tests/test_reflection.py`:
```python
import pytest

from memo_agent.reflection.detector import ReflectionDetector
from memo_agent.config import Config


@pytest.fixture
def detector():
    return ReflectionDetector(Config())


def test_detect_keyword(detector):
    assert detector.check("不对，MAGCN不是这样处理的") is True


def test_detect_keyword_2(detector):
    assert detector.check("你搞反了") is True


def test_detect_command(detector):
    assert detector.check("/reflect") is True


def test_detect_command_2(detector):
    assert detector.check("/纠错") is True


def test_no_false_positive(detector):
    assert detector.check("请分析HGNN在药物预测中的应用") is False


def test_no_false_positive_2(detector):
    assert detector.check("对的，这个思路很好") is False


def test_extract_correction(detector):
    result = detector.extract_correction("不对，TARSL是各向异性的")
    assert result is not None
    assert result["trigger"] == "不对，TARSL是各向异性的"
    assert "各向异性" in result["hint"]


def test_extract_correction_no_keyword(detector):
    result = detector.extract_correction("请继续分析")
    assert result is None


def test_extract_correction_command(detector):
    result = detector.extract_correction("/reflect")
    assert result is not None
    assert result["trigger"] == "/reflect"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reflection.py -v`
Expected: FAIL — `cannot import name 'ReflectionDetector'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/reflection/__init__.py`:
```python
```

`src/memo_agent/reflection/detector.py`:
```python
import re

from memo_agent.config import Config


class ReflectionDetector:
    def __init__(self, config: Config):
        self._keywords = config.negation_keywords
        self._commands = config.reflection_commands

    def check(self, user_input: str) -> bool:
        stripped = user_input.strip()
        if stripped in self._commands:
            return True
        for kw in self._keywords:
            if kw in stripped:
                return True
        return False

    def extract_correction(self, user_input: str) -> dict | None:
        if not self.check(user_input):
            return None
        stripped = user_input.strip()
        hint = stripped
        for kw in self._keywords:
            hint = hint.replace(kw, "", 1)
        hint = hint.strip().lstrip(",，、").strip()
        return {"trigger": stripped, "hint": hint if hint else stripped}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_reflection.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/reflection/ tests/test_reflection.py
git commit -m "feat: add ReflectionDetector with keyword and command triggers"
```

---

## Task 7: Reflector

**Files:**
- Modify: `src/memo_agent/reflection/reflector.py` (create)
- Modify: `tests/test_reflection.py` (add reflector tests)

- [ ] **Step 1: Add failing tests to test_reflection.py**

Append to `tests/test_reflection.py`:
```python
from unittest.mock import MagicMock

from memo_agent.reflection.reflector import Reflector
from memo_agent.models import Guideline


@pytest.fixture
def reflector():
    mock_llm = MagicMock()
    return Reflector(llm=mock_llm)


def test_reflect_extracts_guideline(reflector):
    reflector._llm.invoke.return_value = MagicMock(
        content='[Guideline] TARSL uses relation-specific projections for anisotropic attention'
    )
    error_context = [
        {"role": "user", "content": "分析TARSL"},
        {"role": "assistant", "content": "TARSL uses isotropic attention"},
        {"role": "user", "content": "不对，TARSL是各向异性的"},
    ]
    correction = {"trigger": "不对，TARSL是各向异性的", "hint": "TARSL是各向异性的"}
    result = reflector.reflect(error_context, correction)
    assert result is not None
    assert isinstance(result, Guideline)
    assert "TARSL" in result.source_entities or "TARSL" in result.rule
    assert result.timestamp != ""


def test_reflect_returns_none_on_invalid_output(reflector):
    reflector._llm.invoke.return_value = MagicMock(
        content="I cannot determine the error source."
    )
    error_context = [{"role": "user", "content": "test"}]
    correction = {"trigger": "错了", "hint": "something else"}
    result = reflector.reflect(error_context, correction)
    assert result is None


def test_reflect_uses_reflection_prompt(reflector):
    reflector._llm.invoke.return_value = MagicMock(
        content='[Guideline] Test rule'
    )
    error_context = [{"role": "user", "content": "test"}]
    correction = {"trigger": "错了", "hint": "correct way"}
    reflector.reflect(error_context, correction)
    call_args = reflector._llm.invoke.call_args[0][0]
    assert "学术推理审查器" in call_args
    assert "test" in call_args
    assert "correct way" in call_args
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reflection.py::test_reflect_extracts_guideline -v`
Expected: FAIL — `cannot import name 'Reflector'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/reflection/reflector.py`:
```python
import logging
from datetime import datetime, timezone

from memo_agent.models import Guideline

logger = logging.getLogger(__name__)

REFLECTION_PROMPT = """你是一个学术推理审查器。以下是一个错误的学术推导案例：

【错误上下文】
{error_context}

【用户纠正】
{correction_hint}

请分析：
1. 错误根源：Agent 混淆了什么概念？遗漏了什么约束？
2. 正确逻辑：应当如何推导？

基于以上分析，提取一条普适性规则，格式：
[Guideline] {{一条具体的、可执行的学术推理规则}}"""


class Reflector:
    def __init__(self, llm):
        self._llm = llm

    def reflect(self, error_context: list[dict], correction_hint: dict) -> Guideline | None:
        context_text = "\n".join(
            f"{t['role']}: {t['content']}" for t in error_context
        )
        prompt = REFLECTION_PROMPT.format(
            error_context=context_text,
            correction_hint=correction_hint.get("hint", correction_hint.get("trigger", "")),
        )
        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Reflector LLM call failed: {e}")
            return None

        guideline_text = self._parse_guideline(content)
        if guideline_text is None:
            logger.warning(f"Failed to extract Guideline from: {content[:200]}")
            return None

        entities = self._extract_entities_from_hint(correction_hint)
        return Guideline(
            rule=guideline_text,
            source_entities=entities,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _parse_guideline(self, text: str) -> str | None:
        marker = "[Guideline]"
        idx = text.find(marker)
        if idx == -1:
            return None
        rule = text[idx + len(marker):].strip()
        return rule if rule else None

    def _extract_entities_from_hint(self, correction_hint: dict) -> list[str]:
        hint = correction_hint.get("hint", "")
        if not hint:
            return []
        words = hint.replace("，", " ").replace("、", " ").replace("的", " ").split()
        entities = [w.strip() for w in words if len(w.strip()) >= 2]
        return entities[:5]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_reflection.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/reflection/reflector.py tests/test_reflection.py
git commit -m "feat: add Reflector with CoT reflection and Guideline extraction"
```

---

## Task 8: KG Updater

**Files:**
- Create: `src/memo_agent/reflection/kg_updater.py`
- Modify: `tests/test_reflection.py` (add kg_updater tests)

- [ ] **Step 1: Add failing tests to test_reflection.py**

Append to `tests/test_reflection.py`:
```python
from memo_agent.reflection.kg_updater import KGUpdater
from memo_agent.memory.semantic import SemanticMemory


@pytest.fixture
def kg_updater(tmp_path):
    from pathlib import Path
    sm = SemanticMemory(kg_file=tmp_path / "semantic.json")
    return KGUpdater()


def test_apply_guideline_creates_rule_node(kg_updater, tmp_path):
    sm = SemanticMemory(kg_file=tmp_path / "semantic.json")
    sm.add_entity("MAGCN", "algorithm", {})
    sm.add_entity("cross-network attention", "mechanism", {})
    guideline = Guideline(
        rule="MAGCN cross-network attention must align features first",
        source_entities=["MAGCN", "cross-network attention"],
        timestamp="2026-05-16T10:00:00",
    )
    kg_updater.apply_guideline(guideline, sm)
    guidelines = sm.get_guidelines_for("MAGCN")
    assert len(guidelines) == 1
    assert "align features first" in guidelines[0]


def test_apply_guideline_creates_missing_entities(kg_updater, tmp_path):
    sm = SemanticMemory(kg_file=tmp_path / "semantic.json")
    guideline = Guideline(
        rule="Test rule for NEW_ENTITY",
        source_entities=["NEW_ENTITY"],
        timestamp="2026-05-16T10:00:00",
    )
    kg_updater.apply_guideline(guideline, sm)
    assert sm.get_entity("NEW_ENTITY") is not None
    assert len(sm.get_guidelines_for("NEW_ENTITY")) == 1


def test_apply_guideline_dedup(kg_updater, tmp_path):
    sm = SemanticMemory(kg_file=tmp_path / "semantic.json")
    sm.add_entity("X", "concept", {})
    g1 = Guideline(rule="X must be processed carefully", source_entities=["X"], timestamp="2026-01-01")
    g2 = Guideline(rule="X must be processed carefully and thoroughly", source_entities=["X"], timestamp="2026-01-02")
    kg_updater.apply_guideline(g1, sm)
    kg_updater.apply_guideline(g2, sm)
    guidelines = sm.get_guidelines_for("X")
    assert len(guidelines) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reflection.py::test_apply_guideline_creates_rule_node -v`
Expected: FAIL — `cannot import name 'KGUpdater'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/reflection/kg_updater.py`:
```python
import logging

from memo_agent.models import Guideline
from memo_agent.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)


class KGUpdater:
    def apply_guideline(self, guideline: Guideline, semantic: SemanticMemory) -> None:
        if self._is_duplicate(guideline.rule, semantic):
            logger.warning(f"Duplicate Guideline skipped: {guideline.rule[:80]}")
            return
        for entity_name in guideline.source_entities:
            if semantic.get_entity(entity_name) is None:
                semantic.add_entity(entity_name, "concept", {})
        semantic.add_guideline(guideline.rule, related_entities=guideline.source_entities)
        logger.info(f"Guideline applied: {guideline.rule[:80]}")

    def _is_duplicate(self, new_rule: str, semantic: SemanticMemory) -> bool:
        for _, data in semantic._graph.nodes(data=True):
            if data.get("type") == "rule":
                existing = data.get("rule", "")
                if existing and (existing in new_rule or new_rule in existing):
                    return True
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_reflection.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/reflection/kg_updater.py tests/test_reflection.py
git commit -m "feat: add KGUpdater with dedup check for Guideline nodes"
```

---

## Task 9: Reflection Log (Observability)

**Files:**
- Modify: `src/memo_agent/reflection/kg_updater.py` (add logging)
- Add test for log output in `tests/test_reflection.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_reflection.py`:
```python
def test_apply_guideline_writes_reflection_log(kg_updater, tmp_path):
    from pathlib import Path
    import json
    log_file = tmp_path / "reflection_log.jsonl"
    sm = SemanticMemory(kg_file=tmp_path / "semantic.json")
    sm.add_entity("Y", "concept", {})
    guideline = Guideline(
        rule="Y requires special handling",
        source_entities=["Y"],
        timestamp="2026-05-16T10:00:00",
    )
    kg_updater.apply_guideline(guideline, sm, log_file=log_file)
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["rule"] == "Y requires special handling"
    assert "trigger" not in entry  # trigger comes from orchestrator, not updater
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reflection.py::test_apply_guideline_writes_reflection_log -v`
Expected: FAIL — `apply_guideline() got an unexpected keyword argument 'log_file'`

- [ ] **Step 3: Update implementation to write reflection log**

Replace `src/memo_agent/reflection/kg_updater.py`:
```python
import json
import logging
from pathlib import Path

from memo_agent.models import Guideline
from memo_agent.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)


class KGUpdater:
    def apply_guideline(self, guideline: Guideline, semantic: SemanticMemory,
                        log_file: Path | None = None) -> None:
        if self._is_duplicate(guideline.rule, semantic):
            logger.warning(f"Duplicate Guideline skipped: {guideline.rule[:80]}")
            return
        for entity_name in guideline.source_entities:
            if semantic.get_entity(entity_name) is None:
                semantic.add_entity(entity_name, "concept", {})
        semantic.add_guideline(guideline.rule, related_entities=guideline.source_entities)
        logger.info(f"Guideline applied: {guideline.rule[:80]}")
        if log_file is not None:
            self._write_log(log_file, guideline)

    def _write_log(self, log_file: Path, guideline: Guideline) -> None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "rule": guideline.rule,
            "source_entities": guideline.source_entities,
            "timestamp": guideline.timestamp,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _is_duplicate(self, new_rule: str, semantic: SemanticMemory) -> bool:
        for _, data in semantic._graph.nodes(data=True):
            if data.get("type") == "rule":
                existing = data.get("rule", "")
                if existing and (existing in new_rule or new_rule in existing):
                    return True
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_reflection.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/reflection/kg_updater.py tests/test_reflection.py
git commit -m "feat: add reflection log writing to KGUpdater"
```

---

## Task 10: Entity Extractor

**Files:**
- Create: `src/memo_agent/retrieval/__init__.py`
- Create: `src/memo_agent/retrieval/entity_extractor.py`
- Create: `tests/test_retrieval.py`

- [ ] **Step 1: Write failing tests**

`tests/test_retrieval.py`:
```python
from unittest.mock import MagicMock

import pytest

from memo_agent.retrieval.entity_extractor import EntityExtractor


@pytest.fixture
def extractor():
    mock_llm = MagicMock()
    return EntityExtractor(llm=mock_llm)


def test_extract_entities(extractor):
    extractor._llm.invoke.return_value = MagicMock(content="MAGCN\n跨网络注意力\n链路预测")
    result = extractor.extract("我准备用MAGCN做链路预测，结合跨网络注意力机制")
    assert "MAGCN" in result
    assert "跨网络注意力" in result
    assert "链路预测" in result


def test_extract_entities_caches_result(extractor):
    extractor._llm.invoke.return_value = MagicMock(content="HGNN")
    r1 = extractor.extract("分析HGNN")
    r2 = extractor.extract("分析HGNN")
    assert r1 == r2
    assert extractor._llm.invoke.call_count == 1


def test_extract_entities_empty_input(extractor):
    extractor._llm.invoke.return_value = MagicMock(content="")
    result = extractor.extract("今天天气不错")
    assert result == []


def test_extract_entities_handles_none_response(extractor):
    extractor._llm.invoke.return_value = MagicMock(content="")
    result = extractor.extract("hello")
    assert isinstance(result, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_retrieval.py -v`
Expected: FAIL — `cannot import name 'EntityExtractor'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/retrieval/__init__.py`:
```python
```

`src/memo_agent/retrieval/entity_extractor.py`:
```python
import hashlib
import logging

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """从以下文本中提取学术/技术实体（算法名、方法名、数据集、领域术语）。
仅返回实体列表，每行一个，不要解释。如果没有学术实体，返回空。

文本：{text}"""


class EntityExtractor:
    def __init__(self, llm):
        self._llm = llm
        self._cache: dict[str, list[str]] = {}

    def extract(self, text: str) -> list[str]:
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        prompt = EXTRACTION_PROMPT.format(text=text)
        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"EntityExtractor LLM call failed: {e}")
            return []
        entities = [line.strip() for line in content.strip().split("\n") if line.strip()]
        self._cache[cache_key] = entities
        return entities
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_retrieval.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/retrieval/ tests/test_retrieval.py
git commit -m "feat: add EntityExtractor with LLM-based extraction and caching"
```

---

## Task 11: Context Assembler

**Files:**
- Create: `src/memo_agent/retrieval/context_assembler.py`
- Modify: `tests/test_retrieval.py` (add context assembler tests)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_retrieval.py`:
```python
from unittest.mock import MagicMock, patch

from memo_agent.retrieval.context_assembler import ContextAssembler
from memo_agent.memory.working import WorkingMemory
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory


@pytest.fixture
def assembler(tmp_path):
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = ["MAGCN"]
    sm = SemanticMemory(kg_file=tmp_path / "semantic.json")
    sm.add_entity("MAGCN", "algorithm", {})
    sm.add_guideline("MAGCN must align features first", related_entities=["MAGCN"])
    return ContextAssembler(entity_extractor=mock_extractor), sm


def test_assemble_includes_guidelines(assembler, tmp_path):
    ca, sm = assembler
    wm = WorkingMemory()
    wm.add("user", "分析MAGCN")
    mock_episodic = MagicMock()
    mock_episodic.search.return_value = []
    result = ca.assemble("分析MAGCN", wm, mock_episodic, sm)
    assert "学术审查规则" in result
    assert "align features first" in result


def test_assemble_omits_empty_sections(assembler, tmp_path):
    ca, sm = assembler
    wm = WorkingMemory()
    wm.add("user", "分析MAGCN")
    mock_episodic = MagicMock()
    mock_episodic.search.return_value = []
    result = ca.assemble("分析MAGCN", wm, mock_episodic, sm)
    assert "相关历史讨论" not in result


def test_assemble_includes_episodic_when_present(assembler, tmp_path):
    ca, sm = assembler
    wm = WorkingMemory()
    wm.add("user", "分析MAGCN")
    mock_episodic = MagicMock()
    mock_episodic.search.return_value = [
        {"content": "Previously discussed MAGCN", "metadata": {"conversation_id": "c1", "timestamp": "2026-01-01"}, "distance": 0.3}
    ]
    result = ca.assemble("分析MAGCN", wm, mock_episodic, sm)
    assert "相关历史讨论" in result
    assert "Previously discussed MAGCN" in result


def test_assemble_includes_user_input(assembler, tmp_path):
    ca, sm = assembler
    wm = WorkingMemory()
    wm.add("user", "分析MAGCN")
    mock_episodic = MagicMock()
    mock_episodic.search.return_value = []
    result = ca.assemble("分析MAGCN", wm, mock_episodic, sm)
    assert "分析MAGCN" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_retrieval.py::test_assemble_includes_guidelines -v`
Expected: FAIL — `cannot import name 'ContextAssembler'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/retrieval/context_assembler.py`:
```python
import logging

from memo_agent.memory.working import WorkingMemory
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.retrieval.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)


class ContextAssembler:
    def __init__(self, entity_extractor: EntityExtractor, max_subgraph_tokens: int = 1000,
                 max_episodic_tokens: int = 1500, max_context_tokens: int = 128000):
        self._entity_extractor = entity_extractor
        self._max_subgraph_tokens = max_subgraph_tokens
        self._max_episodic_tokens = max_episodic_tokens
        self._max_context_tokens = int(max_context_tokens * 0.8)

    def assemble(self, user_input: str, working: WorkingMemory,
                 episodic: EpisodicMemory, semantic: SemanticMemory) -> str:
        entities = self._entity_extractor.extract(user_input)
        sections = []

        # Priority 1: Guidelines — never truncated
        guidelines = []
        if entities:
            for entity in entities:
                guidelines.extend(semantic.get_guidelines_for(entity))

        if guidelines:
            rule_lines = "\n".join(f"- {g}" for g in guidelines)
            sections.append(("guidelines", f"【学术审查规则 - 你必须严格遵守】\n{rule_lines}"))

        # Priority 2: Knowledge subgraph — truncate to max_subgraph_tokens
        knowledge = ""
        if entities:
            subgraph = semantic.get_subgraph(entities, depth=1)
            if subgraph["nodes"]:
                parts = []
                for node in subgraph["nodes"]:
                    parts.append(f"  {node['name']} ({node.get('entity_type', node.get('type', ''))})")
                for edge in subgraph["edges"]:
                    parts.append(f"  {edge['source']} --[{edge['relation']}]--> {edge['target']}")
                knowledge = "\n".join(parts)
        if knowledge:
            knowledge = self._truncate(knowledge, self._max_subgraph_tokens)
            sections.append(("subgraph", f"【相关知识】\n{knowledge}"))

        # Priority 3: Episodic memory — truncate to max_episodic_tokens
        episodic_results = episodic.search(user_input, top_k=3)
        if episodic_results:
            history_parts = []
            for item in episodic_results:
                cid = item["metadata"].get("conversation_id", "unknown")
                ts = item["metadata"].get("timestamp", "unknown")
                history_parts.append(f"[{cid} @ {ts}] {item['content']}")
            history_text = "\n".join(history_parts)
            history_text = self._truncate(history_text, self._max_episodic_tokens)
            sections.append(("episodic", f"【相关历史讨论】\n{history_text}"))

        # Priority 4: Current conversation — truncate oldest turns first
        current_ctx = working.get_full_context()
        if current_ctx:
            conv_lines = [f"{msg['role']}: {msg['content']}" for msg in current_ctx]
            conv_text = self._truncate_list(conv_lines, self._remaining_budget(sections))
            if conv_text:
                sections.append(("context", f"【当前对话】\n{conv_text}"))

        sections.append(("user", f"【用户最新输入】\n{user_input}"))

        return "\n\n".join(text for _, text in sections)

    @staticmethod
    def _truncate(text: str, max_tokens: int) -> str:
        # Rough estimate: 1 token ≈ 1.5 chars for mixed CJK/English
        max_chars = int(max_tokens * 1.5)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    @staticmethod
    def _truncate_list(lines: list[str], max_tokens: int) -> str:
        max_chars = int(max_tokens * 1.5)
        result_chars = 0
        kept = []
        for line in lines:
            if result_chars + len(line) > max_chars:
                break
            kept.append(line)
            result_chars += len(line)
        return "\n".join(kept)

    def _remaining_budget(self, sections: list[tuple[str, str]]) -> int:
        used = sum(int(len(text) / 1.5) for _, text in sections)
        return max(self._max_context_tokens - used, 2000)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_retrieval.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/retrieval/context_assembler.py tests/test_retrieval.py
git commit -m "feat: add ContextAssembler with priority-based prompt assembly"
```

---

## Task 12: Orchestrator

**Files:**
- Create: `src/memo_agent/orchestrator.py`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

`tests/test_integration.py`:
```python
import uuid
from unittest.mock import MagicMock

import pytest

from memo_agent.config import Config
from memo_agent.memory.working import WorkingMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.orchestrator import Orchestrator


@pytest.fixture
def orch(tmp_path):
    config = Config()
    config.kg_file = tmp_path / "semantic.json"
    config.reflection_log = tmp_path / "reflection_log.jsonl"
    config.chroma_dir = tmp_path / "chroma"

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content="MAGCN uses cross-network attention for feature fusion."
    )
    orch = Orchestrator(config=config, llm=mock_llm)
    return orch


def test_normal_turn(orch):
    response = orch.run_turn("请分析MAGCN")
    assert response != ""
    assert len(orch.working.get_full_context()) == 2  # user + assistant


def test_reflection_turn(orch):
    orch.run_turn("请分析TARSL")
    mock_reflect_llm = MagicMock()
    mock_reflect_llm.invoke.return_value = MagicMock(
        content="[Guideline] TARSL uses relation-specific projections for anisotropic attention"
    )
    orch._reflector._llm = mock_reflect_llm
    response = orch.run_turn("不对，TARSL是各向异性的")
    assert "Guideline" in response or "规则" in response or "已成功" in response
    guidelines = orch.semantic.get_guidelines_for("TARSL")
    assert len(guidelines) >= 1


def test_reflection_carries_forward(orch):
    orch.run_turn("请分析TARSL")
    mock_reflect_llm = MagicMock()
    mock_reflect_llm.invoke.return_value = MagicMock(
        content="[Guideline] TARSL uses relation-specific projections for anisotropic attention"
    )
    orch._reflector._llm = mock_reflect_llm
    orch.run_turn("不对，TARSL是各向异性的")
    orch._llm.invoke.return_value = MagicMock(
        content="TARSL employs relation-specific projections for anisotropic attention."
    )
    orch.run_turn("重新分析TARSL")
    last_call = orch._llm.invoke.call_args[0][0]
    assert "学术审查规则" in last_call or "TARSL" in last_call


def test_session_start_and_quit(orch):
    orch.start_session()
    assert orch._conversation_id != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_integration.py -v`
Expected: FAIL — `cannot import name 'Orchestrator'`

- [ ] **Step 3: Write implementation**

`src/memo_agent/orchestrator.py`:
```python
import logging
import uuid

from memo_agent.config import Config
from memo_agent.memory.working import WorkingMemory
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.reflection.detector import ReflectionDetector
from memo_agent.reflection.reflector import Reflector
from memo_agent.reflection.kg_updater import KGUpdater
from memo_agent.retrieval.entity_extractor import EntityExtractor
from memo_agent.retrieval.context_assembler import ContextAssembler

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, config: Config, llm):
        self._config = config
        self._llm = llm
        self._conversation_id = ""

        self.working = WorkingMemory()
        self.semantic = SemanticMemory(kg_file=config.kg_file)
        self.semantic.load()

        self.episodic = EpisodicMemory(
            persist_dir=config.chroma_dir,
            embedding_model_name=config.embedding_model,
        )

        self._detector = ReflectionDetector(config)
        self._reflector = Reflector(llm)
        self._kg_updater = KGUpdater()
        self._entity_extractor = EntityExtractor(llm)
        self._context_assembler = ContextAssembler(self._entity_extractor)

    def start_session(self) -> None:
        self._conversation_id = uuid.uuid4().hex[:8]
        self.working.clear()
        logger.info(f"Session started: {self._conversation_id}")

    def run_turn(self, user_input: str) -> str:
        self.working.add("user", user_input)

        if self._detector.check(user_input):
            return self._handle_reflection(user_input)

        context = self._context_assembler.assemble(
            user_input, self.working, self.episodic, self.semantic
        )

        try:
            response = self._llm.invoke(context)
            response_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            response_text = "推理暂时不可用，请稍后重试。"

        self.working.add("assistant", response_text)

        entities = self._entity_extractor.extract(user_input)
        self.episodic.store(
            self._conversation_id,
            {"role": "assistant", "content": response_text},
            metadata={
                "conversation_id": self._conversation_id,
                "timestamp": self._get_timestamp(),
                "entities": entities,
            },
        )

        return response_text

    def _handle_reflection(self, user_input: str) -> str:
        correction = self._detector.extract_correction(user_input)
        if correction is None:
            return "未能识别纠正内容。"

        error_context = self.working.get_recent(self._config.reflection_recent_turns)
        guideline = self._reflector.reflect(error_context, correction)

        if guideline is None:
            return "未能提取有效规则。"

        self._kg_updater.apply_guideline(
            guideline, self.semantic, log_file=self._config.reflection_log
        )

        return f"已成功提取 Guideline: \"{guideline.rule[:80]}\" 并绑定至语义记忆。"

    @staticmethod
    def _get_timestamp() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memo_agent/orchestrator.py tests/test_integration.py
git commit -m "feat: add Orchestrator with reflection detection and memory coordination"
```

---

## Task 13: CLI

**Files:**
- Create: `src/memo_agent/cli.py`

- [ ] **Step 1: Write implementation**

`src/memo_agent/cli.py`:
```python
import sys
import logging

from dotenv import load_dotenv

from memo_agent.config import Config
from memo_agent.orchestrator import Orchestrator

load_dotenv()

HELP_TEXT = """可用命令：
  /help              显示帮助
  /quit              退出并保存
  /reflect           手动触发反思
  /memory status     显示三级记忆状态
  /memory clear episodic  清空情节记忆
  /guidelines        列出所有已沉淀的 Guidelines
"""


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    config = Config()

    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model=config.llm_model, max_tokens=4096)

    orch = Orchestrator(config=config, llm=llm)
    orch.start_session()

    print("MemoAgent 已启动。输入 /help 查看命令，/quit 退出。")

    try:
        from prompt_toolkit import prompt as pt_prompt
        use_prompt_toolkit = True
    except ImportError:
        use_prompt_toolkit = False

    while True:
        try:
            if use_prompt_toolkit:
                user_input = pt_prompt("User >> ").strip()
            else:
                user_input = input("User >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("再见！")
            break

        if user_input == "/help":
            print(HELP_TEXT)
            continue

        if user_input == "/guidelines":
            _print_guidelines(orch)
            continue

        if user_input == "/memory status":
            _print_memory_status(orch)
            continue

        if user_input == "/memory clear episodic":
            orch.episodic.clear()
            print("情节记忆已清空。")
            continue

        if user_input == "/reflect":
            try:
                correction = input("请输入纠正内容: ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if correction:
                user_input = f"不对，{correction}"
            else:
                continue

        response = orch.run_turn(user_input)
        print(f"Agent >> {response}")


def _print_memory_status(orch: Orchestrator):
    entity_count = sum(1 for _, d in orch.semantic._graph.nodes(data=True) if d.get("type") == "entity")
    rule_count = sum(1 for _, d in orch.semantic._graph.nodes(data=True) if d.get("type") == "rule")
    try:
        conv_count = orch.episodic._collection.count()
    except Exception:
        conv_count = 0
    print(f"语义记忆: {entity_count} 个实体, {rule_count} 条 Guidelines")
    print(f"情节记忆: {conv_count} 条对话记录")
    print(f"工作记忆: {len(orch.working.get_full_context())} 轮当前对话")


def _print_guidelines(orch: Orchestrator):
    rules = []
    for _, data in orch.semantic._graph.nodes(data=True):
        if data.get("type") == "rule":
            rules.append(data.get("rule", ""))
    if not rules:
        print("暂无 Guidelines。")
        return
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI entry point is registered**

Run: `pip install -e . && memo-agent --help 2>&1 || echo "entry point installed"`
Expected: No import errors (may show usage help or start REPL; if REPL starts, Ctrl+C to exit)

- [ ] **Step 3: Commit**

```bash
git add src/memo_agent/cli.py
git commit -m "feat: add CLI REPL with commands for memory inspection and reflection"
```

---

## Task 14: Final Integration Verification

**Files:**
- No new files; run full test suite

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run a smoke test of the CLI**

Run: `echo "/quit" | memo-agent 2>&1 | head -5`
Expected: Shows "MemoAgent 已启动" and "再见！"

- [ ] **Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "chore: final integration verification and fixes"
```
