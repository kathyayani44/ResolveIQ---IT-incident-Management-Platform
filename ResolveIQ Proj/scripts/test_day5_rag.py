"""
ResolveIQ Day 5 — RAG Pipeline Validation Script.
Tests the full pipeline: Retrieval → Reranking → Context Assembly.
10 realistic incident test cases.

No external LLM APIs. No Docker.
"""
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings.embedder import ResolveIQEmbedder
from src.vectorstore.qdrant_store import ResolveIQQdrantStore
from src.retrieval import ResolveIQRetriever
from src.reranking import ResolveIQReranker
from src.retrieval.context_builder import build_context


# ---------------------------------------------------------------------------
# 10 Realistic Incident Test Cases
# ---------------------------------------------------------------------------

TEST_INCIDENTS = [
    {
        "name": "1. API 503 Error",
        "title": "Payment API returning 503",
        "category": "Application",
        "service": "Payment API",
        "severity": "Critical",
        "keywords": ["503", "deployment"],
    },
    {
        "name": "2. Database Failure",
        "title": "Production database not responding to queries",
        "category": "Database",
        "service": "PostgreSQL",
        "severity": "Critical",
        "keywords": ["database", "connection", "timeout"],
    },
    {
        "name": "3. Network Failure",
        "title": "Network connectivity lost between data centers",
        "category": "Network",
        "service": "Core Network",
        "severity": "High",
        "keywords": ["network", "connectivity", "failure"],
    },
    {
        "name": "4. Wrong Category (graceful fallback)",
        "title": "Users unable to log in to the portal",
        "category": "Furniture",
        "service": "Auth Portal",
        "severity": "High",
        "keywords": ["login", "authentication"],
    },
    {
        "name": "5. Unknown Service (graceful fallback)",
        "title": "Service returning errors intermittently",
        "category": "Application",
        "service": "XyzNonexistentMicroservice",
        "severity": "Medium",
        "keywords": ["errors", "intermittent"],
    },
    {
        "name": "6. No Metadata Match (dense fallback)",
        "title": "High CPU usage on production servers",
        "category": None,
        "service": None,
        "severity": None,
        "keywords": [],
    },
    {
        "name": "7. Empty Keywords",
        "title": "Email delivery delays for all users",
        "category": "Email",
        "service": "Exchange Online",
        "severity": "Medium",
        "keywords": [],
    },
    {
        "name": "8. Connection Timeout",
        "title": "Database connection timeout during peak hours",
        "category": "Database",
        "service": "Azure SQL",
        "severity": "High",
        "keywords": ["timeout", "connection", "peak"],
    },
    {
        "name": "9. Deployment Failure",
        "title": "Deployment failed and application is down",
        "category": "Application",
        "service": "CI/CD Pipeline",
        "severity": "Critical",
        "keywords": ["deployment", "rollback", "failure"],
    },
    {
        "name": "10. Authentication Failure",
        "title": "Users cannot authenticate with SSO",
        "category": "Security",
        "service": "Azure AD",
        "severity": "Critical",
        "keywords": ["SSO", "authentication", "MFA"],
    },
]

REQUIRED_CONTEXT_FIELDS = {"chunk_id", "source", "title", "content", "score", "category"}


def build_query_from_incident(incident: dict) -> str:
    """Build a query string from incident fields (same logic as the API)."""
    parts = [incident["title"]]
    if incident.get("category"):
        parts.append(incident["category"])
    if incident.get("service"):
        parts.append(incident["service"])
    if incident.get("severity"):
        parts.append(incident["severity"])
    if incident.get("keywords"):
        parts.extend(incident["keywords"])
    return " ".join(parts).strip()


