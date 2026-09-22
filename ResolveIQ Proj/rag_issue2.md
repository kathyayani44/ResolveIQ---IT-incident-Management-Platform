We need to diagnose an RAG integration problem in ResolveIQ.

IMPORTANT CONTEXT:

A teammate originally implemented the RAG/vector-store pipeline in a separate repository structure. That implementation was later integrated into the current ResolveIQ repository.

The current repository has this structure:

app/
├── agents/
│   ├── classification/
│   ├── kb/
│   ├── rag/
│   │   ├── agent.py
│   │   ├── chunker.py
│   │   ├── context_builder.py
│   │   ├── embedder.py
│   │   ├── loader.py
│   │   ├── normalizer.py
│   │   ├── reranker.py
│   │   ├── retriever.py
│   │   └── vectorstore.py
│   ├── rca/
│   ├── resolution/
│   └── revision/
├── graph/
├── integrations/
├── schemas/
├── services/
│   ├── pipeline.py
│   ├── jira_ingestion.py
│   └── ...
├── api/
└── main.py

data/
└── qdrant_db/
    ├── lock
    └── meta.json

The teammate's ORIGINAL RAG implementation had approximately this architecture:

src/vectorstore/qdrant_store.py
    ResolveIQQdrantStore
    → QdrantClient(path="data/qdrant_db")
    → setup_collection()
    → insert_chunks()
    → search()
    → get_collection_stats()
    → get_sample_payload()

src/retrieval/retriever.py
    ResolveIQRetriever
    → query embedding
    → Qdrant semantic search
    → retrieved chunks

scripts/build_vector_store.py
    → data/chunks/
    → embeddings
    → Qdrant

scripts/test_retrieval.py
    → direct retrieval testing

scripts/test_day5_rag.py
    → /rag/retrieve

The current integrated implementation appears to have equivalent functionality under:

app/agents/rag/

and ResolveIQ now uses the RAG pipeline through its LangGraph/service architecture.

CURRENT SYMPTOM:

For incident RESIQ-2:

"vpn failed to start"
Category: Network
Service: VPN

The UI shows:

RAG Retrieval → COMPLETED
but:
"No retrieved knowledge chunks associated with this incident."

RCA → INSUFFICIENT_EVIDENCE
Resolution → INSUFFICIENT_EVIDENCE
Human Approval → BLOCKED

Previous investigation showed that the LangGraph state is correctly passing the empty retrieval result.

However, because the teammate's original RAG implementation was later integrated into the current structure, we now need to determine whether the integration itself caused the problem.

DO NOT MODIFY CODE YET.

DO NOT create new runbooks.
DO NOT create a new ingestion pipeline.
DO NOT re-index the database.
DO NOT replace the existing RAG implementation.

First perform a READ-ONLY integration audit.

==================================================
PART 1 — MAP THE ORIGINAL RAG FLOW
==================================================

Inspect the current files under:

app/agents/rag/

Determine the exact responsibilities of:

agent.py
loader.py
normalizer.py
chunker.py
embedder.py
vectorstore.py
retriever.py
reranker.py
context_builder.py

Then reconstruct the intended flow:

Knowledge documents
→ loader
→ normalizer
→ chunker
→ embedder
→ vectorstore
→ retriever
→ reranker
→ context builder
→ RAG result

Identify whether every step is actually connected.

Do not assume that because a file exists, it is actually used.

==================================================
PART 2 — TRACE THE INGESTION/STORAGE FLOW
==================================================

Find the current equivalent of the teammate's:

scripts/build_vector_store.py

Determine:

1. What input directory does the current ingestion process use?
2. Does it actually find documents/chunks?
3. Does it generate embeddings?
4. What embedding model is used?
5. What embedding dimension is produced?
6. What Qdrant client is used?
7. What Qdrant path is used?
8. What collection names are created?
9. Does insert_chunks() actually execute?
10. How many points exist after the teammate's existing ingestion?

IMPORTANT:

Do not run a rebuild or re-index operation.

Only inspect the existing database and existing ingestion code/state.

