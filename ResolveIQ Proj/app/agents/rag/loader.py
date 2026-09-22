"""
Dataset loader module for ResolveIQ RAG.
Loads raw runbooks and postmortems from input directory.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


def load_json_files(directory_path: str) -> List[Dict[str, Any]]:
    """Loads all JSON files from a specified directory."""
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        return []

    documents = []
    for file_path in path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_file_path"] = str(file_path)
                documents.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return documents
