import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.rag.retriever import ResolveIQRetriever
from app.agents.rag.reranker import ResolveIQReranker

def main():
    print("=" * 75)
    print("VPN RETRIEVAL & RERANKING VERIFICATION (REAL EMBEDDINGS)")
    print("=" * 75)

    retriever = ResolveIQRetriever()
    reranker = ResolveIQReranker()

    print(f"Embedder Real Model Active: {retriever.embedder.model is not None} ({retriever.embedder.get_model_name()})")
    print(f"Reranker Real Model Active: {reranker.model is not None} ({reranker.get_model_name()})")

    query = "vpn failed to start routing error port 1194"
    print(f"\nQuery: '{query}'")

    # Step 1: Retrieve candidates
    candidates = retriever.retrieve(query=query, top_k=10)
    print(f"\n[1] Retrieved {len(candidates)} candidates from Qdrant.")

    print("\n--- Top 5 BEFORE Reranking ---")
    for i, c in enumerate(candidates[:5], 1):
        category = c.get("metadata", {}).get("category") or c.get("category") or "Unknown"
        title = c.get("title", "Untitled")
        score = c.get("score")
        source = c.get("source")
        collection = c.get("collection")
        content = c.get("content", "").replace("\n", " ").strip()
        excerpt = content[:150] + ("..." if len(content) > 150 else "")
        print(f"{i}. [{collection}] {title}")
        print(f"   Category: {category} | Score: {score:.4f} | Source: {source}")
        print(f"   Excerpt : {excerpt}\n")

    # Step 2: Rerank top 10 -> top 5
    reranked = reranker.rerank(query=query, candidates=list(candidates), top_k=5)

    print("\n--- Top 5 AFTER Reranking (CrossEncoder) ---")
    for i, c in enumerate(reranked, 1):
        category = c.get("metadata", {}).get("category") or c.get("category") or "Unknown"
        title = c.get("title", "Untitled")
        initial_score = c.get("score")
        rerank_score = c.get("rerank_score")
        source = c.get("source")
        collection = c.get("collection")
        content = c.get("content", "").replace("\n", " ").strip()
        excerpt = content[:150] + ("..." if len(content) > 150 else "")
        print(f"{i}. [{collection}] {title}")
        print(f"   Category: {category} | Initial Score: {initial_score:.4f} | Rerank Score: {rerank_score} | Source: {source}")
        print(f"   Excerpt : {excerpt}\n")

if __name__ == "__main__":
    main()
