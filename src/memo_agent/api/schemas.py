from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    entities: List[str] = []
    guidelines_used: List[str] = []
    is_reflection: bool = False
    guideline: Optional[str] = None


class ReflectionLogEntry(BaseModel):
    id: str
    rule: str
    source_entities: List[str]
    error_context: str
    reflection_prompt: str
    kg_diff: dict
    timestamp: str


class KGNode(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    rule: Optional[str] = None


class KGEdge(BaseModel):
    source: str
    target: str
    relation: str


class KnowledgeGraph(BaseModel):
    nodes: List[KGNode]
    edges: List[KGEdge]


class MemoryStatus(BaseModel):
    semantic: dict
    episodic: dict
    working: dict


class EntityCreate(BaseModel):
    name: str


class EntityDelete(BaseModel):
    id: str


class StatusResponse(BaseModel):
    status: str
