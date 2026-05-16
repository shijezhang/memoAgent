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
