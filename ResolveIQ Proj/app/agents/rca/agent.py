from typing import List
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RCAResult, RetrievedChunk
from app.agents.rca.prompts import SYSTEM_PROMPT, format_rca_user_prompt
from app.core.llm_client import execute_llm_request


async def run_rca(
    incident: CanonicalIncident,
    retrieved_chunks: List[RetrievedChunk]
) -> RCAResult:
    """
    Determines the most likely root cause using:
    - incident information
    - top 3 to 5 retrieved evidence chunks

    Rules:
    - Base conclusion strictly on provided evidence.
    - If evidence is insufficient, returns status 'insufficient_evidence' and root_cause=None.
    - Does NOT receive classification results, resolution details, or workflow state.
    """
    # Enforce maximum of 5 chunks
    chunks = retrieved_chunks[:5] if retrieved_chunks else []

    user_prompt = format_rca_user_prompt(incident, chunks)

    result = await execute_llm_request(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=RCAResult,
        operation_name="RCA Agent",
    )
    return result
