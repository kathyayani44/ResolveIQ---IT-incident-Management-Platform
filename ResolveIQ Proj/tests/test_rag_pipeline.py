import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import numpy as np
from app.main import app
from app.schemas.incident import CanonicalIncident
from app.schemas.rag import RAGIncidentRequest, RAGResponse, RetrievalResult
from app.agents.rag.embedder import ResolveIQEmbedder
from app.agents.rag.vectorstore import ResolveIQQdrantStore
from app.agents.rag.retriever import ResolveIQRetriever
from app.agents.rag.reranker import ResolveIQReranker
from app.agents.rag.context_builder import build_context
from app.agents.rag.agent import run_rag_retrieval, run_rag_request_retrieval

client = TestClient(app)


class MockEmbedder:
    def embed_batch(self, texts, batch_size=32, show_progress_bar=False):
        res = []
        for t in texts:
            vec = np.ones(384, dtype=np.float32)
            res.append(vec / np.linalg.norm(vec))
        return np.array(res)

    def get_dimension(self):
        return 384


class MockReranker:
    def rerank(self, query, candidates, top_k=5):
        reranked = []
        for c in candidates[:top_k]:
            item = c.copy()
            item["rerank_score"] = 0.92
            reranked.append(item)
        return reranked


class TestRAGPipeline(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.embedder = MockEmbedder()
        self.store = ResolveIQQdrantStore(db_path=":memory:")
        self.retriever = ResolveIQRetriever(embedder=self.embedder, store=self.store)
        self.reranker = MockReranker()

        # Seed sample data into vector store
        chunks = [
            {
                "chunk_id": "runbook_vpn_01",
                "title": "VPN Gateway Troubleshooting",
                "content": "To resolve VPN gateway timeout, restart ipsec service and verify TLS certs.",
                "source": "runbook_vpn.json"
            },
            {
                "chunk_id": "postmortem_db_02",
                "title": "Database Outage Postmortem",
                "content": "Database pool exhausted due to leak in reporting service sessions.",
                "source": "postmortem_db.json"
            }
        ]
        embeddings = self.embedder.embed_batch([c["content"] for c in chunks])
        self.store.insert_chunks("resolveiq_runbooks", chunks[:1], embeddings[:1])
        self.store.insert_chunks("resolveiq_postmortems", chunks[1:], embeddings[1:])

    def test_embedder_vector_generation(self):
        vecs = self.embedder.embed_batch(["Test query"])
        self.assertEqual(len(vecs), 1)
        self.assertEqual(len(vecs[0]), 384)

    def test_retriever_and_reranker(self):
        results = self.retriever.retrieve("VPN timeout issue", top_k=2)
        self.assertGreater(len(results), 0)

        reranked = self.reranker.rerank("VPN timeout issue", list(results), top_k=2)
        self.assertGreater(len(reranked), 0)
        self.assertIn("rerank_score", reranked[0])

    def test_context_builder(self):
        chunks = [{
            "chunk_id": "test_chunk_1",
            "title": "Test Title",
            "content": "Test content snippet",
            "source": "test.json",
            "collection": "resolveiq_runbooks",
            "rerank_score": 0.95
        }]
        context = build_context("VPN issue", chunks)
        self.assertEqual(context["query"], "VPN issue")
        self.assertEqual(len(context["retrieved_context"]), 1)
        self.assertEqual(context["citations"], ["test_chunk_1"])

    @patch("app.agents.rag.agent.get_rag_components")
    async def test_canonical_incident_rag_retrieval(self, mock_get_components):
        mock_get_components.return_value = (self.retriever, self.reranker)

        incident = CanonicalIncident(
            issue_key="NET-500",
            title="VPN Connection Failure",
            description="Users report TLS handshake failure on primary VPN gateway.",
            severity="Critical"
        )
        response: RetrievalResult = await run_rag_retrieval(incident, top_k=2)
        self.assertIsInstance(response, RetrievalResult)
        self.assertIn("VPN Connection Failure", response.query)
        self.assertEqual(len(response.retrieved_chunks), 2)


@patch("app.agents.rag.agent.get_rag_components")
def test_api_rag_retrieve_endpoint(mock_get_components):
    mock_store = ResolveIQQdrantStore(db_path=":memory:")
    mock_retriever = ResolveIQRetriever(embedder=MockEmbedder(), store=mock_store)
    mock_get_components.return_value = (mock_retriever, MockReranker())

    req = {
        "title": "PostgreSQL High CPU Usage",
        "category": "Database",
        "service": "Postgres",
        "severity": "High"
    }
    response = client.post("/api/v1/rag/retrieve", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "retrieved_context" in data
    assert "citations" in data
