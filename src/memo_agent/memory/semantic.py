import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx

logger = logging.getLogger(__name__)


class SemanticMemory:
    def __init__(self, kg_file: Path):
        self._kg_file = Path(kg_file)
        self._graph = nx.DiGraph()

    def add_entity(self, name: str, entity_type: str, properties: dict) -> str:
        existing = self.get_entity(name)
        if existing is not None:
            return existing["node_id"]
        node_id = f"entity_{name}"
        self._graph.add_node(
            node_id,
            type="entity",
            name=name,
            entity_type=entity_type,
            properties=properties,
        )
        self.save()
        return node_id

    def add_relation(self, source: str, target: str, relation: str) -> None:
        src_id = self._ensure_entity(source)
        tgt_id = self._ensure_entity(target)
        self._graph.add_edge(src_id, tgt_id, type=relation)
        self.save()

    def add_guideline(self, rule: str, related_entities: List[str]) -> str:
        entity_ids = [self._ensure_entity(e) for e in related_entities]
        rule_id = f"rule_{len(self._graph.nodes)}"
        self._graph.add_node(rule_id, type="rule", name=rule, rule=rule)
        for eid in entity_ids:
            self._graph.add_edge(eid, rule_id, type="governs")
        self.save()
        return rule_id

    def get_entity(self, name: str) -> Optional[Dict]:
        for node_id, data in self._graph.nodes(data=True):
            if data.get("name") == name and data.get("type") == "entity":
                return {"node_id": node_id, **data}
        return None

    def get_guidelines_for(self, entity_name: str) -> List[str]:
        entity = self.get_entity(entity_name)
        if entity is None:
            return []
        eid = entity["node_id"]
        guidelines = []
        for _, target, edge_data in self._graph.out_edges(eid, data=True):
            if edge_data.get("type") == "governs":
                node_data = self._graph.nodes[target]
                if node_data.get("type") == "rule":
                    guidelines.append(node_data["rule"])
        return guidelines

    def get_subgraph(self, entity_names: List[str], depth: int = 1) -> Dict:
        if not entity_names:
            return {"nodes": [], "edges": []}
        seed_ids = set()
        for name in entity_names:
            entity = self.get_entity(name)
            if entity:
                seed_ids.add(entity["node_id"])
        if not seed_ids:
            return {"nodes": [], "edges": []}
        visited_nodes = set()
        visited_edges = []
        frontier = seed_ids
        for _ in range(depth + 1):
            next_frontier = set()
            for nid in frontier:
                if nid in visited_nodes:
                    continue
                visited_nodes.add(nid)
                for src, tgt, edata in self._graph.edges(nid, data=True):
                    visited_edges.append({
                        "source": self._graph.nodes[src].get("name", src),
                        "target": self._graph.nodes[tgt].get("name", tgt),
                        "relation": edata.get("type", ""),
                    })
                    if tgt not in visited_nodes:
                        next_frontier.add(tgt)
                for src, tgt, edata in self._graph.in_edges(nid, data=True):
                    visited_edges.append({
                        "source": self._graph.nodes[src].get("name", src),
                        "target": self._graph.nodes[tgt].get("name", tgt),
                        "relation": edata.get("type", ""),
                    })
                    if src not in visited_nodes:
                        next_frontier.add(src)
            frontier = next_frontier
        nodes = [
            {
                "name": self._graph.nodes[nid].get("name", nid),
                "type": self._graph.nodes[nid].get("type", ""),
                **self._graph.nodes[nid],
            }
            for nid in visited_nodes
        ]
        return {"nodes": nodes, "edges": visited_edges}

    def save(self) -> None:
        self._kg_file.parent.mkdir(parents=True, exist_ok=True)
        bak_file = Path(str(self._kg_file) + ".bak")
        if self._kg_file.exists():
            bak_file.write_text(self._kg_file.read_text())
        data = nx.node_link_data(self._graph)
        self._kg_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load(self) -> None:
        if not self._kg_file.exists():
            self._graph = nx.DiGraph()
            return
        try:
            data = json.loads(self._kg_file.read_text())
            self._graph = nx.node_link_graph(data, directed=True)
        except (json.JSONDecodeError, KeyError):
            logger.warning("KG file corrupted, loading backup")
            bak_file = Path(str(self._kg_file) + ".bak")
            if bak_file.exists():
                data = json.loads(bak_file.read_text())
                self._graph = nx.node_link_graph(data, directed=True)
            else:
                self._graph = nx.DiGraph()

    def _ensure_entity(self, name: str) -> str:
        existing = self.get_entity(name)
        if existing:
            return existing["node_id"]
        return self.add_entity(name, "concept", {})
