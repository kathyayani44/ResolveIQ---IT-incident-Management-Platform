from typing import Dict, Any
from app.graph.state import ResolveIQState
from app.agents.rag import run_rag_retrieval


async def retrieval_node(state: ResolveIQState) -> Dict[str, Any]:
    """
    Thin LangGraph node for RAG Retrieval.
    Extracts incident and optional classification from state and invokes run_rag_retrieval.
    """
    incident = state["incident"]
    classification = state.get("classification")

    result = await run_rag_retrieval(
        incident=incident,
        classification=classification,
        top_k=5
    )
    return {"retrieval": result}