def run_tests():
    print("=" * 80)
    print("RESOLVEIQ DAY 5 — RAG PIPELINE VALIDATION")
    print("=" * 80)

    # --- Initialize components ---
    print("\n[1/4] Initializing components...")
    start = time.time()
    embedder = ResolveIQEmbedder()
    store = ResolveIQQdrantStore(db_path="data/qdrant_db")
    retriever = ResolveIQRetriever(embedder=embedder, store=store)
    reranker = ResolveIQReranker()
    init_time = time.time() - start
    print(f"Components initialized in {init_time:.1f}s")

    rb_stats = store.get_collection_stats(retriever.COLLECTION_RUNBOOKS)
    pm_stats = store.get_collection_stats(retriever.COLLECTION_POSTMORTEMS)
    print(f"Runbooks: {rb_stats.get('points_count', 0):,} vectors")
    print(f"Postmortems: {pm_stats.get('points_count', 0):,} vectors")

    # --- Run all 10 test cases ---
    print(f"\n[2/4] Running {len(TEST_INCIDENTS)} test cases...")

    results_summary = []
    all_passed = True

    for incident in TEST_INCIDENTS:
        name = incident["name"]
        print(f"\n{'─' * 80}")
        print(f"TEST: {name}")
        print(f"{'─' * 80}")

        query = build_query_from_incident(incident)
        print(f"  Query: \"{query}\"")

        errors = []

        try:
            # Step 1: Retrieve Top 10
            candidates = retriever.retrieve(query=query, top_k=10)
            candidate_list = list(candidates)
            num_candidates = len(candidate_list)
            print(f"  Retrieved: {num_candidates} candidates")

            if num_candidates == 0:
                errors.append("No candidates retrieved")

            # Step 2: Rerank → Top 5
            reranked = reranker.rerank(
                query=query,
                candidates=candidate_list,
                top_k=5,
            )
            num_reranked = len(reranked)
            print(f"  Reranked:  {num_reranked} results")

            if num_reranked > 5:
                errors.append(f"Expected <= 5 reranked, got {num_reranked}")

            # Step 3: Build context
            response = build_context(query=query, reranked_chunks=reranked)

            # Validate response structure
            if "query" not in response:
                errors.append("Missing 'query' in response")
            if "retrieved_context" not in response:
                errors.append("Missing 'retrieved_context' in response")
            if "citations" not in response:
                errors.append("Missing 'citations' in response")

            ctx_items = response.get("retrieved_context", [])
            citations = response.get("citations", [])

            if len(ctx_items) > 5:
                errors.append(f"Expected <= 5 context items, got {len(ctx_items)}")

            # Validate each context item has required fields
            for i, item in enumerate(ctx_items):
                missing = REQUIRED_CONTEXT_FIELDS - set(item.keys())
                if missing:
                    errors.append(f"Item {i} missing fields: {missing}")

            # Validate citations match chunk_ids
            context_chunk_ids = [item["chunk_id"] for item in ctx_items if item.get("chunk_id")]
            if set(citations) != set(context_chunk_ids):
                errors.append("Citations do not match context chunk_ids")

            # Validate rerank scores are present
            for chunk in reranked:
                if "rerank_score" not in chunk:
                    errors.append("Missing rerank_score in reranked chunk")
                    break

            # Display top results
            for rank, item in enumerate(ctx_items[:3], 1):
                preview = item["content"].replace("\n", " ")[:90]
                print(f"    {rank}. Score: {item['score']:.4f} | [{item['category']}] {item['title']}")
                print(f"       Preview: \"{preview}...\"")

        except Exception as e:
            errors.append(f"Exception: {e}")
            import traceback
            traceback.print_exc()

        passed = len(errors) == 0
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
            for err in errors:
                print(f"    [ERROR] {err}")

        results_summary.append({"name": name, "status": status, "errors": errors})
        print(f"  Result: {status}")

    # --- Validation Report ---
    print(f"\n{'=' * 80}")
    print("DAY 5 RAG PIPELINE VALIDATION REPORT")
    print(f"{'=' * 80}")
    print()
    print(f"Embedding Model:   {embedder.get_model_name()}")
    print(f"Reranker Model:    {reranker.get_model_name()}")
    print(f"Vector Dimension:  {embedder.get_dimension()}")
    print(f"Database Path:     {store.db_path}")
    print()

    print("Test Results:")
    for r in results_summary:
        print(f"  {r['name']}: {r['status']}")
        if r["errors"]:
            for err in r["errors"]:
                print(f"    → {err}")

    passed_count = sum(1 for r in results_summary if r["status"] == "PASS")
    total_count = len(results_summary)

    print()
    print(f"Tests Passed: {passed_count}/{total_count}")
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    run_tests()
