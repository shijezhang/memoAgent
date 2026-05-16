import json
import logging
from pathlib import Path
from typing import Optional

from memo_agent.models import Guideline
from memo_agent.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)


class KGUpdater:
    def apply_guideline(self, guideline: Guideline, semantic: SemanticMemory,
                        log_file: Optional[Path] = None) -> None:
        if self._is_duplicate(guideline.rule, semantic):
            logger.warning(f"Duplicate Guideline skipped: {guideline.rule[:80]}")
            return
        for entity_name in guideline.source_entities:
            if semantic.get_entity(entity_name) is None:
                semantic.add_entity(entity_name, "concept", {})
        semantic.add_guideline(guideline.rule, related_entities=guideline.source_entities)
        logger.info(f"Guideline applied: {guideline.rule[:80]}")
        if log_file is not None:
            self._write_log(log_file, guideline)

    def _write_log(self, log_file: Path, guideline: Guideline) -> None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "rule": guideline.rule,
            "source_entities": guideline.source_entities,
            "timestamp": guideline.timestamp,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _is_duplicate(self, new_rule: str, semantic: SemanticMemory) -> bool:
        for _, data in semantic._graph.nodes(data=True):
            if data.get("type") == "rule":
                existing = data.get("rule", "")
                if existing and (existing in new_rule or new_rule in existing):
                    return True
        return False
