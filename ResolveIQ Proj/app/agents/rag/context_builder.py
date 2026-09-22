"""
Context assembly module for ResolveIQ RAG.
Builds structured JSON response contract from reranked chunks.
"""
from typing import Any, Dict, List


def build_context(
    query: str,
    reranked_chunks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Assemble structured retrieval context from reranked chunks.
    """
    retrieved_context = []
    citations = []

    for chunk in reranked_chunks:
        collection = chunk.get("collection", "")
        if "runbook" in str(collection).lower():
            category = "runbooks"
        elif "postmortem" in str(collection).lower():
            category = "postmortems"
        else:
            category = str(collection) if collection else "unknown"

        score = chunk.get("rerank_score", chunk.get("score", 0.0))
        chunk_id = chunk.get("chunk_id", "")

        context_item = {
            "chunk_id": chunk_id,
            "source": chunk.get("source", "unknown"),
            "title": chunk.get("title", "Untitled"),
            "content": chunk.get("content", ""),
            "score": round(float(score), 4),
            "category": category,
        }

        retrieved_context.append(context_item)

        if chunk_id:
            citations.append(chunk_id)

    return {
        "query": query,
        "retrieved_context": retrieved_context,
        "citations": citations,
    }