==================================================
PART 3 — TRACE THE QDRANT CONNECTION
==================================================

Inspect:

app/agents/rag/vectorstore.py

Determine the exact Qdrant initialization.

Compare it with the original implementation:

QdrantClient(path="data/qdrant_db")

Check for:

- local vs server Qdrant
- relative vs absolute path
- working-directory dependency
- environment variables
- fallback behavior
- in-memory store
- collection creation
- collection recreation
- collection naming
- embedding dimension
- distance metric

CRITICAL:

Determine the ACTUAL absolute filesystem path being used at runtime.

A relative path such as:

data/qdrant_db

can point to a different location depending on the process working directory.

Do not assume that the visible:

data/qdrant_db/

is necessarily the database the running application is reading.

==================================================
PART 4 — VERIFY THE EXISTING QDRANT DATABASE
==================================================

Without modifying it, inspect:

data/qdrant_db/

Determine:

- Does Qdrant recognize the database?
- What collections exist?
- Point count for resolveiq_runbooks
- Point count for resolveiq_postmortems
- Sample payload if points exist

If there are zero collections/points, determine whether:

A. the database was never populated

OR

B. the teammate populated a DIFFERENT Qdrant path/database

OR

C. the integration changed the Qdrant configuration

OR

D. the application is falling back to another store.

Do not conclude that the global Qdrant database is empty without checking the ingestion configuration.

==================================================
PART 5 — TRACE RETRIEVAL
==================================================

Inspect:

app/agents/rag/retriever.py

Trace exactly:

RESIQ-2
→ search query construction
→ query embedding
→ vectorstore initialization
→ collection selection
→ search()
→ result filtering
→ reranking
→ RetrievedChunk
→ RAG result

Use this query:

"vpn failed to start Network VPN Medium"

Determine at every boundary:

Input
Output
Number of chunks

Specifically check whether chunks are lost:

1. Before Qdrant
2. During Qdrant search
3. After Qdrant search
4. During reranking
5. During context building
6. When converting to RetrievalResult

==================================================
PART 6 — TRACE THE API FLOW
==================================================

Find the current equivalent of the old:

POST /rag/retrieve

Trace:

API
→ RAG agent
→ retriever
→ vectorstore
→ Qdrant
→ reranker/context builder
→ API response

Determine whether the API uses the same RAG components as LangGraph.

If an older standalone RAG API still exists, compare it with the LangGraph-integrated RAG implementation.

We specifically want to know if there are now TWO RAG paths:

Path A:
API → RAG

Path B:
LangGraph → RAG

If so, determine whether they use different configuration, stores, retrievers, or initialization.

==================================================
PART 7 — TRACE THE LANGGRAPH INTEGRATION
==================================================

Inspect:

app/graph/
app/services/pipeline.py
app/agents/rag/agent.py

Trace:

Classification
→ RAG node
→ RAG agent
→ Retriever
→ Qdrant
→ RetrievalResult
→ LangGraph state
→ RCA

Confirm:

- Which function LangGraph actually calls.
- Whether it uses app/agents/rag/agent.py.
- Whether it creates a new retriever/store instance.
- Whether it uses the same Qdrant configuration as the original RAG scripts.
- Whether retrieval results are transformed before entering LangGraph state.

Do NOT assume the LangGraph RAG node is equivalent to the old standalone RAG API.

==================================================
PART 8 — CHECK DEPENDENCY / FALLBACK PROBLEMS
==================================================

Determine why the previous diagnostic reported:

qdrant_client → ModuleNotFoundError

Check:

requirements.txt
pyproject.toml
Pipfile
environment configuration
virtual environment/package installation

Determine:

- Is qdrant_client declared as a dependency?
- Is it installed in the environment running ResolveIQ?
- Does vectorstore.py silently fall back to an in-memory store?
- Does that fallback start empty?
- Could this explain the current zero-chunk retrieval?

Do not install or modify dependencies yet. Report the issue first.

==================================================
PART 9 — CHECK EMBEDDING COMPATIBILITY
==================================================

Compare the embedding pipeline used when vectors were stored with the embedding pipeline used for retrieval.

