from typing import List
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RCAResult, ResolutionResult, RetrievedChunk
from app.agents.resolution.prompts import SYSTEM_PROMPT, format_resolution_user_prompt
from app.core.llm_client import execute_llm_request


async def run_resolution(
    incident: CanonicalIncident,
    rca: RCAResult,
    relevant_knowledge: List[RetrievedChunk]
) -> ResolutionResult:
    """
    Creates a practical recovery recommendation using:
    - incident details
    - RCA result
    - relevant knowledge/runbook information

    Rules:
    - If RAG returns zero evidence and RCA reports INSUFFICIENT_EVIDENCE, the LLM is NOT called.
    - Grounding is strictly evidence-based: Resolution must reference valid chunk IDs from relevant_knowledge.
    - Safe default: A resolution is NEVER considered grounded unless verified against retrieved chunks.
    """
    knowledge_chunks = relevant_knowledge or []

    # Rule 4 & 7: Do not invoke Resolution LLM when no relevant evidence exists
    if len(knowledge_chunks) == 0 and rca.status == "insufficient_evidence":
        return ResolutionResult(
            recommendation="Resolution blocked: No verified knowledge base runbook or postmortem evidence found for this incident.",
            steps=[],
            risks=["Ungrounded resolution: Action without verified runbook risks operational disruption."],
            evidence=[],
            is_grounded=False,
            grounding_type="insufficient_evidence",
            evidence_sources=[]
        )

    user_prompt = format_resolution_user_prompt(incident, rca, knowledge_chunks)

    result = await execute_llm_request(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=ResolutionResult,
        operation_name="Resolution Agent",
    )

    # Rule 3 & 6: Strictly verify referenced evidence chunks against retrieved knowledge
    valid_chunk_map = {chunk.chunk_id: chunk for chunk in knowledge_chunks}
    matched_chunk_ids = [cid for cid in (result.evidence or []) if cid in valid_chunk_map]

    if matched_chunk_ids and rca.status != "insufficient_evidence":
        result.is_grounded = True
        result.grounding_type = "rag_grounded"
        result.evidence_sources = [
            {
                "chunk_id": valid_chunk_map[cid].chunk_id,
                "source": valid_chunk_map[cid].source,
                "document_type": valid_chunk_map[cid].document_type,
                "score": valid_chunk_map[cid].score,
                "snippet": valid_chunk_map[cid].text[:200] if valid_chunk_map[cid].text else "",
            }
            for cid in matched_chunk_ids
        ]
    else:
        # Never consider grounded if evidence references are missing or RCA lacked evidence
        result.is_grounded = False
        result.grounding_type = "insufficient_evidence"
        result.evidence_sources = []

    return result

