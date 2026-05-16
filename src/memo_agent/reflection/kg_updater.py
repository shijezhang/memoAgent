import logging

from memo_agent.models import Guideline
from memo_agent.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)


class KGUpdater:
    def apply_guideline(self, guideline: Guideline, semantic: SemanticMemory) -> None:
        if self._is_duplicate(guideline.rule, semantic):
            logger.warning(f"Duplicate Guideline skipped: {guideline.rule[:80]}")
            return
        for entity_name in guideline.source_entities:
            if semantic.get_entity(entity_name) is None:
                semantic.add_entity(entity_name, "concept", {})
        semantic.add_guideline(guideline.rule, related_entities=guideline.source_entities)
        logger.info(f"Guideline applied: {guideline.rule[:80]}")

    def _is_duplicate(self, new_rule: str, semantic: SemanticMemory) -> bool:
        for _, data in semantic._graph.nodes(data=True):
            if data.get("type") == "rule":
                existing = data.get("rule", "")
                if existing and (existing in new_rule or new_rule in existing):
                    return True
        return False
