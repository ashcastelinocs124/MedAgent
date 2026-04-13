"""Tests for agentic_medbench grader agents.

Tests verify structure and behaviour WITHOUT making API calls.
Grader model interactions are mocked wherever needed.
"""

from __future__ import annotations

import json
from inspect import signature
from unittest.mock import MagicMock

import pytest

from simple_evals.agentic_medbench.graders import (
    AnswerGrader,
    BaseGrader,
    ReasoningGrader,
    RetrievalGrader,
    SelfCorrectionGrader,
    ToolGrader,
    _parse_grader_response,
    grade_all_dimensions,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_agent_trace() -> dict:
    """Minimal agent trace dict with all expected keys populated."""
    return {
        "final_answer": "Take ibuprofen 200mg every 6 hours with food.",
        "tool_calls": [
            {
                "tool_name": "pubmed_search",
                "arguments": {"query": "ibuprofen dosage"},
                "result": "PMID 123: recommended dose is 200-400mg",
                "timestamp": 1.0,
            },
            {
                "tool_name": "drug_interaction_db",
                "arguments": {"drug_name": "ibuprofen"},
                "result": "No major interactions found",
                "timestamp": 2.0,
            },
        ],
        "reasoning_trace": [
            "User is asking about ibuprofen dosage.",
            "Need to check standard dosing guidelines.",
            "PubMed confirms 200-400mg every 4-6 hours.",
            "Should mention taking with food to avoid GI issues.",
        ],
        "corrections": [
            {
                "original": "Take 400mg every 4 hours",
                "corrected": "Take 200mg every 6 hours",
                "reason": "Lower dose is safer for OTC recommendation",
            },
        ],
        "retrieval_results": [
            {
                "source": "PubMed",
                "content": "Ibuprofen 200-400mg q4-6h",
                "relevance_score": 0.95,
            },
            {
                "source": "FDA Label",
                "content": "Take with food or milk",
                "relevance_score": 0.88,
            },
        ],
    }


@pytest.fixture()
def sample_test_case() -> dict:
    """Minimal test case dict with all rubric/checkpoint fields."""
    return {
        "question": "What is the recommended OTC dose of ibuprofen?",
        "answer_rubric": {
            "positive_points": [
                {"criterion": "Mentions 200-400mg dose range", "points": 2},
                {"criterion": "Mentions frequency (every 4-6 hours)", "points": 2},
                {"criterion": "Mentions taking with food", "points": 1},
            ],
            "negative_points": [
                {"criterion": "Recommends more than 1200mg/day without MD", "points": -2},
                {"criterion": "Fails to mention any warnings", "points": -1},
            ],
            "total_possible_points": 5,
        },
        "required_tools": ["pubmed_search", "drug_interaction_db"],
        "expected_retrieval_topics": [
            "ibuprofen dosage guidelines",
            "ibuprofen food interactions",
        ],
        "reasoning_checkpoints": [
            "Identifies query as drug dosage question",
            "Checks authoritative source for dosing",
            "Considers safety / side effects",
        ],
    }


# ---------------------------------------------------------------------------
# _parse_grader_response
# ---------------------------------------------------------------------------


class TestParseGraderResponse:
    """Tests for the JSON-parsing helper."""

    def test_valid_json(self):
        text = '{"score": 0.85, "explanation": "Good answer"}'
        result = _parse_grader_response(text)
        assert result["score"] == 0.85
        assert result["explanation"] == "Good answer"

    def test_markdown_fenced_json(self):
        text = 'Here is my evaluation:\n```json\n{"score": 0.7, "explanation": "Decent"}\n```'
        result = _parse_grader_response(text)
        assert result["score"] == 0.7
        assert result["explanation"] == "Decent"

    def test_markdown_fenced_no_lang(self):
        text = '```\n{"score": 0.5, "explanation": "Average"}\n```'
        result = _parse_grader_response(text)
        assert result["score"] == 0.5

    def test_invalid_input_returns_zero(self):
        result = _parse_grader_response("This is not JSON at all!")
        assert result["score"] == 0.0
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0

    def test_empty_string_returns_zero(self):
        result = _parse_grader_response("")
        assert result["score"] == 0.0

    def test_json_with_extra_fields_preserved(self):
        text = '{"score": 0.9, "explanation": "Great", "required_tools_used": ["pubmed_search"]}'
        result = _parse_grader_response(text)
        assert result["score"] == 0.9
        assert result["required_tools_used"] == ["pubmed_search"]

    def test_json_missing_score_returns_zero(self):
        text = '{"explanation": "No score field"}'
        result = _parse_grader_response(text)
        assert result["score"] == 0.0

    def test_json_embedded_in_prose(self):
        text = 'I evaluated the answer carefully.\n{"score": 0.6, "explanation": "Partial"}\nThat is my assessment.'
        result = _parse_grader_response(text)
        assert result["score"] == 0.6


# ---------------------------------------------------------------------------
# System prompts contain relevant keywords
# ---------------------------------------------------------------------------


class TestGraderSystemPrompts:
    """Each grader's system_prompt must contain keywords relevant to its dimension."""

    def test_answer_grader_prompt(self):
        grader = AnswerGrader()
        prompt = grader.system_prompt.lower()
        assert "rubric" in prompt or "answer" in prompt
        assert "score" in prompt

    def test_tool_grader_prompt(self):
        grader = ToolGrader()
        prompt = grader.system_prompt.lower()
        assert "tool" in prompt
        assert "score" in prompt

    def test_retrieval_grader_prompt(self):
        grader = RetrievalGrader()
        prompt = grader.system_prompt.lower()
        assert "retrieval" in prompt or "relevance" in prompt
        assert "score" in prompt

    def test_reasoning_grader_prompt(self):
        grader = ReasoningGrader()
        prompt = grader.system_prompt.lower()
        assert "reasoning" in prompt or "checkpoint" in prompt
        assert "score" in prompt

    def test_self_correction_grader_prompt(self):
        grader = SelfCorrectionGrader()
        prompt = grader.system_prompt.lower()
        assert "correction" in prompt or "error" in prompt
        assert "score" in prompt


# ---------------------------------------------------------------------------
# build_user_prompt returns non-empty strings
# ---------------------------------------------------------------------------


class TestBuildUserPrompt:
    """Each grader's build_user_prompt must return a non-empty string."""

    def test_answer_grader(self, sample_agent_trace, sample_test_case):
        grader = AnswerGrader()
        prompt = grader.build_user_prompt(sample_agent_trace, sample_test_case)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include the final answer
        assert "ibuprofen" in prompt.lower()

    def test_tool_grader(self, sample_agent_trace, sample_test_case):
        grader = ToolGrader()
        prompt = grader.build_user_prompt(sample_agent_trace, sample_test_case)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include tool call info
        assert "pubmed_search" in prompt

    def test_retrieval_grader(self, sample_agent_trace, sample_test_case):
        grader = RetrievalGrader()
        prompt = grader.build_user_prompt(sample_agent_trace, sample_test_case)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include retrieval topics
        assert "ibuprofen" in prompt.lower()

    def test_reasoning_grader(self, sample_agent_trace, sample_test_case):
        grader = ReasoningGrader()
        prompt = grader.build_user_prompt(sample_agent_trace, sample_test_case)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include reasoning checkpoints
        assert "checkpoint" in prompt.lower() or "reasoning" in prompt.lower()

    def test_self_correction_grader(self, sample_agent_trace, sample_test_case):
        grader = SelfCorrectionGrader()
        prompt = grader.build_user_prompt(sample_agent_trace, sample_test_case)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include correction info
        assert "corrected" in prompt.lower() or "correction" in prompt.lower() or "original" in prompt.lower()


# ---------------------------------------------------------------------------
# grade_all_dimensions function signature and structure
# ---------------------------------------------------------------------------


class TestGradeAllDimensions:
    """Verify grade_all_dimensions has the correct signature and key structure."""

    def test_function_signature(self):
        sig = signature(grade_all_dimensions)
        param_names = list(sig.parameters.keys())
        assert "agent_trace" in param_names
        assert "test_case" in param_names
        assert "grader_model" in param_names

    def test_returns_all_five_dimension_keys(
        self, sample_agent_trace, sample_test_case
    ):
        """Mock the grader model so no API call is made."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.response_text = json.dumps(
            {"score": 0.8, "explanation": "Mocked evaluation"}
        )
        mock_model.return_value = mock_response

        result = grade_all_dimensions(
            sample_agent_trace, sample_test_case, mock_model
        )

        expected_keys = {
            "answer_quality",
            "tool_selection",
            "retrieval_quality",
            "reasoning_trace",
            "self_correction",
        }
        assert set(result.keys()) == expected_keys

    def test_each_dimension_has_score_and_explanation(
        self, sample_agent_trace, sample_test_case
    ):
        """Each dimension result must contain at least score and explanation."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.response_text = json.dumps(
            {"score": 0.75, "explanation": "Mock"}
        )
        mock_model.return_value = mock_response

        result = grade_all_dimensions(
            sample_agent_trace, sample_test_case, mock_model
        )

        for dim_name, dim_result in result.items():
            assert "score" in dim_result, f"{dim_name} missing 'score'"
            assert "explanation" in dim_result, f"{dim_name} missing 'explanation'"
            assert 0.0 <= dim_result["score"] <= 1.0, (
                f"{dim_name} score {dim_result['score']} out of [0,1]"
            )


