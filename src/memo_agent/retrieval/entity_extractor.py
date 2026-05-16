import hashlib
import logging
from typing import List

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """从以下文本中提取学术/技术实体（算法名、方法名、数据集、领域术语）。
仅返回实体列表，每行一个，不要解释。如果没有学术实体，返回空。

文本：{text}"""


class EntityExtractor:
    def __init__(self, llm):
        self._llm = llm
        self._cache: dict = {}

    def extract(self, text: str) -> List[str]:
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
