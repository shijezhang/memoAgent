import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from memo_agent.models import Guideline
from memo_agent.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)


class KGUpdater:
    def apply_guideline(
        self,
        guideline: Guideline,
        semantic: SemanticMemory,
        log_file: Optional[Path] = None,
        error_context: str = "",
        reflection_prompt: str = "",
    ) -> Dict:
        if self._is_duplicate(guideline.rule, semantic):
            logger.warning(f"Duplicate Guideline skipped: {guideline.rule[:80]}")
            return {"skipped": True, "reason": "duplicate"}

        kg_diff = {"added_nodes": [], "added_edges": []}

        for entity_name in guideline.source_entities:
            if semantic.get_entity(entity_name) is None:
                node_id = semantic.add_entity(entity_name, "concept", {})
                kg_diff["added_nodes"].append({"id": node_id, "name": entity_name, "type": "entity"})

        rule_id = semantic.add_guideline(guideline.rule, related_entities=guideline.source_entities)
        kg_diff["added_nodes"].append({"id": rule_id, "name": guideline.rule[:50], "type": "rule"})

        for entity_name in guideline.source_entities:
            entity = semantic.get_entity(entity_name)
            if entity:
                kg_diff["added_edges"].append({
                    "source": entity["node_id"],
                    "target": rule_id,
                    "relation": "governs",
                })

        logger.info(f"Guideline applied: {guideline.rule[:80]}")
        if log_file is not None:
            self._write_log(log_file, guideline, error_context, reflection_prompt, kg_diff)

        return {"skipped": False, "kg_diff": kg_diff}

    def _write_log(
        self,
        log_file: Path,
        guideline: Guideline,
        error_context: str,
        reflection_prompt: str,
        kg_diff: Dict,
    ) -> None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "rule": guideline.rule,
            "source_entities": guideline.source_entities,
            "timestamp": guideline.timestamp,
            "error_context": error_context,
            "reflection_prompt": reflection_prompt,
            "kg_diff": kg_diff,
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
