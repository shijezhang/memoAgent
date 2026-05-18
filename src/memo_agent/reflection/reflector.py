import logging
from datetime import datetime, timezone
from typing import List, Optional

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
        self.last_prompt: str = ""

    def reflect(self, correction_hint: str, source_entities: List[str]) -> Optional[Guideline]:
        prompt = REFLECTION_PROMPT.format(
            error_context="",
            correction_hint=correction_hint,
        )
        self.last_prompt = prompt
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

        return Guideline(
            rule=guideline_text,
            source_entities=source_entities,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def reflect_with_context(
        self, error_context: str, correction_hint: str, source_entities: List[str]
    ) -> Optional[Guideline]:
        prompt = REFLECTION_PROMPT.format(
            error_context=error_context,
            correction_hint=correction_hint,
        )
        self.last_prompt = prompt
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

        return Guideline(
            rule=guideline_text,
            source_entities=source_entities,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _parse_guideline(self, text: str) -> Optional[str]:
        marker = "[Guideline]"
        idx = text.find(marker)
        if idx == -1:
            return None
        rule = text[idx + len(marker):].strip()
        return rule if rule else None