Compare:

Ingestion:
- embedding model
- embedding dimension
- normalization
- distance metric

Retrieval:
- embedding model
- embedding dimension
- normalization
- distance metric

Determine whether they are compatible.

Do not change the embedding model yet.

==================================================
PART 10 — CHECK COLLECTION NAME COMPATIBILITY
==================================================

Verify that the ingestion side and retrieval side use exactly the same collections.

Expected collections:

resolveiq_runbooks
resolveiq_postmortems

Check for differences such as:

resolveiq_runbook
runbooks
resolveiq_chunks
postmortems
etc.

Also check whether collection setup/recreation is accidentally deleting/recreating an existing collection with zero points during application startup.

This is important.

==================================================
PART 11 — RUN READ-ONLY DIAGNOSTICS
==================================================

Run the existing diagnostic/test functionality if it does not modify the database.

Prefer:

scripts/test_retrieval.py

or the current equivalent.

Then test:

1. Direct ResolveIQQdrantStore search
2. ResolveIQRetriever.retrieve()
3. RAG agent
4. /rag/retrieve if available
5. LangGraph RAG node
6. Full RESIQ-2 workflow

Record chunk counts at each boundary.

Produce a table:

Component                         Chunks
------------------------------------------------
Qdrant collection                  ?
Direct vectorstore.search()        ?
ResolveIQRetriever.retrieve()      ?
Reranker                           ?
Context builder                    ?
RAG agent result                   ?
LangGraph RAG node                 ?
RCA input                          ?
Frontend evidence                  ?

==================================================
PART 12 — DETERMINE THE ACTUAL ROOT CAUSE
==================================================

The final diagnosis must identify the exact failure.

Possible causes include:

A. Qdrant database actually contains zero vectors.

B. Teammate's ingestion populated a different Qdrant path.

C. Relative path "data/qdrant_db" resolves to a different location when ResolveIQ runs.

D. qdrant_client is missing and ResolveIQ falls back to an empty in-memory store.

E. The integration changed the Qdrant initialization/configuration.

F. Collection names changed between ingestion and retrieval.

G. Collection setup/recreation is clearing previously stored vectors.

H. Embedding model/dimension mismatch.

I. Retrieval receives Qdrant results but filtering/reranking removes them.

J. Standalone RAG API works but LangGraph uses a different RAG instance/configuration.

K. LangGraph integration loses the chunks.

L. Persistence/serialization loses the chunks.

M. Another specific integration problem.

Do NOT choose one based on assumption.

Prove the diagnosis with actual runtime values and code references.

==================================================
PART 13 — IMPORTANT SUCCESS CRITERIA
==================================================

We want to establish exactly which of these two situations is occurring:

CASE 1:

Qdrant
→ 0 chunks

Then the problem is on the ingestion/storage/configuration side.

CASE 2:

Qdrant
→ chunks exist
→ direct search returns chunks
→ ResolveIQRetriever returns chunks
→ LangGraph receives []

Then the problem is in the integration/data-flow side.

Also investigate the cases between these two boundaries.

==================================================
PART 14 — DO NOT FIX YET
==================================================

After completing the investigation, STOP.

Do NOT modify code.

Do NOT re-index.

Do NOT rebuild Qdrant.

Do NOT change similarity thresholds.

Do NOT add LLM fallback.

Do NOT create new knowledge files.

Do NOT change grounding behavior.

Give me:

1. Exact root cause
2. Evidence proving the root cause
3. Exact file/function where the problem occurs
4. Original teammate flow
5. Current integrated flow
6. Differences between the two flows
7. Qdrant path actually used by ingestion
8. Qdrant path actually used by ResolveIQ
9. Collection names and point counts
10. Embedding model/dimension on both sides
11. Chunk count at every retrieval boundary
12. Minimum fix required

Only after I review the diagnosis will we implement the fix.

SAFETY:
Preserve all existing project work. Make no destructive changes during this investigation. Do not delete, overwrite, reset, clean, move, or replace existing files/folders unless I explicitly authorize the exact target.