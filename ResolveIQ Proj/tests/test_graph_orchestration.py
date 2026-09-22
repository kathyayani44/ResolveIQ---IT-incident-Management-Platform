import unittest
from unittest.mock import patch, AsyncMock
from app.schemas.incident import CanonicalIncident
from app.schemas.agent_results import ClassificationResult, RCAResult, RCAEvidence, ResolutionResult, RetrievedChunk
from app.schemas.rag import RetrievalResult
from app.graph.state import ResolveIQState
from app.graph.nodes import (
    classification_node,
    retrieval_node,
    rca_node,
    resolution_node
)
from app.graph.builder import run_orchestration_graph, build_resolveiq_graph


class TestGraphOrchestration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.incident = CanonicalIncident(
            issue_key="GRAPH-101",
            title="Kafka Consumer Lag Spike",
            description="Consumer group offset falling behind in payment events topic.",
            severity="High"
        )
        self.classification = ClassificationResult(category="Streaming", service="Kafka")
        self.retrieval = RetrievalResult(
            query="Kafka Consumer Lag Spike Streaming Kafka High",
            retrieved_chunks=[
                RetrievedChunk(chunk_id="chunk_k1", text="Increase num.partitions and max.poll.records", source="kafka_kb.json", document_type="runbooks", score=0.94)
            ]
        )
        self.rca = RCAResult(
            root_cause="Consumer thread deadlocked on downstream DB write.",
            status="identified",
            evidence=[RCAEvidence(chunk_id="chunk_k1", reason="Matches thread dump deadlock pattern.")]
        )
        self.resolution = ResolutionResult(
            recommendation="Restart consumer pod and scale consumer group instances.",
            steps=["1. kubectl rollout restart deployment/kafka-consumer", "2. Scale replicas to 5"],
            risks=["Temporary rebalance lag"],
            evidence=["chunk_k1"]
        )

    @patch("app.graph.nodes.classification_node.run_classification", new_callable=AsyncMock)
    async def test_classification_node(self, mock_run):
        mock_run.return_value = self.classification
        state: ResolveIQState = {"incident": self.incident}

        output = await classification_node(state)
        self.assertEqual(output["classification"], self.classification)
        mock_run.assert_called_once_with(self.incident)

    @patch("app.graph.nodes.retrieval_node.run_rag_retrieval", new_callable=AsyncMock)
    async def test_retrieval_node(self, mock_run):
        mock_run.return_value = self.retrieval
        state: ResolveIQState = {"incident": self.incident, "classification": self.classification}

        output = await retrieval_node(state)
        self.assertEqual(output["retrieval"], self.retrieval)
        mock_run.assert_called_once_with(incident=self.incident, classification=self.classification, top_k=5)

    @patch("app.graph.nodes.rca_node.run_rca", new_callable=AsyncMock)
    async def test_rca_node(self, mock_run):
        mock_run.return_value = self.rca
        state: ResolveIQState = {"incident": self.incident, "retrieval": self.retrieval}

        output = await rca_node(state)
        self.assertEqual(output["rca"], self.rca)
        mock_run.assert_called_once_with(incident=self.incident, retrieved_chunks=self.retrieval.retrieved_chunks)

    @patch("app.graph.nodes.resolution_node.run_resolution", new_callable=AsyncMock)
    async def test_resolution_node(self, mock_run):
        mock_run.return_value = self.resolution
        state: ResolveIQState = {"incident": self.incident, "retrieval": self.retrieval, "rca": self.rca}

        output = await resolution_node(state)
        self.assertEqual(output["resolution"], self.resolution)
        mock_run.assert_called_once_with(incident=self.incident, rca=self.rca, relevant_knowledge=self.retrieval.retrieved_chunks)

    @patch("app.graph.nodes.resolution_node.run_resolution", new_callable=AsyncMock)
    @patch("app.graph.nodes.rca_node.run_rca", new_callable=AsyncMock)
    @patch("app.graph.nodes.retrieval_node.run_rag_retrieval", new_callable=AsyncMock)
    @patch("app.graph.nodes.classification_node.run_classification", new_callable=AsyncMock)
    async def test_full_graph_orchestration_flow(
        self, mock_classif, mock_retrieval, mock_rca, mock_resolution
    ):
        mock_classif.return_value = self.classification
        mock_retrieval.return_value = self.retrieval
        mock_rca.return_value = self.rca
        mock_resolution.return_value = self.resolution

        final_state: ResolveIQState = await run_orchestration_graph(self.incident)

        self.assertIn("incident", final_state)
        self.assertIn("classification", final_state)
        self.assertIn("retrieval", final_state)
        self.assertIn("rca", final_state)
        self.assertIn("resolution", final_state)

        # Assert no revision fields exist
        self.assertNotIn("revision", final_state)
        self.assertNotIn("needs_revision", final_state)
        self.assertNotIn("revision_feedback", final_state)
