import logging
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class EpisodicMemory:
    def __init__(self, persist_dir: Path, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self._persist_dir = str(persist_dir)
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        self._collection = self._client.get_or_create_collection(
            name="episodic",
            embedding_function=self._embedding_fn,
        )

    def store(self, conversation_id: str, turn: dict, metadata: dict) -> None:
        doc_id = f"{conversation_id}_{self._collection.count()}"
        content = turn.get("content", "")
        meta = {
            "conversation_id": metadata.get("conversation_id", conversation_id),
            "timestamp": metadata.get("timestamp", ""),
            "entities": ",".join(metadata.get("entities", [])),
        }
        try:
            self._collection.add(ids=[doc_id], documents=[content], metadatas=[meta])
        except Exception as e:
            logger.error(f"EpisodicMemory store failed: {e}")

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        try:
            results = self._collection.query(query_texts=[query], n_results=top_k)
        except Exception as e:
            logger.error(f"EpisodicMemory search failed: {e}")
            return []
        if not results["documents"] or not results["documents"][0]:
            return []
        items = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0.0
            entities_str = meta.get("entities", "")
            meta["entities"] = [e for e in entities_str.split(",") if e]
            items.append({"content": doc, "metadata": meta, "distance": dist})
        return items

    def get_by_conversation(self, conversation_id: str) -> List[dict]:
        try:
            results = self._collection.get(
                where={"conversation_id": conversation_id},
            )
        except Exception as e:
            logger.error(f"EpisodicMemory get_by_conversation failed: {e}")
            return []
        if not results["documents"]:
            return []
        items = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            entities_str = meta.get("entities", "")
            meta["entities"] = [e for e in entities_str.split(",") if e]
            items.append({"content": doc, "metadata": meta})
        return items

    def clear(self) -> None:
        self._client.delete_collection("episodic")
        self._collection = self._client.get_or_create_collection(
            name="episodic",
            embedding_function=self._embedding_fn,
        )
