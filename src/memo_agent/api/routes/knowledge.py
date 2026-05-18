from typing import Optional

from fastapi import APIRouter, HTTPException

from memo_agent.api.schemas import (
    KnowledgeGraph,
    KGNode,
    KGEdge,
    EntityCreate,
    StatusResponse,
)
from memo_agent.api.deps import get_semantic

router = APIRouter()


@router.get("/knowledge/graph", response_model=KnowledgeGraph)
async def get_knowledge_graph():
    semantic = get_semantic()
    nodes = []
    edges = []

    for node_id, data in semantic._graph.nodes(data=True):
        nodes.append(KGNode(
            id=node_id,
            type=data.get("type", ""),
            name=data.get("name"),
            rule=data.get("rule"),
        ))

    for src, tgt, edge_data in semantic._graph.edges(data=True):
        edges.append(KGEdge(
            source=src,
            target=tgt,
            relation=edge_data.get("type", ""),
        ))

    return KnowledgeGraph(nodes=nodes, edges=edges)


@router.get("/knowledge/subgraph", response_model=KnowledgeGraph)
async def get_subgraph(entity: str):
    semantic = get_semantic()
    subgraph = semantic.get_subgraph([entity], depth=1)

    nodes = [
        KGNode(
            id=n.get("node_id", n.get("name", "")),
            type=n.get("type", ""),
            name=n.get("name"),
            rule=n.get("rule"),
        )
        for n in subgraph["nodes"]
    ]

    edges = [
        KGEdge(source=e["source"], target=e["target"], relation=e["relation"])
        for e in subgraph["edges"]
    ]

    return KnowledgeGraph(nodes=nodes, edges=edges)


@router.post("/knowledge/entity", response_model=KGNode)
async def create_entity(request: EntityCreate):
    semantic = get_semantic()
    node_id = semantic.add_entity(request.name, "concept", {})
    return KGNode(id=node_id, type="entity", name=request.name)


@router.delete("/knowledge/entity/{entity_id}", response_model=StatusResponse)
async def delete_entity(entity_id: str):
    semantic = get_semantic()
    if entity_id not in semantic._graph.nodes:
        raise HTTPException(status_code=404, detail="Entity not found")
    semantic._graph.remove_node(entity_id)
    semantic.save()
    return StatusResponse(status="ok")
