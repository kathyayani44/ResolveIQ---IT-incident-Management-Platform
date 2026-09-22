"""
ResolveIQ LangGraph Workflow Builder.
Orchestrates: START -> classification -> retrieval -> rca -> resolution -> END
"""
from typing import Dict, Any, Optional
from app.schemas.incident import CanonicalIncident
from app.graph.state import ResolveIQState
from app.graph.nodes import (
    classification_node,
    retrieval_node,
    rca_node,
    resolution_node
)

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = "START"
    END = "END"


def build_resolveiq_graph():
    """Builds and compiles the ResolveIQ LangGraph orchestration workflow graph."""
    if not LANGGRAPH_AVAILABLE:
        return None

    builder = StateGraph(ResolveIQState)

    # Add thin nodes
    builder.add_node("classification", classification_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("rca", rca_node)
    builder.add_node("resolution", resolution_node)

    # Define linear execution edges
    builder.add_edge(START, "classification")
    builder.add_edge("classification", "retrieval")
    builder.add_edge("retrieval", "rca")
    builder.add_edge("rca", "resolution")
    builder.add_edge("resolution", END)

    return builder.compile()


async def run_orchestration_graph(incident: CanonicalIncident) -> ResolveIQState:
    """
    Executes the compiled LangGraph workflow graph or fallback linear runner.
    """
    initial_state: ResolveIQState = {"incident": incident}
    graph = build_resolveiq_graph()

    if graph is not None:
        final_state = await graph.ainvoke(initial_state)
        return final_state

    # Pure Python execution fallback if LangGraph runtime is omitted
    c_res = await classification_node(initial_state)
    initial_state.update(c_res)

    r_res = await retrieval_node(initial_state)
    initial_state.update(r_res)

    rca_res = await rca_node(initial_state)
    initial_state.update(rca_res)

    res_res = await resolution_node(initial_state)
    initial_state.update(res_res)

    return initial_state
