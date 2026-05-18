from fastapi import APIRouter

from memo_agent.api.schemas import MemoryStatus, StatusResponse
from memo_agent.api.deps import get_session_manager, get_semantic, get_episodic

router = APIRouter()


@router.get("/memory/status", response_model=MemoryStatus)
async def get_memory_status():
    session_manager = get_session_manager()
    semantic = get_semantic()
    episodic = get_episodic()

    entity_count = sum(1 for _, d in semantic._graph.nodes(data=True) if d.get("type") == "entity")
    rule_count = sum(1 for _, d in semantic._graph.nodes(data=True) if d.get("type") == "rule")

    try:
        conv_count = episodic._collection.count()
    except Exception:
        conv_count = 0

    return MemoryStatus(
        semantic={"entities": entity_count, "guidelines": rule_count},
        episodic={"conversations": conv_count},
        working={"turns": len(session_manager._working.get_full_context())},
    )


@router.delete("/memory/episodic", response_model=StatusResponse)
async def clear_episodic():
    episodic = get_episodic()
    episodic.clear()
    return StatusResponse(status="ok")
