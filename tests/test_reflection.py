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
