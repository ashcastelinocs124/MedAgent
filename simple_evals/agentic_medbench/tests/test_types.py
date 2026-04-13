"""Tests for agentic_medbench core data models and unified scoring."""

import math
import time

import pytest

from simple_evals.agentic_medbench.types import (
    DIMENSION_WEIGHTS,
    AgentTrace,
    Correction,
    RetrievalItem,
    ToolCall,
    compute_unified_score,
)


# ---------------------------------------------------------------------------
# ToolCall
# ---------------------------------------------------------------------------

class TestToolCall:
    def test_creation(self):
        tc = ToolCall(
            tool_name="pubmed_search",
            arguments={"query": "aspirin dosage"},
            result='{"articles": []}',
            timestamp=1700000000.0,
        )
        assert tc.tool_name == "pubmed_search"
        assert tc.arguments == {"query": "aspirin dosage"}
        assert tc.result == '{"articles": []}'
        assert tc.timestamp == 1700000000.0


# ---------------------------------------------------------------------------
# Correction
# ---------------------------------------------------------------------------

class TestCorrection:
    def test_creation(self):
        c = Correction(
            original="Take 500mg ibuprofen every 2 hours",
            corrected="Take 200-400mg ibuprofen every 4-6 hours",
            reason="Original dosage exceeded safe maximum frequency",
        )
        assert c.original == "Take 500mg ibuprofen every 2 hours"
        assert c.corrected == "Take 200-400mg ibuprofen every 4-6 hours"
        assert c.reason == "Original dosage exceeded safe maximum frequency"


# ---------------------------------------------------------------------------
# RetrievalItem
# ---------------------------------------------------------------------------

class TestRetrievalItem:
    def test_creation(self):
        ri = RetrievalItem(
            source="PubMed:PMC12345",
            content="Aspirin reduces platelet aggregation...",
            relevance_score=0.92,
        )
        assert ri.source == "PubMed:PMC12345"
        assert ri.content == "Aspirin reduces platelet aggregation..."
        assert ri.relevance_score == 0.92


# ---------------------------------------------------------------------------
# AgentTrace
# ---------------------------------------------------------------------------

