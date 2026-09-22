Investigate the current ResolveIQ RAG pipeline and determine the ACTUAL root cause of why evidence chunks are not reaching the RCA/Resolution stages.

IMPORTANT: Do NOT immediately modify the implementation. First inspect and trace the existing code and identify exactly where the failure occurs.

Current observed behavior for incident RESIQ-2:
- Classification completes successfully.
- RAG Retrieval stage is shown as COMPLETED.
- UI shows: "No retrieved knowledge chunks associated with this incident."
- RCA returns: INSUFFICIENT_EVIDENCE.
- Resolution is correctly blocked as INSUFFICIENT_EVIDENCE.
- Human Approval is correctly BLOCKED.
- Therefore, the grounding protection appears to be working, but we need to determine WHY RAG produced no usable evidence.

Investigate these possibilities separately:

1. RAG RETRIEVAL FAILURE
   - Is the RAG/vector search actually returning 0 chunks?
   - Is the knowledge base/vector database populated?
   - Is the embedding/search query being generated correctly?
   - Is the similarity threshold too restrictive?
   - Is the incident query being passed correctly to the retriever?
   - Is the correct collection/table/index being queried?
   - Are runbooks/postmortems actually indexed?
   - Does a direct/manual RAG query for the RESIQ-2 incident return anything?

2. LANGGRAPH / STATE-PASSING FAILURE
   - Does the RAG node successfully produce retrieved chunks internally?
   - If RAG produces chunks, are they correctly written into the LangGraph state?
   - Does the next RCA node receive the same chunks?
   - Is the state field name/type consistent between RAG → RCA?
   - Is some node accidentally resetting, overwriting, filtering, or dropping `relevant_chunks`?
   - Are chunks lost during serialization/deserialization or state merging?
   - Is the frontend displaying an empty field even though the backend actually has retrieved evidence?

3. RCA INPUT FAILURE
   - Log/inspect the exact RAG output immediately before returning from the RAG node.
   - Log/inspect the exact LangGraph state entering RCA.
   - Compare both values.
   - Determine whether RCA receives:
       a) genuinely empty RAG results, or
       b) valid RAG results that were lost somewhere in the graph.

4. RESOLUTION INPUT FAILURE
   - Confirm that Resolution receives the same evidence/RCA information that RCA produced.
   - Do NOT re-enable ungrounded LLM generation.
   - The existing grounding protection must remain intact.

5. TRACE THE COMPLETE DATA FLOW

   Jira Incident
       ↓
   Classification
       ↓
   RAG Query Construction
       ↓
   Vector/Knowledge Search
       ↓
   Retrieved Chunks
       ↓
   LangGraph State
       ↓
   RCA
       ↓
   RCA Evidence
       ↓
   Resolution

For each boundary, report:
- Input received
- Output produced
- Number of retrieved chunks
- Relevant state field names
- Whether the data is preserved or lost

6. TEST THE RAG COMPONENT IN ISOLATION

Create/run a focused diagnostic test for the RAG retriever using RESIQ-2 or an equivalent incident.

The test must establish:
- What query is sent to the retriever
- Which knowledge source/index is queried
- Number of chunks returned
- Chunk IDs
- Similarity scores
- Source/document metadata
- Whether the returned chunks contain relevant content

Then run the same case through the complete LangGraph pipeline and compare the values.

7. DO NOT ASSUME THE PROBLEM IS RAG OR LANGGRAPH

Give a clear diagnosis based on evidence:

A. "RAG itself is returning zero chunks"
OR
B. "RAG returns chunks, but LangGraph/state passing loses them"
OR
C. "RAG and LangGraph both work, but the UI/persistence layer loses/displays the evidence incorrectly"
OR
D. "The knowledge base/indexing/vector-store configuration is the actual problem"
OR
E. another specific root cause discovered from the code.

Show the exact file/function/node where the problem occurs and explain the data flow that proves the diagnosis.

Only AFTER identifying the root cause, propose the smallest safe fix.

Do not make unrelated architectural changes.

Preserve the existing:
- Jira integration
- LangGraph workflow
- RAG architecture
- grounding protection
- human approval gate
- Jira writeback/verification flow

Do not introduce an LLM fallback that allows unsupported resolutions when RAG evidence is unavailable.

Also add/adjust tests that specifically prevent this regression:
- RAG returns chunks → chunks reach RCA
- RAG returns zero chunks → RCA receives zero chunks and Resolution remains blocked
- RAG returns chunks but LangGraph loses them → test must detect the failure
- valid evidence remains available to Resolution
- no evidence → no automated resolution/approval

IMPORTANT SAFETY:
Before changing anything, inspect the existing implementation and preserve the current working project. Make changes incrementally and only to the files/functions required for this diagnosis and fix. Do not delete, overwrite, reset, clean, move, or replace existing project files/folders unless I explicitly authorize the exact target. Do not perform destructive cleanup operations.

At the end, report:
1. Actual root cause
2. Evidence proving it
3. Exact file/function involved
4. Minimal fix made (if any)
5. Tests run and results
6. Whether RESIQ-2 now retrieves and passes evidence correctly