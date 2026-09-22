from typing import Dict, Any
from app.graph.state import ResolveIQState
from app.agents.classification import run_classification


async def classification_node(state: ResolveIQState) -> Dict[str, Any]:
    """
    Thin LangGraph node for Classification.
    Extracts incident from state and invokes run_classification.
    """
    incident = state["incident"]
    result = await run_classification(incident)
    return {"classification": result}
