"""
Embedding generation module for ResolveIQ RAG.
Uses SentenceTransformers to generate embeddings with graceful fallback.
"""
import os
from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except (ImportError, OSError, Exception):
    SentenceTransformer = None


class ResolveIQEmbedder:
    """
    Wrapper around sentence-transformers to generate embeddings for document chunks.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None

        if SentenceTransformer is not None and os.environ.get("RESOLVEIQ_FAST_TEST") != "1":
            try:
                self.model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                print(f"Warning: Could not load SentenceTransformer model '{model_name}': {e}")

    def get_dimension(self) -> int:
        """Return the embedding dimension of the loaded model (384 for bge-small-en-v1.5)."""
        if self.model is not None:
            if hasattr(self.model, "get_embedding_dimension"):
                return self.model.get_embedding_dimension()
            return self.model.get_sentence_embedding_dimension()
        return 384

    def get_model_name(self) -> str:
        return self.model_name

    def embed_batch(
        self, texts: List[str], batch_size: int = 32, show_progress_bar: bool = False
    ) -> np.ndarray:
        """
        Generate normalized embeddings for a batch of texts.
        """
        if self.model is not None:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                normalize_embeddings=True,
            )
            return embeddings

        # Fallback deterministic pseudo-embeddings for testing without heavy model download
        dim = self.get_dimension()
        result = []
        for text in texts:
            seed = sum(ord(c) for c in text) % 1000
            np.random.seed(seed)
            vec = np.random.randn(dim)
            norm = np.linalg.norm(vec)
            result.append(vec / (norm if norm > 0 else 1.0))
        return np.array(result)
