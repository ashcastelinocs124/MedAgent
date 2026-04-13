"""Tests for AgenticSampler — NO API calls.

Validates the AgentCondition enum, constructor behaviour under each condition,
and structural properties (tool availability, subgraph presence).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from simple_evals.agentic_medbench.agent_sampler import (
    AgentCondition,
    AgenticSampler,
)


# ---------------------------------------------------------------------------
# AgentCondition enum
# ---------------------------------------------------------------------------


class TestAgentCondition:
    """Verify the AgentCondition enum has exactly three values."""

    def test_has_three_values(self):
        members = list(AgentCondition)
        assert len(members) == 3

    def test_expected_values_exist(self):
        assert AgentCondition.BASELINE is not None
        assert AgentCondition.BRAIN_STEERED is not None
        assert AgentCondition.FULLY_STEERED is not None

    def test_values_are_distinct(self):
        values = {m.value for m in AgentCondition}
        assert len(values) == 3


# ---------------------------------------------------------------------------
# AgenticSampler — BASELINE condition
# ---------------------------------------------------------------------------


class TestBaselineSampler:
    """BASELINE condition: brain_graph must NOT be available."""

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_baseline_excludes_brain_graph(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BASELINE,
        )
        schema_names = {
            s["function"]["name"] for s in sampler.tool_schemas
        }
        assert "brain_graph" not in schema_names

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_baseline_includes_other_tools(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BASELINE,
        )
        schema_names = {
            s["function"]["name"] for s in sampler.tool_schemas
        }
        assert "pubmed_search" in schema_names
        assert "drug_interaction_db" in schema_names
        assert "web_search" in schema_names

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_baseline_has_no_merger(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BASELINE,
        )
        assert sampler.merger is None

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_baseline_has_no_user_subgraph(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BASELINE,
        )
        assert sampler.user_subgraph is None


# ---------------------------------------------------------------------------
# AgenticSampler — BRAIN_STEERED condition
# ---------------------------------------------------------------------------


class TestBrainSteeredSampler:
    """BRAIN_STEERED condition: brain_graph must be available, no user subgraph."""

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_brain_steered_includes_brain_graph(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BRAIN_STEERED,
        )
        schema_names = {
            s["function"]["name"] for s in sampler.tool_schemas
        }
        assert "brain_graph" in schema_names

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_brain_steered_includes_all_four_tools(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BRAIN_STEERED,
        )
        schema_names = {
            s["function"]["name"] for s in sampler.tool_schemas
        }
        assert schema_names == {
            "brain_graph",
            "pubmed_search",
            "drug_interaction_db",
            "web_search",
        }

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_brain_steered_has_merger(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BRAIN_STEERED,
        )
        assert sampler.merger is not None

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_brain_steered_has_category_names(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BRAIN_STEERED,
        )
        assert sampler.category_names is not None
        assert len(sampler.category_names) > 0

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_brain_steered_has_no_user_subgraph(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.BRAIN_STEERED,
        )
        assert sampler.user_subgraph is None


# ---------------------------------------------------------------------------
# AgenticSampler — FULLY_STEERED condition
# ---------------------------------------------------------------------------


class TestFullySteeredSampler:
    """FULLY_STEERED condition: brain_graph + user subgraph with anchored categories."""

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_fully_steered_includes_brain_graph(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.FULLY_STEERED,
            profile_name="elderly_comorbid",
        )
        schema_names = {
            s["function"]["name"] for s in sampler.tool_schemas
        }
        assert "brain_graph" in schema_names

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_fully_steered_has_user_subgraph(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.FULLY_STEERED,
            profile_name="elderly_comorbid",
        )
        assert sampler.user_subgraph is not None

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_fully_steered_subgraph_has_anchored_categories(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.FULLY_STEERED,
            profile_name="elderly_comorbid",
        )
        # elderly_comorbid has CHF, COPD, Arthritis -> 3 anchored categories
        anchored = sampler.user_subgraph.anchored_categories
        assert len(anchored) >= 3
        assert "cat:heart_blood_vessels" in anchored
        assert "cat:breathing_lungs" in anchored
        assert "cat:bones_joints_muscles" in anchored

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_fully_steered_has_profile(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.FULLY_STEERED,
            profile_name="elderly_comorbid",
        )
        assert sampler.profile is not None
        assert sampler.profile.age == 72

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_fully_steered_has_merger(self, mock_openai_cls):
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.FULLY_STEERED,
            profile_name="low_literacy_patient",
        )
        assert sampler.merger is not None

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_fully_steered_default_profile(self, mock_openai_cls):
        """Using 'default' profile should still build a subgraph (even if no anchors)."""
        sampler = AgenticSampler(
            model="gpt-4o",
            condition=AgentCondition.FULLY_STEERED,
            profile_name="default",
        )
        assert sampler.user_subgraph is not None
        assert sampler.profile is not None


# ---------------------------------------------------------------------------
# Constructor defaults
# ---------------------------------------------------------------------------


class TestSamplerDefaults:
    """Verify default constructor parameters."""

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_default_model(self, mock_openai_cls):
        sampler = AgenticSampler()
        assert sampler.model == "gpt-4o"

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_default_condition_is_baseline(self, mock_openai_cls):
        sampler = AgenticSampler()
        assert sampler.condition == AgentCondition.BASELINE

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_default_temperature(self, mock_openai_cls):
        sampler = AgenticSampler()
        assert sampler.temperature == 0.3

    @patch("simple_evals.agentic_medbench.agent_sampler.OpenAI")
    def test_default_max_tokens(self, mock_openai_cls):
        sampler = AgenticSampler()
        assert sampler.max_tokens == 4096


# ---------------------------------------------------------------------------
# _parse_retrieval_items helper
# ---------------------------------------------------------------------------


def test_parse_retrieval_items_pubmed():
    """PubMed results should be parsed into RetrievalItem objects."""
    from simple_evals.agentic_medbench.agent_sampler import _parse_retrieval_items

    result = (
        "PubMed results for 'aspirin' (2 articles):\n"
        "- PMID 12345: Aspirin and cardiovascular risk (JAMA, 2024)\n"
        "- PMID 67890: Low-dose aspirin therapy (Lancet, 2023)"
    )
    items = _parse_retrieval_items("pubmed_search", result)

    assert len(items) == 2
    assert items[0].source == "PMID 12345"
    assert "Aspirin and cardiovascular risk" in items[0].content
    assert items[0].relevance_score == 1.0
    assert items[1].source == "PMID 67890"


def test_parse_retrieval_items_drug_interaction():
    """Drug interaction results should be wrapped as a single RetrievalItem."""
    from simple_evals.agentic_medbench.agent_sampler import _parse_retrieval_items

    result = "Drug interaction data for 'warfarin':\nWarfarin interacts with aspirin."
    items = _parse_retrieval_items("drug_interaction_db", result)

    assert len(items) == 1
    assert items[0].source == "openfda"
    assert "warfarin" in items[0].content.lower()


def test_parse_retrieval_items_error_returns_empty():
    """Error responses should produce no retrieval items."""
    from simple_evals.agentic_medbench.agent_sampler import _parse_retrieval_items

    items = _parse_retrieval_items("pubmed_search", "Error searching PubMed: HTTP 429")
    assert items == []


def test_parse_retrieval_items_non_retrieval_tool_returns_empty():
    """Non-retrieval tools (brain_graph, web_search) should produce no items."""
    from simple_evals.agentic_medbench.agent_sampler import _parse_retrieval_items

    items = _parse_retrieval_items("brain_graph", "Some brain content")
    assert items == []

    items = _parse_retrieval_items("web_search", "Some web content")
    assert items == []


# ---------------------------------------------------------------------------
# Reasoning trace capture from tool calls
# ---------------------------------------------------------------------------


def test_reasoning_trace_captured_from_tool_calls():
    """Each tool call should generate a reasoning trace entry."""
    import json

    from simple_evals.agentic_medbench.agent_sampler import AgenticSampler, AgentCondition

    sampler = AgenticSampler.__new__(AgenticSampler)
    sampler.model = "gpt-4o"
    sampler.condition = AgentCondition.BASELINE
    sampler.temperature = 0.3
    sampler.max_tokens = 4096
    sampler.available_tools = ["pubmed_search"]
    sampler.registry = MagicMock()
    sampler.registry.execute.return_value = "PubMed results for 'test' (1 articles):\n- PMID 11111: Test Article (Journal, 2024)"
    sampler.registry.get_schemas.return_value = []
    sampler.tool_schemas = []
    sampler.base_graph = None
    sampler.category_names = None
    sampler.merger = None
    sampler.profile = None
    sampler.user_subgraph = None
    sampler.client = MagicMock()

    # Mock two rounds: first returns tool call, second returns final answer
    tool_call_msg = MagicMock()
    tool_call_msg.tool_calls = [MagicMock()]
    tool_call_msg.tool_calls[0].function.name = "pubmed_search"
    tool_call_msg.tool_calls[0].function.arguments = json.dumps({"query": "aspirin"})
    tool_call_msg.tool_calls[0].id = "call_123"
    tool_call_msg.content = None
    tool_call_msg.model_dump.return_value = {"role": "assistant", "content": None, "tool_calls": []}

    final_msg = MagicMock()
    final_msg.tool_calls = None
    final_msg.content = "Here is my answer about aspirin."

    response1 = MagicMock()
    response1.choices = [MagicMock()]
    response1.choices[0].message = tool_call_msg

    response2 = MagicMock()
    response2.choices = [MagicMock()]
    response2.choices[0].message = final_msg

    sampler.client.chat.completions.create.side_effect = [response1, response2]

    result = sampler([{"role": "user", "content": "Tell me about aspirin"}])

    trace = result.response_metadata["agent_trace"]
    assert len(trace["reasoning_trace"]) >= 1, "Expected at least one reasoning trace entry"
    assert "pubmed_search" in trace["reasoning_trace"][0]
    assert "aspirin" in trace["reasoning_trace"][0]