# ---------------------------------------------------------------------------
# BaseGrader.grade — retry and clip behaviour (via a concrete subclass)
# ---------------------------------------------------------------------------


class TestBaseGraderGradeMethod:
    """Test the grade() method's retry and score-clipping logic."""

    def test_score_clipped_to_0_1(self, sample_agent_trace, sample_test_case):
        """Scores above 1.0 or below 0.0 must be clipped."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.response_text = json.dumps(
            {"score": 1.5, "explanation": "Over max"}
        )
        mock_model.return_value = mock_response

        grader = AnswerGrader()
        result = grader.grade(sample_agent_trace, sample_test_case, mock_model)
        assert result["score"] <= 1.0

    def test_negative_score_clipped(self, sample_agent_trace, sample_test_case):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.response_text = json.dumps(
            {"score": -0.3, "explanation": "Negative"}
        )
        mock_model.return_value = mock_response

        grader = AnswerGrader()
        result = grader.grade(sample_agent_trace, sample_test_case, mock_model)
        assert result["score"] >= 0.0

    def test_retries_on_parse_failure(self, sample_agent_trace, sample_test_case):
        """If first attempts return unparseable text, grade() should retry."""
        mock_model = MagicMock()
        bad_response = MagicMock()
        bad_response.response_text = "not json at all"
        good_response = MagicMock()
        good_response.response_text = json.dumps(
            {"score": 0.9, "explanation": "Good"}
        )
        # First two calls fail, third succeeds
        mock_model.side_effect = [bad_response, bad_response, good_response]

        grader = AnswerGrader()
        result = grader.grade(sample_agent_trace, sample_test_case, mock_model)
        assert result["score"] == 0.9

    def test_all_retries_exhausted_returns_zero(
        self, sample_agent_trace, sample_test_case
    ):
        """If all retries produce unparseable output, return score 0.0."""
        mock_model = MagicMock()
        bad_response = MagicMock()
        bad_response.response_text = "garbage"
        mock_model.return_value = bad_response

        grader = AnswerGrader()
        result = grader.grade(sample_agent_trace, sample_test_case, mock_model)
        assert result["score"] == 0.0
