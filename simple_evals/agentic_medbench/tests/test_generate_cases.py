"""Tests for agentic_medbench test case generator.

Tests verify prompt constants, parsing logic, and function signatures
WITHOUT making any API calls.
"""

from __future__ import annotations

import json
from inspect import signature

import pytest

from simple_evals.agentic_medbench.generate_cases import (
    AUGMENTATION_PROMPT,
    GENERATION_PROMPT,
    augment_healthbench_example,
    generate_fresh_case,
    parse_augmented_case,
)


# ---------------------------------------------------------------------------
# AUGMENTATION_PROMPT
# ---------------------------------------------------------------------------


class TestAugmentationPrompt:
    """AUGMENTATION_PROMPT must contain key instruction terms."""

    def test_contains_required_tools(self):
        assert "required_tools" in AUGMENTATION_PROMPT

    def test_contains_expected_retrieval_topics(self):
        assert "expected_retrieval_topics" in AUGMENTATION_PROMPT

    def test_contains_reasoning_checkpoints(self):
        assert "reasoning_checkpoints" in AUGMENTATION_PROMPT

    def test_contains_difficulty(self):
        assert "difficulty" in AUGMENTATION_PROMPT


# ---------------------------------------------------------------------------
# GENERATION_PROMPT
# ---------------------------------------------------------------------------


class TestGenerationPrompt:
    """GENERATION_PROMPT must contain key instruction terms."""

    def test_contains_reasoning_checkpoints(self):
        assert "reasoning_checkpoints" in GENERATION_PROMPT

    def test_contains_required_tools(self):
        assert "required_tools" in GENERATION_PROMPT

    def test_contains_answer_rubric(self):
        assert "answer_rubric" in GENERATION_PROMPT

    def test_contains_difficulty(self):
        assert "difficulty" in GENERATION_PROMPT


# ---------------------------------------------------------------------------
# parse_augmented_case
# ---------------------------------------------------------------------------


class TestParseAugmentedCase:
    """Tests for JSON parsing with various input formats."""

    def test_valid_json(self):
        raw = json.dumps({
            "required_tools": ["pubmed_search"],
            "expected_retrieval_topics": ["aspirin dosage"],
            "reasoning_checkpoints": ["Identify drug"],
            "difficulty": "standard",
        })
        result = parse_augmented_case(raw)
        assert result["required_tools"] == ["pubmed_search"]
        assert result["expected_retrieval_topics"] == ["aspirin dosage"]
        assert result["reasoning_checkpoints"] == ["Identify drug"]
        assert result["difficulty"] == "standard"

    def test_markdown_fenced_json(self):
        raw = (
            "Here is the analysis:\n"
            "```json\n"
            '{"required_tools": ["web_search"], '
            '"expected_retrieval_topics": ["diabetes management"], '
            '"reasoning_checkpoints": ["Check guidelines"], '
            '"difficulty": "hard"}\n'
            "```\n"
            "That is my output."
        )
        result = parse_augmented_case(raw)
        assert result["required_tools"] == ["web_search"]
        assert result["difficulty"] == "hard"

    def test_markdown_fenced_no_lang(self):
        raw = (
            "```\n"
            '{"required_tools": ["brain_graph"], "difficulty": "standard"}\n'
            "```"
        )
        result = parse_augmented_case(raw)
        assert result["required_tools"] == ["brain_graph"]

    def test_raises_on_invalid_input(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parse_augmented_case("This is not JSON at all and has no braces")

    def test_raises_on_empty_string(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parse_augmented_case("")

    def test_handles_extra_whitespace(self):
        raw = '   \n  {"required_tools": ["pubmed_search"], "difficulty": "standard"}  \n  '
        result = parse_augmented_case(raw)
        assert result["required_tools"] == ["pubmed_search"]


# ---------------------------------------------------------------------------
# augment_healthbench_example — function signature
# ---------------------------------------------------------------------------


class TestAugmentHealthbenchExampleSignature:
    """Verify augment_healthbench_example has the correct function signature."""

    def test_has_correct_parameters(self):
        sig = signature(augment_healthbench_example)
        param_names = list(sig.parameters.keys())
        assert "example" in param_names
        assert "augmenter_model" in param_names

    def test_parameter_count(self):
        sig = signature(augment_healthbench_example)
        assert len(sig.parameters) == 2


# ---------------------------------------------------------------------------
# generate_fresh_case — function signature
# ---------------------------------------------------------------------------


class TestGenerateFreshCaseSignature:
    """Verify generate_fresh_case has the correct function signature."""

    def test_has_correct_parameters(self):
        sig = signature(generate_fresh_case)
        param_names = list(sig.parameters.keys())
        assert "topic" in param_names
        assert "generator_model" in param_names

    def test_parameter_count(self):
        sig = signature(generate_fresh_case)
        assert len(sig.parameters) == 2
