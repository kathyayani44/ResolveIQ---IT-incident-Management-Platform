"""
Data normalizer for ResolveIQ RAG dataset records.
"""
from typing import Dict, Any, Optional


def normalize_record(raw_record: Dict[str, Any], doc_type: str = "runbook") -> Dict[str, Any]:
    """Normalizes raw input records into a uniform schema."""
    doc_id = raw_record.get("id") or raw_record.get("document_id") or raw_record.get("runbook_id") or raw_record.get("postmortem_id")
    title = raw_record.get("title") or raw_record.get("name") or "Untitled Document"

    content = raw_record.get("content") or raw_record.get("body") or raw_record.get("text") or ""
    if isinstance(content, list):
        content = "\n".join(str(item) for item in content)

    return {
        "document_id": str(doc_id) if doc_id else "unknown_doc",
        "document_type": doc_type,
        "title": title,
        "content": content,
        "source": raw_record.get("source", "dataset"),
        "metadata": {
            "category": raw_record.get("category"),
            "service": raw_record.get("service"),
            "company": raw_record.get("company"),
        }
    }
