from typing import Dict, Any
from app.graph.state import ResolveIQState
from app.agents.rca import run_rca


async def rca_node(state: ResolveIQState) -> Dict[str, Any]:
    """
    Thin LangGraph node for Root Cause Analysis (RCA).
    Extracts incident and top 3-5 retrieved chunks from state and invokes run_rca.
    """
    incident = state["incident"]
    retrieval = state.get("retrieval")
    chunks = retrieval.retrieved_chunks[:5] if retrieval and retrieval.retrieved_chunks else []

    result = await run_rca(
        incident=incident,
        retrieved_chunks=chunks
    )
    return {"rca": result}
