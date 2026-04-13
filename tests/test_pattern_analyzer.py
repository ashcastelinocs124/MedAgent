"""Tests for pattern analyzer -- LLM tagging, dedup, graduation."""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.evaluation.pattern_analyzer import PatternAnalyzer


@pytest.fixture
def results_file(tmp_path):
    data = {
        "metadata": {
            "example_level_metadata": [
                {
                    "prompt_id": "p001",
                    "prompt": [{"role": "user", "content": "What are side effects of metformin?"}],
                    "completion": [{"role": "assistant", "content": "Metformin is a diabetes drug."}],
                    "score": 0.3,
                    "rubric_items": [
                        {
                            "criterion": "Mentions common GI side effects",
                            "points": 1.0,
                            "tags": ["completeness"],
                            "criteria_met": False,
                            "explanation": "Response did not mention GI side effects",
                        },
                        {
                            "criterion": "Provides accurate information",
                            "points": 1.0,
                            "tags": ["accuracy"],
                            "criteria_met": True,
                            "explanation": "Information was accurate",
                        },
                    ],
                },
                {
                    "prompt_id": "p002",
                    "prompt": [{"role": "user", "content": "Can I take ibuprofen with warfarin?"}],
                    "completion": [{"role": "assistant", "content": "Ibuprofen is a pain reliever."}],
                    "score": 0.2,
                    "rubric_items": [
                        {
                            "criterion": "Warns about bleeding risk with concurrent use",
                            "points": 2.0,
                            "tags": ["safety"],
                            "criteria_met": False,
                            "explanation": "Did not warn about drug interaction",
                        },
                    ],
                },
            ]
        }
    }
    path = tmp_path / "allresults.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def analyzer(tmp_path, results_file):
    tracker_path = tmp_path / "pattern_tracker.json"
    return PatternAnalyzer(
        results_path=results_file,
        tracker_path=tracker_path,
    )


def test_extract_failures(analyzer):
    failures = analyzer.extract_failures()
    assert len(failures) == 2
    assert failures[0]["prompt_id"] == "p001"
    assert failures[1]["prompt_id"] == "p002"


async def test_tag_failure_calls_llm(analyzer):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "missing_side_effect_listing"

    with patch("src.evaluation.pattern_analyzer.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_response
        failure = analyzer.extract_failures()[0]
        tag = await analyzer.tag_failure(failure)
        assert tag == "missing_side_effect_listing"


async def test_check_existing_tags_merges_similar(analyzer):
    analyzer._tracker.add("missing_drug_interaction_warning", "ex1", "s1")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "missing_drug_interaction_warning"

    with patch("src.evaluation.pattern_analyzer.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_response
        merged = await analyzer.check_existing_tags("no_drug_interaction_alert")
        assert merged == "missing_drug_interaction_warning"


async def test_graduate_pattern_writes_learning(analyzer, tmp_path):
    learnings_path = tmp_path / "learnings.md"
    learnings_path.write_text("# Learnings\n", encoding="utf-8")
    analyzer._learnings_path = learnings_path

    for i in range(5):
        analyzer._tracker.add("uncited_statistical_claim", f"ex_{i}", f"Pipeline cited statistics without source reference (example {i})")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Always cite the source when presenting statistical claims."

    with patch("src.evaluation.pattern_analyzer.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_response
        await analyzer.graduate_ready_patterns()

    content = learnings_path.read_text(encoding="utf-8")
    assert "## Self-Learning" in content
    assert "uncited_statistical_claim" in content
    assert analyzer._tracker.get("uncited_statistical_claim")["graduated"] is True
