from typing import Dict, Any
from app.graph.state import ResolveIQState
from app.agents.resolution import run_resolution


async def resolution_node(state: ResolveIQState) -> Dict[str, Any]:
    """
    Thin LangGraph node for Resolution.
    Extracts incident, rca result, and top 3-5 retrieved chunks from state and invokes run_resolution.
    """
    incident = state["incident"]
    rca = state["rca"]
    retrieval = state.get("retrieval")
    chunks = retrieval.retrieved_chunks[:5] if retrieval and retrieval.retrieved_chunks else []

    result = await run_resolution(
        incident=incident,
        rca=rca,
        relevant_knowledge=chunks
    )
    return {"resolution": result}
