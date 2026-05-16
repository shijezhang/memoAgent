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
