"""Tests for PipelineSampler and pipeline.py return_context flag."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.context import Citation, PipelineResult, QueryContext, SearchResult
from src.personalization.models import HealthLiteracy, Sex, UserProfile


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_profile() -> UserProfile:
    return UserProfile(
        age=40,
        sex=Sex.PREFER_NOT_TO_SAY,
        health_literacy=HealthLiteracy.MEDIUM,
        conditions=[],
        medications=[],
    )


def _make_ctx(query: str = "test query") -> QueryContext:
    """Return a fully-populated QueryContext as agents would produce."""
    ctx = QueryContext(query=query, user_profile=_make_profile())
    ctx.category = "heart_blood_vessels"
    ctx.classification_method = "embedding"
    ctx.normalized_terms = ["heart failure", "symptoms"]
    ctx.brain_context = "## Heart & Blood Vessels\nSource priority: AHA guidelines..."
    ctx.retrieval_plan = MagicMock(must_load=["heart_blood_vessels"], may_load=["medications_drug_safety"])
    ctx.search_results = [
        SearchResult(
            record_id="1",
            source_table="medmcqa_records",
            primary_category="heart_blood_vessels",
            quality_tier="TIER_A",
            chunk_text="Heart failure symptoms include dyspnea.",
            relevance_score=0.85,
            rrf_score=0.016,
        )
    ]
    ctx.raw_answer = "Heart failure causes shortness of breath."
    ctx.final_answer = "Heart failure causes shortness of breath. Consult a doctor."
    ctx.confidence = 0.82
    ctx.disclaimer = "This is informational only."
    ctx.uncertainty_flags = []
    ctx.verified_citations = [
        Citation(
            record_id="1",
            source_table="medmcqa_records",
            quality_tier="TIER_A",
            text_snippet="Heart failure symptoms include dyspnea.",
            relevance_score=0.85,
        )
    ]
    return ctx


def _make_pipeline(ctx: QueryContext) -> MagicMock:
    """Return a mock Pipeline whose run() returns (PipelineResult, ctx)."""
    pipeline = MagicMock()
    result = PipelineResult.from_context(ctx)

    async def _run(query, user_profile, return_context=False):
        if return_context:
            return result, ctx
        return result

    pipeline.run = _run
    pipeline._adaptive = MagicMock()
    return pipeline


# ---------------------------------------------------------------------------
# Task 1: return_context flag on real Pipeline
# ---------------------------------------------------------------------------

def test_pipeline_run_returns_tuple_when_return_context_true():
    """Pipeline.run(return_context=True) returns (PipelineResult, QueryContext)."""
    from src.pipeline import Pipeline

    profile = _make_profile()

    p = Pipeline.__new__(Pipeline)

    async def _agent_run(ctx):
        return ctx

    p._agent_a = MagicMock()
    p._agent_a.run = AsyncMock(side_effect=_agent_run)
    p._agent_b = MagicMock()
    p._agent_b.run = AsyncMock(side_effect=_agent_run)
    p._agent_c = MagicMock()
    p._agent_c.run = AsyncMock(side_effect=_agent_run)

    async def _agent_d_run(ctx):
        ctx.final_answer = "Test answer"
        ctx.confidence = 0.7
        ctx.disclaimer = None
        ctx.uncertainty_flags = []
        ctx.verified_citations = []
        return ctx

    p._agent_d = MagicMock()
    p._agent_d.run = AsyncMock(side_effect=_agent_d_run)
    p._adaptive = MagicMock()

    result = asyncio.run(p.run("test query", profile, return_context=True))

    assert isinstance(result, tuple), "Expected a tuple when return_context=True"
    assert len(result) == 2
    pipeline_result, query_ctx = result
    assert isinstance(pipeline_result, PipelineResult)
    assert isinstance(query_ctx, QueryContext)
    assert query_ctx.query == "test query"


def test_pipeline_run_returns_pipeline_result_by_default():
    """Pipeline.run() without return_context returns plain PipelineResult."""
    from src.pipeline import Pipeline

    profile = _make_profile()
    p = Pipeline.__new__(Pipeline)

    async def _agent_run(ctx):
        return ctx

    p._agent_a = MagicMock()
    p._agent_a.run = AsyncMock(side_effect=_agent_run)
    p._agent_b = MagicMock()
    p._agent_b.run = AsyncMock(side_effect=_agent_run)
    p._agent_c = MagicMock()
    p._agent_c.run = AsyncMock(side_effect=_agent_run)

    async def _agent_d_run(ctx):
        ctx.final_answer = "Test answer"
        ctx.confidence = 0.7
        ctx.disclaimer = None
        ctx.uncertainty_flags = []
        ctx.verified_citations = []
        return ctx

    p._agent_d = MagicMock()
    p._agent_d.run = AsyncMock(side_effect=_agent_d_run)
    p._adaptive = MagicMock()

    result = asyncio.run(p.run("test query", profile))

    assert isinstance(result, PipelineResult), "Default should return PipelineResult, not tuple"


# ---------------------------------------------------------------------------
# Task 2: _extract_query, _build_agent_trace, PipelineSampler
# ---------------------------------------------------------------------------

class TestExtractQuery:
    def test_extracts_last_user_message(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _extract_query

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "What causes heart failure?"},
        ]
        assert _extract_query(messages) == "What causes heart failure?"

    def test_returns_empty_string_when_no_user_message(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _extract_query

        messages = [{"role": "system", "content": "You are helpful."}]
        assert _extract_query(messages) == ""

    def test_handles_list_content_parts(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _extract_query

        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "What is aspirin?"}],
            }
        ]
        assert _extract_query(messages) == "What is aspirin?"


class TestBuildAgentTrace:
    def test_final_answer_populated(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx("heart failure symptoms")
        trace = _build_agent_trace("heart failure symptoms", ctx)
        assert trace.final_answer == ctx.final_answer

    def test_reasoning_trace_has_all_agent_steps(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx("heart failure symptoms")
        trace = _build_agent_trace("heart failure symptoms", ctx)

        assert len(trace.reasoning_trace) >= 5
        combined = " ".join(trace.reasoning_trace)
        assert "Agent A" in combined
        assert "Agent B" in combined
        assert "Agent C" in combined
        assert "Agent D" in combined

    def test_reasoning_trace_includes_category_and_method(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx()
        trace = _build_agent_trace("query", ctx)
        assert "heart_blood_vessels" in trace.reasoning_trace[0]
        assert "embedding" in trace.reasoning_trace[0]

    def test_tool_calls_include_brain_graph(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx()
        trace = _build_agent_trace("query", ctx)
        tool_names = [tc.tool_name for tc in trace.tool_calls]
        assert "brain_graph" in tool_names

    def test_tool_calls_include_hybrid_db_search(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx()
        trace = _build_agent_trace("query", ctx)
        tool_names = [tc.tool_name for tc in trace.tool_calls]
        assert "hybrid_db_search" in tool_names

    def test_retrieval_results_mapped_from_citations(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx()
        trace = _build_agent_trace("query", ctx)
        assert len(trace.retrieval_results) == 1
        item = trace.retrieval_results[0]
        assert item.source == "medmcqa_records"
        assert item.content == "Heart failure symptoms include dyspnea."
        assert item.relevance_score == pytest.approx(0.85)

    def test_uncertainty_flags_appear_in_reasoning_trace(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = _make_ctx()
        ctx.uncertainty_flags = ["low evidence", "contradictory sources"]
        trace = _build_agent_trace("query", ctx)
        combined = " ".join(trace.reasoning_trace)
        assert "low evidence" in combined

    def test_empty_context_does_not_raise(self):
        from simple_evals.agentic_medbench.pipeline_sampler import _build_agent_trace

        ctx = QueryContext(query="bare query", user_profile=_make_profile())
        ctx.final_answer = "Some answer"
        trace = _build_agent_trace("bare query", ctx)
        assert trace.final_answer == "Some answer"
        assert isinstance(trace.reasoning_trace, list)


class TestPipelineSampler:
    def test_raises_on_unknown_profile(self):
        from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler

        with pytest.raises(ValueError, match="Unknown profile"):
            PipelineSampler(pipeline=MagicMock(), profile_name="nonexistent_profile")

    def test_call_returns_sampler_response(self):
        from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler
        from simple_evals.types import SamplerResponse

        ctx = _make_ctx("What are heart failure symptoms?")
        pipeline = _make_pipeline(ctx)

        sampler = PipelineSampler(pipeline=pipeline, profile_name="default")
        messages = [{"role": "user", "content": "What are heart failure symptoms?"}]

        response = sampler(messages)

        assert isinstance(response, SamplerResponse)
        assert response.response_text == ctx.final_answer

    def test_response_metadata_contains_agent_trace(self):
        from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler

        ctx = _make_ctx("What are heart failure symptoms?")
        pipeline = _make_pipeline(ctx)
        sampler = PipelineSampler(pipeline=pipeline, profile_name="default")
        messages = [{"role": "user", "content": "What are heart failure symptoms?"}]

        response = sampler(messages)

        assert "agent_trace" in response.response_metadata
        trace_dict = response.response_metadata["agent_trace"]
        assert "final_answer" in trace_dict
        assert "tool_calls" in trace_dict
        assert "reasoning_trace" in trace_dict
        assert "retrieval_results" in trace_dict

    def test_actual_queried_message_list_preserved(self):
        from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler

        ctx = _make_ctx()
        pipeline = _make_pipeline(ctx)
        sampler = PipelineSampler(pipeline=pipeline, profile_name="default")
        messages = [{"role": "user", "content": "test query"}]

        response = sampler(messages)
        assert response.actual_queried_message_list == messages

    def test_empty_message_list_does_not_raise(self):
        from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler

        ctx = _make_ctx("")
        pipeline = _make_pipeline(ctx)
        sampler = PipelineSampler(pipeline=pipeline, profile_name="default")

        response = sampler([])
        assert isinstance(response.response_text, str)

    def test_profile_preset_assigned_to_sampler(self):
        from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler
        from src.personalization.models import HealthLiteracy

        ctx = _make_ctx()
        pipeline = _make_pipeline(ctx)
        sampler = PipelineSampler(pipeline=pipeline, profile_name="low_literacy_patient")

        assert sampler.user_profile.health_literacy == HealthLiteracy.LOW
        assert sampler.user_profile.age == 55

# ---------------------------------------------------------------------------
# Task 4: GPT-4o pipeline paths
# ---------------------------------------------------------------------------

class TestAgentCGpt4o:
    def test_agent_c_uses_openai_when_anthropic_none(self):
        """Agent C calls openai.chat.completions when anthropic_client is None."""
        import asyncio
        from unittest.mock import MagicMock, patch
        from src.agents.agent_c import SynthesisAgent
        from src.agents.context import QueryContext, SearchResult
        from src.personalization.models import HealthLiteracy, Sex, UserProfile

        mock_openai = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "GPT-4o answer"
        mock_openai.chat.completions.create.return_value = mock_response

        mock_searcher = MagicMock()
        mock_searcher.search.return_value = []

        agent_c = SynthesisAgent(
            searcher=mock_searcher,
            anthropic_client=None,
            openai_client=mock_openai,
        )

        ctx = QueryContext(
            query="What causes hypertension?",
            user_profile=UserProfile(
                age=40,
                sex=Sex.PREFER_NOT_TO_SAY,
                health_literacy=HealthLiteracy.MEDIUM,
                conditions=[],
                medications=[],
            ),
        )
        ctx.category = "heart_blood_vessels"
        ctx.normalized_terms = ["hypertension"]
        ctx.brain_context = "## Heart rules"
        ctx.retrieval_plan = MagicMock()

        result_ctx = asyncio.run(agent_c.run(ctx))

        mock_openai.chat.completions.create.assert_called_once()
        assert result_ctx.raw_answer == "GPT-4o answer"

    def test_agent_c_raises_when_both_clients_none(self):
        """Agent C raises AttributeError when both clients are None and run() is called."""
        import asyncio
        from src.agents.agent_c import SynthesisAgent
        from src.agents.context import QueryContext
        from src.personalization.models import HealthLiteracy, Sex, UserProfile

        mock_searcher = MagicMock()
        mock_searcher.search.return_value = []

        agent_c = SynthesisAgent(
            searcher=mock_searcher,
            anthropic_client=None,
            openai_client=None,
        )

        ctx = QueryContext(
            query="test",
            user_profile=UserProfile(
                age=40,
                sex=Sex.PREFER_NOT_TO_SAY,
                health_literacy=HealthLiteracy.MEDIUM,
                conditions=[],
                medications=[],
            ),
        )
        ctx.category = "heart_blood_vessels"
        ctx.normalized_terms = ["test"]
        ctx.brain_context = ""
        ctx.retrieval_plan = MagicMock()

        with pytest.raises((AttributeError, TypeError)):
            asyncio.run(agent_c.run(ctx))


class TestPipelineUseGpt4oFlag:
    def test_pipeline_passes_none_anthropic_to_agents_when_use_gpt4o(self):
        """Pipeline passes anthropic_client=None to Agent A and C when use_gpt4o=True."""
        from unittest.mock import patch
        from src.pipeline import Pipeline

        mock_db = MagicMock()
        mock_openai = MagicMock()
        mock_anthropic = MagicMock()

        with (
            patch("src.pipeline.QueryUnderstandingAgent") as MockA,
            patch("src.pipeline.RetrievalPlanningAgent"),
            patch("src.pipeline.SynthesisAgent") as MockC,
            patch("src.pipeline.VerificationAgent"),
            patch("src.pipeline.HybridSearcher"),
            patch("src.pipeline.build_base_graph"),
            patch("src.pipeline.UserSubgraphBuilder"),
            patch("src.pipeline.QueryGraphMerger"),
            patch("src.pipeline.AdaptiveLearner"),
        ):
            MockA.return_value = MagicMock()
            MockA.return_value.build_centroids = MagicMock()
            MockC.return_value = MagicMock()

            Pipeline(
                db_conn=mock_db,
                openai_client=mock_openai,
                anthropic_client=mock_anthropic,
                build_centroids=False,
                use_gpt4o=True,
            )

            # Agent A should receive anthropic_client=None
            a_kwargs = MockA.call_args.kwargs
            assert a_kwargs.get("anthropic_client") is None

            # Agent C should receive anthropic_client=None and openai_client set
            c_kwargs = MockC.call_args.kwargs
            assert c_kwargs.get("anthropic_client") is None
            assert c_kwargs.get("openai_client") is mock_openai
