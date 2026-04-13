"""Tests for the AgenticMedBenchEval runner.

Tests verify structure and behaviour WITHOUT making API calls.
All sampler and grader interactions are mocked.
"""

from __future__ import annotations

import json
from inspect import signature
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from simple_evals.agentic_medbench.eval import (
    AgenticMedBenchEval,
    _aggregate_results,
)
from simple_evals.agentic_medbench.types import DIMENSION_WEIGHTS
from simple_evals.types import Eval, EvalResult, SingleEvalResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_grader_model() -> MagicMock:
    """A mock grader model that returns valid grading JSON for all dimensions."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.response_text = json.dumps(
        {"score": 0.8, "explanation": "Mocked evaluation"}
    )
    mock.return_value = mock_response
    return mock


@pytest.fixture()
def sample_test_cases() -> list[dict]:
    """Minimal test cases for the eval runner."""
    return [
        {
            "conversation": [
                {"role": "user", "content": "What is the OTC dose for ibuprofen?"}
            ],
            "answer_rubric": {
                "positive_points": [
                    {"criterion": "Mentions 200-400mg", "points": 2},
                ],
                "negative_points": [],
                "total_possible_points": 2,
            },
            "required_tools": ["pubmed_search"],
            "expected_retrieval_topics": ["ibuprofen dosage"],
            "reasoning_checkpoints": ["Identifies drug dosage question"],
            "tags": ["pharmacology"],
            "difficulty": "easy",
        },
        {
            "conversation": [
                {"role": "user", "content": "Is metformin safe during pregnancy?"}
            ],
            "answer_rubric": {
                "positive_points": [
                    {"criterion": "Mentions pregnancy risk", "points": 3},
                ],
                "negative_points": [],
                "total_possible_points": 3,
            },
            "required_tools": ["pubmed_search", "drug_interaction_db"],
            "expected_retrieval_topics": ["metformin pregnancy safety"],
            "reasoning_checkpoints": ["Considers teratogenicity"],
            "tags": ["pharmacology", "obstetrics"],
            "difficulty": "hard",
        },
    ]


def _make_single_eval_result(
    score: float,
    tags: list[str] | None = None,
    difficulty: str = "easy",
) -> SingleEvalResult:
    """Helper to construct a SingleEvalResult with standard metrics."""
    tags = tags or []
    metrics: dict[str, float] = {
        "overall_score": score,
        "answer_quality": score,
        "tool_selection": score,
        "retrieval_quality": score,
        "reasoning_trace": score,
        "self_correction": score,
    }
    for tag in tags:
        metrics[f"tag:{tag}"] = score
    metrics[f"difficulty:{difficulty}"] = score
    return SingleEvalResult(
        score=score,
        metrics=metrics,
        html="<p>mock</p>",
        convo=[{"role": "user", "content": "test"}],
    )


# ---------------------------------------------------------------------------
# AgenticMedBenchEval class existence and interface
# ---------------------------------------------------------------------------


class TestAgenticMedBenchEvalClass:
    """Verify the eval class exists, subclasses Eval, and is callable."""

    def test_class_exists(self):
        assert AgenticMedBenchEval is not None

    def test_subclasses_eval(self):
        assert issubclass(AgenticMedBenchEval, Eval)

    def test_is_callable(self, mock_grader_model, sample_test_cases):
        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=sample_test_cases,
        )
        assert callable(eval_instance)

    def test_constructor_signature(self):
        sig = signature(AgenticMedBenchEval.__init__)
        param_names = list(sig.parameters.keys())
        assert "grader_model" in param_names
        assert "test_cases" in param_names
        assert "test_cases_path" in param_names
        assert "num_examples" in param_names
        assert "n_threads" in param_names

    def test_constructor_with_test_cases(self, mock_grader_model, sample_test_cases):
        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=sample_test_cases,
        )
        assert len(eval_instance.examples) == 2

    def test_constructor_num_examples_sampling(
        self, mock_grader_model, sample_test_cases
    ):
        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=sample_test_cases,
            num_examples=1,
        )
        assert len(eval_instance.examples) == 1

    def test_constructor_num_examples_larger_than_dataset(
        self, mock_grader_model, sample_test_cases
    ):
        """If num_examples >= len(examples), all examples are used."""
        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=sample_test_cases,
            num_examples=100,
        )
        assert len(eval_instance.examples) == 2


# ---------------------------------------------------------------------------
# _aggregate_results
# ---------------------------------------------------------------------------


class TestAggregateResults:
    """Verify _aggregate_results works with mock SingleEvalResults."""

    def test_returns_eval_result(self):
        results = [_make_single_eval_result(0.8), _make_single_eval_result(0.6)]
        agg = _aggregate_results(results)
        assert isinstance(agg, EvalResult)

    def test_score_is_clipped_mean(self):
        results = [_make_single_eval_result(0.8), _make_single_eval_result(0.6)]
        agg = _aggregate_results(results)
        assert agg.score is not None
        assert 0.0 <= agg.score <= 1.0
        assert abs(agg.score - 0.7) < 1e-6

    def test_metrics_contain_bootstrap_std_and_n_samples(self):
        results = [_make_single_eval_result(0.8), _make_single_eval_result(0.6)]
        agg = _aggregate_results(results)
        assert agg.metrics is not None
        # Check that n_samples and bootstrap_std exist for overall_score
        assert "overall_score:n_samples" in agg.metrics
        assert "overall_score:bootstrap_std" in agg.metrics
        assert agg.metrics["overall_score:n_samples"] == 2

    def test_htmls_collected(self):
        results = [_make_single_eval_result(0.8), _make_single_eval_result(0.6)]
        agg = _aggregate_results(results)
        assert len(agg.htmls) == 2

    def test_convos_collected(self):
        results = [_make_single_eval_result(0.8), _make_single_eval_result(0.6)]
        agg = _aggregate_results(results)
        assert len(agg.convos) == 2

    def test_single_result_aggregation(self):
        results = [_make_single_eval_result(0.9)]
        agg = _aggregate_results(results)
        assert agg.score is not None
        assert abs(agg.score - 0.9) < 1e-6

    def test_all_perfect_scores(self):
        results = [_make_single_eval_result(1.0) for _ in range(5)]
        agg = _aggregate_results(results)
        assert agg.score is not None
        assert abs(agg.score - 1.0) < 1e-6

    def test_all_zero_scores(self):
        results = [_make_single_eval_result(0.0) for _ in range(5)]
        agg = _aggregate_results(results)
        assert agg.score is not None
        assert abs(agg.score - 0.0) < 1e-6

    def test_high_scores_clipped_to_one(self):
        """Scores above 1.0 in metrics should be clipped during aggregation."""
        r = SingleEvalResult(
            score=1.5,
            metrics={"overall_score": 1.5},
            html="<p>mock</p>",
            convo=[],
        )
        agg = _aggregate_results([r])
        assert agg.score is not None
        assert agg.score <= 1.0


# ---------------------------------------------------------------------------
# Unified score clipping
# ---------------------------------------------------------------------------


class TestUnifiedScoreClipping:
    """Verify that the unified score is clipped to [0, 1] in the eval runner."""

    @patch("simple_evals.agentic_medbench.eval.grade_all_dimensions")
    def test_score_clipped_to_zero_one(
        self, mock_grade_all, mock_grader_model, sample_test_cases
    ):
        """Even if dimension scores produce a weighted sum > 1.0, clip to [0,1]."""
        # Return scores that would sum > 1.0 with weights
        mock_grade_all.return_value = {
            dim: {"score": 1.5, "explanation": "over max"}
            for dim in DIMENSION_WEIGHTS
        }

        mock_sampler = MagicMock()
        mock_sampler_response = MagicMock()
        mock_sampler_response.response_text = "Mocked agent response"
        mock_sampler_response.response_metadata = {}
        mock_sampler_response.actual_queried_message_list = sample_test_cases[0][
            "conversation"
        ]
        mock_sampler.return_value = mock_sampler_response

        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=[sample_test_cases[0]],
            n_threads=1,
        )
        result = eval_instance(mock_sampler)
        assert result.score is not None
        assert result.score <= 1.0

    @patch("simple_evals.agentic_medbench.eval.grade_all_dimensions")
    def test_negative_score_clipped_to_zero(
        self, mock_grade_all, mock_grader_model, sample_test_cases
    ):
        """If dimension scores are negative, the unified score should be >= 0."""
        mock_grade_all.return_value = {
            dim: {"score": -0.5, "explanation": "negative"}
            for dim in DIMENSION_WEIGHTS
        }

        mock_sampler = MagicMock()
        mock_sampler_response = MagicMock()
        mock_sampler_response.response_text = "Mocked agent response"
        mock_sampler_response.response_metadata = {}
        mock_sampler_response.actual_queried_message_list = sample_test_cases[0][
            "conversation"
        ]
        mock_sampler.return_value = mock_sampler_response

        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=[sample_test_cases[0]],
            n_threads=1,
        )
        result = eval_instance(mock_sampler)
        assert result.score is not None
        assert result.score >= 0.0

    @patch("simple_evals.agentic_medbench.eval.grade_all_dimensions")
    def test_normal_score_within_bounds(
        self, mock_grade_all, mock_grader_model, sample_test_cases
    ):
        """Normal dimension scores produce a unified score within [0, 1]."""
        mock_grade_all.return_value = {
            dim: {"score": 0.8, "explanation": "good"}
            for dim in DIMENSION_WEIGHTS
        }

        mock_sampler = MagicMock()
        mock_sampler_response = MagicMock()
        mock_sampler_response.response_text = "Mocked agent response"
        mock_sampler_response.response_metadata = {}
        mock_sampler_response.actual_queried_message_list = sample_test_cases[0][
            "conversation"
        ]
        mock_sampler.return_value = mock_sampler_response

        eval_instance = AgenticMedBenchEval(
            grader_model=mock_grader_model,
            test_cases=[sample_test_cases[0]],
            n_threads=1,
        )
        result = eval_instance(mock_sampler)
        assert result.score is not None
        assert 0.0 <= result.score <= 1.0
        # All dims have score 0.8, weights sum to 1.0, so unified = 0.8
        assert abs(result.score - 0.8) < 1e-6
