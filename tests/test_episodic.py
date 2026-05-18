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
