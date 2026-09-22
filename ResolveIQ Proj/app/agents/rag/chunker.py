"""
Chunker module for ResolveIQ RAG.
Chunks document content into semantic chunks for vector embedding.
"""
from typing import Dict, List, Any


def chunk_document(doc: Dict[str, Any], max_chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """Chunks a normalized document into smaller overlapping text chunks."""
    content = doc.get("content", "")
    doc_id = doc.get("document_id", "doc")
    title = doc.get("title", "")

    if not content:
        return []

    words = content.split()
    chunks = []
    chunk_idx = 0

    step = max(1, max_chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk_words = words[i : i + max_chunk_size]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "chunk_id": f"{doc_id}_chunk_{chunk_idx}",
            "document_id": doc_id,
            "title": title,
            "content": chunk_text,
            "section": f"Chunk {chunk_idx + 1}",
            "source": doc.get("source", "unknown"),
            "metadata": doc.get("metadata", {})
        })
        chunk_idx += 1

    return chunks
