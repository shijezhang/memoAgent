import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from memo_agent.config import Config
from memo_agent.core.agent import AgentCore
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.memory.working import WorkingMemory
from memo_agent.models import Guideline
from memo_agent.reflection.detector import ReflectionDetector

logger = logging.getLogger(__name__)


@dataclass
class TurnResult:
    response: str
    is_reflection: bool
    guideline: Optional[Guideline] = None
    entities: List[str] = field(default_factory=list)
    guidelines_used: List[str] = field(default_factory=list)


class SessionManager:
    def __init__(
        self,
        config: Config,
        agent_core: AgentCore,
        working: WorkingMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        detector: ReflectionDetector,
    ):
        self._config = config
        self._agent_core = agent_core
        self._working = working
        self._episodic = episodic
        self._semantic = semantic
        self._detector = detector
        self._conversation_id: str = ""

    def start_session(self) -> str:
        self._conversation_id = uuid.uuid4().hex[:8]
        self._working.clear()
        logger.info(f"Session started: {self._conversation_id}")
        return self._conversation_id

    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    def process_turn(self, user_input: str) -> TurnResult:
        is_reflection, hint = self._detector.check_and_extract(user_input)
        if is_reflection:
            return self._handle_reflection(user_input, hint)
        else:
            return self._handle_inference(user_input)

    def _handle_inference(self, user_input: str) -> TurnResult:
        self._working.add("user", user_input)
        entities = self._agent_core.get_entities(user_input)

        guidelines_used = []
        for entity in entities:
            guidelines_used.extend(self._agent_core.get_guidelines_for_entity(entity))
        guidelines_used = list(dict.fromkeys(guidelines_used))

        response = self._agent_core.infer(user_input, self._working)
        self._working.add("assistant", response)

        self._episodic.store(
            self._conversation_id,
            {"role": "user", "content": user_input},
            metadata={
                "conversation_id": self._conversation_id,
                "timestamp": self._get_timestamp(),
                "entities": entities,
            },
        )
        self._episodic.store(
            self._conversation_id,
            {"role": "assistant", "content": response},
            metadata={
                "conversation_id": self._conversation_id,
                "timestamp": self._get_timestamp(),
                "entities": entities,
            },
        )

        return TurnResult(
            response=response,
            is_reflection=False,
            entities=entities,
            guidelines_used=guidelines_used,
        )

    def _handle_reflection(self, user_input: str, hint: str) -> TurnResult:
        recent = self._working.get_recent(2)
        error_context = ""
        for msg in recent:
            if msg["role"] == "assistant":
                error_context = msg["content"]
                break

        self._working.add("user", user_input)
        entities = self._agent_core.get_entities(user_input + " " + hint)

        guideline = self._agent_core.reflect(user_input, hint, error_context, self._working)
        if guideline is None:
            response = "未能提取有效规则。"
        else:
            response = f"已沉淀 Guideline: {guideline.rule}"

        self._working.add("assistant", response)

        if guideline:
            self._episodic.store(
                self._conversation_id,
                {"role": "user", "content": user_input},
                metadata={
                    "conversation_id": self._conversation_id,
                    "timestamp": self._get_timestamp(),
                    "type": "reflection",
                },
            )
            self._episodic.store(
                self._conversation_id,
                {"role": "assistant", "content": response},
                metadata={
                    "conversation_id": self._conversation_id,
                    "timestamp": self._get_timestamp(),
                    "type": "guideline",
                    "rule": guideline.rule,
                },
            )

        return TurnResult(
            response=response,
            is_reflection=True,
            guideline=guideline,
            entities=entities,
        )

    @staticmethod
    def _get_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
