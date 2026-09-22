"""
Qdrant vector store module for ResolveIQ.
Handles connection to local Qdrant, collection management, and vector insertion.
"""
import uuid
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    QdrantClient = None
    models = None


class ResolveIQQdrantStore:
    """
    Wrapper around QdrantClient for local persistent storage.
    """

    def __init__(self, db_path: str = "data/qdrant_db"):
        if QdrantClient is None:
            raise ImportError(
                "qdrant-client is not installed. "
                "Please install it using 'pip install qdrant-client'."
            )
        
        self.db_path = db_path
        self.client = QdrantClient(path=self.db_path)
        print(f"Connected to local Qdrant at {self.db_path}")

    def setup_collection(
        self, collection_name: str, dimension: int, rebuild: bool = False
    ) -> bool:
        """
        Setup a Qdrant collection.
        If rebuild is True, delete if it exists and recreate.
        If rebuild is False, do not recreate if it exists.
        Returns True if the collection is newly created or exists and we are ready to write.
        Returns False if the collection already exists and rebuild is False.
        """
        exists = self.client.collection_exists(collection_name)

        if exists:
            if rebuild:
                print(f"Collection '{collection_name}' exists. Rebuild requested. Deleting...")
                self.client.delete_collection(collection_name=collection_name)
            else:
                print(f"Collection '{collection_name}' already exists. Skipping recreation to avoid duplicates.")
                return False

        print(f"Creating collection '{collection_name}' with dimension {dimension}...")
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE
            )
        )
        print(f"Collection '{collection_name}' created successfully.")
        return True

    def insert_chunks(
        self, 
        collection_name: str, 
        chunks: List[Dict[str, Any]], 
        embeddings: np.ndarray,
        batch_size: int = 100
    ):
        """
        Insert chunks and their corresponding embeddings into the collection in batches.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")

        total = len(chunks)
        points = []

        for i in range(total):
            chunk = chunks[i]
            embedding = embeddings[i]
            
            # Use chunk_id as the ID for the point. Qdrant requires UUIDs or integers.
            # We can generate a UUID based on the string chunk_id to keep it deterministic.
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["chunk_id"]))
            
            # Payload is the entire chunk
            payload = chunk.copy()

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload
                )
            )

        # Upsert in batches
        for i in range(0, total, batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch
            )

    def search(
        self, collection_name: str, query_vector: np.ndarray, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for the closest vectors in a collection.
        """
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_vector.tolist(),
            limit=limit,
        ).points
        return [
            {
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get basic statistics for a collection.
        """
        if not self.client.collection_exists(collection_name):
            return {"status": "not_found"}
        
        info = self.client.get_collection(collection_name)
        return {
            "status": info.status,
            "points_count": info.points_count,
            "vectors_count": info.points_count
        }

    def get_sample_payload(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single sample payload from the collection.
        """
        if not self.client.collection_exists(collection_name):
            return None
        
        scroll_res, _ = self.client.scroll(
            collection_name=collection_name,
            limit=1
        )
        if scroll_res:
            return scroll_res[0].payload
        return None
