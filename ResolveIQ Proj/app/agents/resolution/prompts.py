import json
from typing import List
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RCAResult, RetrievedChunk

SYSTEM_PROMPT = """You are ResolveIQ's Resolution Agent.

Generate a practical recovery recommendation.

Use only:
- incident
- RCA
- relevant knowledge

Rules:
- Produce actionable steps.
- Mention operational risks.
- Reference only provided evidence chunk IDs.
- Return only valid JSON in the following format:
{
  "recommendation": "High level recovery summary",
  "steps": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "risks": [
    "Operational risk 1 ..."
  ],
  "evidence": [
    "runbook_1023_04"
  ]
}

Never include:
- classification
- unrelated retrieval chunks
- metadata
"""


def format_resolution_user_prompt(
    incident: CanonicalIncident,
    rca: RCAResult,
    relevant_knowledge: List[RetrievedChunk]
) -> str:
    """
    Formats user prompt for Resolution Agent.
    Sends ONLY incident, RCA result, and relevant knowledge chunks.
    """
    knowledge_data = [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            **({"document_type": chunk.document_type} if chunk.document_type else {})
        }
        for chunk in (relevant_knowledge or [])
    ]

    payload = {
        "incident": {
            "title": incident.title,
            "description": incident.description or "",
            "severity": incident.severity or incident.priority or "Medium",
        },
        "rca": rca.model_dump(mode="json"),
        "relevant_knowledge": knowledge_data,
    }

    return f"Incident, RCA, and relevant knowledge for resolution:\n{json.dumps(payload, indent=2)}"
