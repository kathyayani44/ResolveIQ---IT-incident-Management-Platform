"""
Reranking module for ResolveIQ RAG.
Uses BAAI/bge-reranker-large or fallback heuristic scoring to rerank retrieval candidates.
"""
import os
from typing import Any, Dict, List

try:
    from sentence_transformers import CrossEncoder
except (ImportError, OSError, Exception):
    CrossEncoder = None


class ResolveIQReranker:
    """
    Cross-encoder reranker that rescores query-candidate pairs.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-large",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self.model = None

        if CrossEncoder is not None and os.environ.get("RESOLVEIQ_FAST_TEST") != "1":
            try:
                self.model = CrossEncoder(self.model_name, device=self.device)
            except Exception as e:
                print(f"Warning: Could not load CrossEncoder model '{model_name}': {e}")

    def get_model_name(self) -> str:
        return self.model_name

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if not query or not query.strip():
            return candidates[:top_k]

        if self.model is not None:
            pairs = []
            for candidate in candidates:
                content = candidate.get("content", "") or candidate.get("title", "")
                pairs.append([query.strip(), content])
            try:
                scores = self.model.predict(pairs)
                reranked = []
                for i, candidate in enumerate(candidates):
                    enriched = candidate.copy()
                    enriched["rerank_score"] = round(float(scores[i]), 4)
                    reranked.append(enriched)
                reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
                return reranked[:top_k]
            except Exception:
                pass

        # Fallback term-matching heuristic scoring if CrossEncoder is not available
        query_words = set(query.lower().split())
        reranked = []
        for candidate in candidates:
            enriched = candidate.copy()
            content_words = set(candidate.get("content", "").lower().split())
            overlap = len(query_words.intersection(content_words))
            base_score = float(candidate.get("score", 0.5))
            boost = overlap * 0.1
            enriched["rerank_score"] = round(base_score + boost, 4)
            reranked.append(enriched)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]
