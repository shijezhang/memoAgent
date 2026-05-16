import logging
import re
import uuid
from datetime import datetime, timezone

from memo_agent.config import Config
from memo_agent.memory.working import WorkingMemory
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.reflection.detector import ReflectionDetector
from memo_agent.reflection.reflector import Reflector
from memo_agent.reflection.kg_updater import KGUpdater
from memo_agent.retrieval.entity_extractor import EntityExtractor
from memo_agent.retrieval.context_assembler import ContextAssembler

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, config: Config, llm):
        self._config = config
        self._llm = llm
        self._conversation_id = ""

        self.working = WorkingMemory()
        self.semantic = SemanticMemory(kg_file=config.kg_file)
        self.semantic.load()

        self.episodic = EpisodicMemory(
            persist_dir=config.chroma_dir,
            embedding_model_name=config.embedding_model,
        )

        self._detector = ReflectionDetector(config)
        self._reflector = Reflector(llm)
        self._kg_updater = KGUpdater()
        self._entity_extractor = EntityExtractor(llm)
        self._context_assembler = ContextAssembler(self._entity_extractor)

    def start_session(self) -> None:
        self._conversation_id = uuid.uuid4().hex[:8]
        self.working.clear()
        logger.info(f"Session started: {self._conversation_id}")

    def run_turn(self, user_input: str) -> str:
        self.working.add("user", user_input)

        if self._detector.check(user_input):
            return self._handle_reflection(user_input)

        context = self._context_assembler.assemble(
            user_input, self.working, self.episodic, self.semantic
        )

        try:
            response = self._llm.invoke(context)
            response_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            response_text = "推理暂时不可用，请稍后重试。"

        self.working.add("assistant", response_text)

        entities = self._entity_extractor.extract(user_input)
        self.episodic.store(
            self._conversation_id,
            {"role": "assistant", "content": response_text},
            metadata={
                "conversation_id": self._conversation_id,
                "timestamp": self._get_timestamp(),
                "entities": entities,
            },
        )

        return response_text

    def _handle_reflection(self, user_input: str) -> str:
        correction = self._detector.extract_correction(user_input)
        if correction is None:
            return "未能识别纠正内容。"

        error_context = self.working.get_recent(self._config.reflection_recent_turns)
        guideline = self._reflector.reflect(error_context, correction)

        if guideline is None:
            return "未能提取有效规则。"

        # Extract entities from user input using LLM-based extractor
        extracted = self._entity_extractor.extract(user_input)
        # Also find uppercase entity names (algorithm/method acronyms)
        uppercase_names = re.findall(r'[A-Z][A-Z0-9]+', user_input)
        all_entities = list(dict.fromkeys(
            guideline.source_entities + extracted + uppercase_names
        ))
        guideline.source_entities = all_entities

        self._kg_updater.apply_guideline(
            guideline, self.semantic, log_file=self._config.reflection_log
        )

        return f"已成功提取 Guideline: \"{guideline.rule[:80]}\" 并绑定至语义记忆。"

    @staticmethod
    def _get_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
