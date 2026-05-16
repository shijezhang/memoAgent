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
    assert any(n.get("name") == "X" for n in bak_data["nodes"])
