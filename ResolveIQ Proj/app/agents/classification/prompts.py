import json
from typing import Dict, Any, Optional
from app.schemas.incident import CanonicalIncident

SYSTEM_PROMPT = """You are ResolveIQ's Classification Agent.

Your only responsibility is to classify the IT incident into:
- category
- affected service

Use only:
- incident title
- incident description
- incident severity
- optional comments

Return only valid JSON in the following format:
{
  "category": "Network",
  "service": "VPN"
}

Never include:
- confidence
- RCA
- resolution
- explanations
- metadata
"""


def format_classification_user_prompt(incident: CanonicalIncident) -> str:
    """
    Formats user prompt for Classification Agent.
    Sends ONLY title, description, severity, and optional comments.
    """
    comments = None
    if isinstance(incident.metadata, dict):
        comments = incident.metadata.get("comments")

    payload: Dict[str, Any] = {
        "title": incident.title,
        "description": incident.description or "",
        "severity": incident.severity or incident.priority or "Medium",
    }
    if comments is not None:
        payload["comments"] = comments

    return f"Incident to classify:\n{json.dumps(payload, indent=2)}"
