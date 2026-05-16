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
