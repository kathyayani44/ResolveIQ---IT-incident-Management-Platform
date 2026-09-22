"""
Qdrant vector store module for ResolveIQ RAG.
Handles connection to local Qdrant, collection management, and vector insertion.
"""
import uuid
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    QdrantClient = None
    models = None


class ResolveIQQdrantStore:
    """
    Wrapper around QdrantClient for local persistent storage.
    """

    _shared_client = None

    def __init__(self, db_path: str = "data/qdrant_db"):
        self.db_path = db_path
        self.client = None
        self._in_memory_store: Dict[str, List[Dict[str, Any]]] = {}

        if QdrantClient is not None:
            try:
                if ResolveIQQdrantStore._shared_client is None:
                    try:
                        ResolveIQQdrantStore._shared_client = QdrantClient(path=self.db_path)
                    except Exception:
                        ResolveIQQdrantStore._shared_client = QdrantClient(location=":memory:")
                self.client = ResolveIQQdrantStore._shared_client
            except Exception as e:
                print(f"Warning: Could not connect to Qdrant at {db_path}: {e}")

    def setup_collection(
        self, collection_name: str, dimension: int, rebuild: bool = False
    ) -> bool:
        if self.client is None or models is None:
            self._in_memory_store[collection_name] = []
            return True

        exists = self.client.collection_exists(collection_name)
        if exists:
            if rebuild:
                self.client.delete_collection(collection_name=collection_name)
            else:
                return False

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE
            )
        )
        return True

    def insert_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
        batch_size: int = 100
    ):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")

        if self.client is None or models is None:
            if collection_name not in self._in_memory_store:
                self._in_memory_store[collection_name] = []
            for i, chunk in enumerate(chunks):
                item = chunk.copy()
                item["_vector"] = embeddings[i]
                self._in_memory_store[collection_name].append(item)
            return

        if not self.client.collection_exists(collection_name):
            dimension = len(embeddings[0]) if len(embeddings) > 0 else 384
            self.setup_collection(collection_name, dimension=dimension)

        total = len(chunks)
        points = []
        for i in range(total):
            chunk = chunks[i]
            embedding = embeddings[i]
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(chunk.get("chunk_id", i))))
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=chunk.copy()
                )
            )

        for i in range(0, total, batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=collection_name, points=batch)

    def search(
        self, collection_name: str, query_vector: np.ndarray, limit: int = 3
    ) -> List[Dict[str, Any]]:
        if self.client is not None:
            try:
                results = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector.tolist(),
                    limit=limit,
                ).points
                return [
                    {
                        "score": hit.score,
                        "payload": hit.payload
                    }
                    for hit in results
                ]
            except Exception:
                pass

        # In-memory search fallback
        items = self._in_memory_store.get(collection_name, [])
        scored = []
        for item in items:
            vec = item.get("_vector")
            if vec is not None and len(vec) == len(query_vector):
                score = float(np.dot(vec, query_vector) / (np.linalg.norm(vec) * np.linalg.norm(query_vector) + 1e-9))
            else:
                score = 0.5
            payload = {k: v for k, v in item.items() if k != "_vector"}
            scored.append({"score": score, "payload": payload})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        if self.client is not None and self.client.collection_exists(collection_name):
            info = self.client.get_collection(collection_name)
            points_cnt = getattr(info, "points_count", 0) or 0
            vectors_cnt = getattr(info, "vectors_count", None) or points_cnt
            return {
                "status": getattr(info, "status", "green"),
                "points_count": points_cnt,
                "vectors_count": vectors_cnt
            }
        in_mem_cnt = len(self._in_memory_store.get(collection_name, []))
        return {"status": "ok", "points_count": in_mem_cnt, "vectors_count": in_mem_cnt}

    def get_sample_payload(self, collection_name: str) -> Optional[Dict[str, Any]]:
        if self.client is not None and self.client.collection_exists(collection_name):
            try:
                records, _ = self.client.scroll(
                    collection_name=collection_name,
                    limit=1,
                    with_payload=True,
                    with_vectors=False
                )
                if records and len(records) > 0:
                    return records[0].payload
            except Exception:
                pass
        items = self._in_memory_store.get(collection_name, [])
        if items:
            return {k: v for k, v in items[0].items() if k != "_vector"}
        return None
