"""
Retrieval pipeline module for ResolveIQ RAG.
Provides unified semantic search across runbooks and postmortems in Qdrant.
"""
from typing import Any, Dict, List, Optional, Union
import numpy as np

from app.agents.rag.embedder import ResolveIQEmbedder
from app.agents.rag.vectorstore import ResolveIQQdrantStore


class RetrievalResult(list):
    """Dual-interface list supporting dictionary-style access."""

    def __init__(self, items: List[Dict[str, Any]], query: str = ""):
        super().__init__(items)
        self.query = query

    def __getitem__(self, index_or_key: Union[int, slice, str]):
        if isinstance(index_or_key, str):
            if index_or_key == "results":
                return list(self)
            if index_or_key == "query":
                return self.query
            raise KeyError(index_or_key)
        return super().__getitem__(index_or_key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "results":
            return list(self)
        if key == "query":
            return self.query
        return default


class ResolveIQRetriever:
    """Coordinates semantic search over vector collections."""

    COLLECTION_RUNBOOKS = "resolveiq_runbooks"
    COLLECTION_POSTMORTEMS = "resolveiq_postmortems"

    def __init__(
        self,
        embedder: Optional[ResolveIQEmbedder] = None,
        store: Optional[ResolveIQQdrantStore] = None,
        db_path: str = "data/qdrant_db",
    ):
        self.embedder = embedder if embedder is not None else ResolveIQEmbedder()
        self.store = store if store is not None else ResolveIQQdrantStore(db_path=db_path)

    def embed_query(self, query: str) -> np.ndarray:
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")
        embeddings = self.embedder.embed_batch([query.strip()], batch_size=1, show_progress_bar=False)
        return embeddings[0]

    def _format_hit(self, hit: Dict[str, Any], collection_name: str) -> Dict[str, Any]:
        payload = hit.get("payload") or {}
        score = float(hit.get("score", 0.0))
        metadata = payload.get("metadata", {})

        source = payload.get("source") or metadata.get("source") or "unknown"
        company = metadata.get("company") or metadata.get("source") or source

        section = payload.get("section")
        if not section or str(section).strip().lower() in ("none", "n/a", ""):
            section = "None"

        return {
            "score": round(score, 4),
            "collection": collection_name,
            "chunk_id": payload.get("chunk_id"),
            "document_id": payload.get("document_id"),
            "title": payload.get("title") or "Untitled",
            "company": company,
            "source": source,
            "section": section,
            "content": payload.get("content", ""),
            "metadata": metadata,
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        collection: str = "all",
    ) -> RetrievalResult:
        if not query or not query.strip():
            return RetrievalResult([], query="")

        query_vector = self.embed_query(query)

        combined = []
        if collection in ("all", "runbooks", self.COLLECTION_RUNBOOKS):
            rb_hits = self.store.search(
                collection_name=self.COLLECTION_RUNBOOKS,
                query_vector=query_vector,
                limit=top_k,
            )
            combined.extend([self._format_hit(h, self.COLLECTION_RUNBOOKS) for h in rb_hits])

        if collection in ("all", "postmortems", self.COLLECTION_POSTMORTEMS):
            pm_hits = self.store.search(
                collection_name=self.COLLECTION_POSTMORTEMS,
                query_vector=query_vector,
                limit=top_k,
            )
            combined.extend([self._format_hit(h, self.COLLECTION_POSTMORTEMS) for h in pm_hits])

        if score_threshold is not None:
            combined = [r for r in combined if r["score"] >= score_threshold]

        combined.sort(key=lambda x: x["score"], reverse=True)
        return RetrievalResult(combined[:top_k], query=query)

    def retrieve_runbooks(
        self, query: str, top_k: int = 5, score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve specifically from the runbooks collection."""
        return self.retrieve(
            query=query, top_k=top_k, score_threshold=score_threshold, collection=self.COLLECTION_RUNBOOKS
        )

    def retrieve_postmortems(
        self, query: str, top_k: int = 5, score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve specifically from the postmortems collection."""
        return self.retrieve(
            query=query, top_k=top_k, score_threshold=score_threshold, collection=self.COLLECTION_POSTMORTEMS
        )
