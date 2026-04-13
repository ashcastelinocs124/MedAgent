"""Test that Pipeline passes memory store to agents."""
from unittest.mock import MagicMock, patch


def test_pipeline_creates_memory_store():
    """Pipeline with memory_dir creates and passes UserMemoryStore."""
    with patch("src.pipeline.build_base_graph") as mock_graph, \
         patch("src.pipeline.UserSubgraphBuilder"), \
         patch("src.pipeline.QueryGraphMerger"), \
         patch("src.pipeline.HybridSearcher"), \
         patch("src.pipeline.AdaptiveLearner"), \
         patch("src.pipeline.QueryUnderstandingAgent") as mock_a, \
         patch("src.pipeline.RetrievalPlanningAgent") as mock_b, \
         patch("src.pipeline.SynthesisAgent"), \
         patch("src.pipeline.VerificationAgent"):

        mock_graph.return_value = MagicMock()

        from src.pipeline import Pipeline
        pipeline = Pipeline(
            db_conn=MagicMock(),
            openai_client=MagicMock(),
            memory_dir="users",
        )

        # Agent A should have received memory_store kwarg
        a_call = mock_a.call_args
        assert a_call.kwargs.get("memory_store") is not None

        # Agent B should have received memory_store kwarg
        b_call = mock_b.call_args
        assert b_call.kwargs.get("memory_store") is not None


def test_pipeline_without_memory_dir():
    """Pipeline without memory_dir passes None to agents."""
    with patch("src.pipeline.build_base_graph") as mock_graph, \
         patch("src.pipeline.UserSubgraphBuilder"), \
         patch("src.pipeline.QueryGraphMerger"), \
         patch("src.pipeline.HybridSearcher"), \
         patch("src.pipeline.AdaptiveLearner"), \
         patch("src.pipeline.QueryUnderstandingAgent") as mock_a, \
         patch("src.pipeline.RetrievalPlanningAgent") as mock_b, \
         patch("src.pipeline.SynthesisAgent"), \
         patch("src.pipeline.VerificationAgent"):

        mock_graph.return_value = MagicMock()

        from src.pipeline import Pipeline
        pipeline = Pipeline(
            db_conn=MagicMock(),
            openai_client=MagicMock(),
        )

        a_call = mock_a.call_args
        assert a_call.kwargs.get("memory_store") is None

        b_call = mock_b.call_args
        assert b_call.kwargs.get("memory_store") is None
