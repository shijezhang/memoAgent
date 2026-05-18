import json
from typing import List, Optional

from fastapi import APIRouter

from memo_agent.api.schemas import ReflectionLogEntry, KGNode
from memo_agent.api.deps import get_config, get_semantic

router = APIRouter()


@router.get("/reflections", response_model=List[ReflectionLogEntry])
async def get_reflections(limit: int = 50, entity: Optional[str] = None):
    config = get_config()
    log_file = config.reflection_log

    if not log_file.exists():
        return []

    entries = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entity and entity not in entry.get("source_entities", []):
                    continue
                entries.append(ReflectionLogEntry(
                    id=entry.get("timestamp", ""),
                    rule=entry.get("rule", ""),
                    source_entities=entry.get("source_entities", []),
                    error_context=entry.get("error_context", ""),
                    reflection_prompt=entry.get("reflection_prompt", ""),
                    kg_diff=entry.get("kg_diff", {}),
                    timestamp=entry.get("timestamp", ""),
                ))
            except json.JSONDecodeError:
                continue

    return entries[-limit:]


@router.get("/guidelines", response_model=List[KGNode])
async def get_guidelines():
    semantic = get_semantic()
    guidelines = []

    for node_id, data in semantic._graph.nodes(data=True):
        if data.get("type") == "rule":
            guidelines.append(KGNode(
                id=node_id,
                type="rule",
                rule=data.get("rule", ""),
                name=data.get("name", data.get("rule", "")[:50]),
            ))

    return guidelines
