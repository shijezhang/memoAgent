import logging
from typing import List, Optional

from memo_agent.core.llm_caller import LLMCaller
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.memory.working import WorkingMemory
from memo_agent.models import Guideline
from memo_agent.reflection.reflector import Reflector
from memo_agent.reflection.kg_updater import KGUpdater
from memo_agent.retrieval.entity_extractor import EntityExtractor
from memo_agent.retrieval.context_assembler import ContextAssembler

logger = logging.getLogger(__name__)


class AgentCore:
    def __init__(
        self,
        llm_caller: LLMCaller,
        entity_extractor: EntityExtractor,
        context_assembler: ContextAssembler,
        reflector: Reflector,
        kg_updater: KGUpdater,
        semantic: SemanticMemory,
        episodic: EpisodicMemory,
    ):
        self._llm_caller = llm_caller
        self._entity_extractor = entity_extractor
        self._context_assembler = context_assembler
        self._reflector = reflector
        self._kg_updater = kg_updater
        self._semantic = semantic
        self._episodic = episodic

    def infer(self, user_input: str, working_memory: WorkingMemory) -> str:
        entities = self._entity_extractor.extract(user_input)
        context = self._context_assembler.assemble(
            user_input, working_memory, self._episodic, self._semantic
        )
        return self._llm_caller.invoke(context)

    def reflect(
        self,
        user_input: str,
        correction_hint: str,
        error_context: str,
        working_memory: WorkingMemory,
    ) -> Optional[Guideline]:
        source_entities = self._entity_extractor.extract(user_input + " " + correction_hint)
        for entity in source_entities:
            if self._semantic.get_entity(entity) is None:
                self._semantic.add_entity(entity, "concept", {})

        guideline = self._reflector.reflect_with_context(
            error_context, correction_hint, source_entities
        )
        if guideline is None:
            return None

        self._kg_updater.apply_guideline(
            guideline,
            self._semantic,
            error_context=error_context,
            reflection_prompt=self._reflector.last_prompt,
        )
        return guideline

    def get_entities(self, text: str) -> List[str]:
        return self._entity_extractor.extract(text)

    def get_guidelines_for_entity(self, entity_name: str) -> List[str]:
        return self._semantic.get_guidelines_for(entity_name)
