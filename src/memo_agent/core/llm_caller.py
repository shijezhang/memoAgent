import logging
import time
from typing import Generator, List

logger = logging.getLogger(__name__)


class LLMCaller:
    def __init__(
        self,
        llm,
        max_retries: int = 3,
        base_delay: float = 1.0,
        fallback_prefix: str = "[降级]",
    ):
        self._llm = llm
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._fallback_prefix = fallback_prefix
        self._last_degraded: bool = False

    def invoke(
        self,
        messages: List,
        fallback: str = "推理暂时不可用，请稍后重试。",
    ) -> str:
        self._last_degraded = False
        for attempt in range(self._max_retries):
            try:
                response = self._llm.invoke(messages)
                content = response.content if hasattr(response, "content") else str(response)
                return content
            except Exception as e:
                logger.error(f"LLM call failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                if attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    self._last_degraded = True
                    return f"{self._fallback_prefix} {fallback}"

    def stream(self, messages: List) -> Generator[str, None, None]:
        self._last_degraded = False
        try:
            for chunk in self._llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM stream failed: {e}")
            self._last_degraded = True
            yield f"{self._fallback_prefix} 推理暂时不可用，请稍后重试。"

    @property
    def last_degraded(self) -> bool:
        return self._last_degraded