class TestAgentTrace:
    """Tests for AgentTrace creation and serialization."""

    def _make_full_trace(self) -> AgentTrace:
        """Build a fully-populated AgentTrace for reuse across tests."""
        return AgentTrace(
            final_answer="Take ibuprofen 200-400mg every 4-6 hours as needed.",
            tool_calls=[
                ToolCall(
                    tool_name="pubmed_search",
                    arguments={"query": "ibuprofen dosage adults"},
                    result='{"count": 5}',
                    timestamp=1700000000.0,
                ),
                ToolCall(
                    tool_name="drug_interaction_check",
                    arguments={"drugs": ["ibuprofen", "aspirin"]},
                    result='{"interaction": "moderate"}',
                    timestamp=1700000001.0,
                ),
            ],
            reasoning_trace=[
                "User asks about ibuprofen dosage.",
                "Need to verify safe dosing range via PubMed.",
                "Check for common drug interactions.",
            ],
            corrections=[
                Correction(
                    original="Take 500mg every 2 hours",
                    corrected="Take 200-400mg every 4-6 hours",
                    reason="Exceeded safe frequency",
                ),
            ],
            retrieval_results=[
                RetrievalItem(
                    source="PubMed:PMC12345",
                    content="Ibuprofen OTC dosing: 200-400mg q4-6h, max 1200mg/day.",
                    relevance_score=0.95,
                ),
            ],
        )

    def test_creation_with_all_fields(self):
        trace = self._make_full_trace()
        assert trace.final_answer == "Take ibuprofen 200-400mg every 4-6 hours as needed."
        assert len(trace.tool_calls) == 2
        assert len(trace.reasoning_trace) == 3
        assert len(trace.corrections) == 1
        assert len(trace.retrieval_results) == 1

    def test_creation_with_defaults(self):
        trace = AgentTrace(final_answer="No information found.")
        assert trace.final_answer == "No information found."
        assert trace.tool_calls == []
        assert trace.reasoning_trace == []
        assert trace.corrections == []
        assert trace.retrieval_results == []

    def test_to_dict_keys(self):
        trace = self._make_full_trace()
        d = trace.to_dict()
        expected_keys = {
            "final_answer",
            "tool_calls",
            "reasoning_trace",
            "corrections",
            "retrieval_results",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_final_answer(self):
        trace = self._make_full_trace()
        d = trace.to_dict()
        assert d["final_answer"] == trace.final_answer

    def test_to_dict_tool_calls_serialization(self):
        trace = self._make_full_trace()
        d = trace.to_dict()
        assert isinstance(d["tool_calls"], list)
        assert len(d["tool_calls"]) == 2
        tc0 = d["tool_calls"][0]
        assert tc0["tool_name"] == "pubmed_search"
        assert tc0["arguments"] == {"query": "ibuprofen dosage adults"}
        assert tc0["result"] == '{"count": 5}'
        assert tc0["timestamp"] == 1700000000.0

    def test_to_dict_corrections_serialization(self):
        trace = self._make_full_trace()
        d = trace.to_dict()
        assert isinstance(d["corrections"], list)
        assert len(d["corrections"]) == 1
        c0 = d["corrections"][0]
        assert c0["original"] == "Take 500mg every 2 hours"
        assert c0["corrected"] == "Take 200-400mg every 4-6 hours"
        assert c0["reason"] == "Exceeded safe frequency"

    def test_to_dict_retrieval_results_serialization(self):
        trace = self._make_full_trace()
        d = trace.to_dict()
        assert isinstance(d["retrieval_results"], list)
        r0 = d["retrieval_results"][0]
        assert r0["source"] == "PubMed:PMC12345"
        assert r0["relevance_score"] == 0.95

    def test_to_dict_reasoning_trace(self):
        trace = self._make_full_trace()
        d = trace.to_dict()
        assert d["reasoning_trace"] == trace.reasoning_trace

    def test_to_dict_empty_defaults(self):
        trace = AgentTrace(final_answer="Minimal.")
        d = trace.to_dict()
        assert d["final_answer"] == "Minimal."
        assert d["tool_calls"] == []
        assert d["reasoning_trace"] == []
        assert d["corrections"] == []
        assert d["retrieval_results"] == []

    def test_to_dict_returns_plain_dict(self):
        """to_dict should return plain dicts, not dataclass instances."""
        trace = self._make_full_trace()
        d = trace.to_dict()
        # Nested items should be plain dicts, not dataclass objects
        for tc in d["tool_calls"]:
            assert isinstance(tc, dict)
        for c in d["corrections"]:
            assert isinstance(c, dict)
        for r in d["retrieval_results"]:
            assert isinstance(r, dict)


# ---------------------------------------------------------------------------
# compute_unified_score
# ---------------------------------------------------------------------------

class TestComputeUnifiedScore:
    """Tests for the weighted scoring function."""

    def test_perfect_scores(self):
        dims = {k: 1.0 for k in DIMENSION_WEIGHTS}
        score = compute_unified_score(dims)
        assert math.isclose(score, 1.0, rel_tol=1e-9)

    def test_zero_scores(self):
        dims = {k: 0.0 for k in DIMENSION_WEIGHTS}
        score = compute_unified_score(dims)
        assert math.isclose(score, 0.0, abs_tol=1e-9)

    def test_known_weighted_sum(self):
        dims = {
            "answer_quality": 0.8,
            "tool_selection": 0.6,
            "retrieval_quality": 0.7,
            "reasoning_trace": 0.9,
            "self_correction": 0.5,
        }
        expected = (
            0.8 * 0.35
            + 0.6 * 0.15
            + 0.7 * 0.20
            + 0.9 * 0.20
            + 0.5 * 0.10
        )
        score = compute_unified_score(dims)
        assert math.isclose(score, expected, rel_tol=1e-9)

    def test_single_dimension_nonzero(self):
        dims = {k: 0.0 for k in DIMENSION_WEIGHTS}
        dims["answer_quality"] = 1.0
        score = compute_unified_score(dims)
        assert math.isclose(score, 0.35, rel_tol=1e-9)

    def test_missing_dimension_raises(self):
        incomplete = {"answer_quality": 1.0, "tool_selection": 1.0}
        with pytest.raises(ValueError):
            compute_unified_score(incomplete)

    def test_extra_dimension_raises(self):
        dims = {k: 1.0 for k in DIMENSION_WEIGHTS}
        dims["bogus_dimension"] = 0.5
        with pytest.raises(ValueError):
            compute_unified_score(dims)

    def test_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert math.isclose(total, 1.0, rel_tol=1e-9)
