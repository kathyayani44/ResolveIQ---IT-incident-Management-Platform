import json
from typing import List
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import RetrievedChunk

SYSTEM_PROMPT = """You are ResolveIQ's RCA Agent.

Use only:
- incident information
- retrieved evidence

Determine the most likely root cause.

Rules:
- Base conclusions strictly and only on the provided evidence chunks.
- Never invent unsupported causes.
- If evidence is insufficient, set status to "insufficient_evidence", root_cause to null, and evidence to [].
- If evidence is sufficient, set status to "identified", state the root_cause clearly, and list evidence items with chunk_id and reason.
- Return only valid JSON in one of the following formats:

Format when evidence is identified:
{
  "root_cause": "VPN authentication service failed due to expired TLS certificate.",
  "status": "identified",
  "evidence": [
    {
      "chunk_id": "postmortem_231_02",
      "reason": "Historical incident matches exact TLS error message."
    }
  ]
}

Format when evidence is insufficient:
{
  "root_cause": null,
  "status": "insufficient_evidence",
  "evidence": []
}

Do not include:
- classification
- resolution
- metadata
"""


def format_rca_user_prompt(incident: CanonicalIncident, retrieved_chunks: List[RetrievedChunk]) -> str:
    """
    Formats user prompt for RCA Agent.
    Sends ONLY incident information and top 3-5 retrieved evidence chunks.
    """
    # Enforce max 5 chunks limit as per contract
    chunks_to_send = retrieved_chunks[:5] if retrieved_chunks else []

    chunks_data = [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            **({"source": chunk.source} if chunk.source else {}),
            **({"document_type": chunk.document_type} if chunk.document_type else {})
        }
        for chunk in chunks_to_send
    ]

    payload = {
        "incident": {
            "title": incident.title,
            "description": incident.description or "",
            "severity": incident.severity or incident.priority or "Medium",
        },
        "retrieved_chunks": chunks_data,
    }

    return f"Incident and retrieved evidence for RCA:\n{json.dumps(payload, indent=2)}"
