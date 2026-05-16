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


from memo_agent.retrieval.context_assembler import ContextAssembler
from memo_agent.memory.working import WorkingMemory
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
