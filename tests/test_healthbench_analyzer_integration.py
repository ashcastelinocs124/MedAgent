"""Test that pattern analyzer can be invoked on empty results."""
import json
import pytest
from pathlib import Path
from src.evaluation.pattern_analyzer import PatternAnalyzer


def test_analyze_empty_results(tmp_path):
    """Analyzer handles empty results gracefully."""
    allresults = {
        "metadata": {"example_level_metadata": []},
        "score": 0.5,
        "metrics": {"overall_score": 0.5},
    }
    results_path = tmp_path / "allresults.json"
    results_path.write_text(json.dumps(allresults))

    analyzer = PatternAnalyzer(
        results_path=results_path,
        tracker_path=tmp_path / "tracker.json",
        learnings_path=tmp_path / "learnings.md",
    )
    failures = analyzer.extract_failures()
    assert failures == []


def test_analyze_extracts_correct_failures(tmp_path):
    """Analyzer extracts only failed positive-point rubric items."""
    allresults = {
        "metadata": {
            "example_level_metadata": [
                {
                    "prompt_id": "p1",
                    "prompt": [{"role": "user", "content": "test query"}],
                    "completion": [{"role": "assistant", "content": "test response"}],
                    "score": 0.5,
                    "rubric_items": [
                        {"criterion": "good", "points": 1.0, "tags": [], "criteria_met": True, "explanation": "ok"},
                        {"criterion": "bad", "points": 1.0, "tags": [], "criteria_met": False, "explanation": "missed"},
                        {"criterion": "negative", "points": -1.0, "tags": [], "criteria_met": False, "explanation": "n/a"},
                    ],
                }
            ]
        }
    }
    results_path = tmp_path / "allresults.json"
    results_path.write_text(json.dumps(allresults))

    analyzer = PatternAnalyzer(
        results_path=results_path,
        tracker_path=tmp_path / "tracker.json",
        learnings_path=tmp_path / "learnings.md",
    )
    failures = analyzer.extract_failures()
    assert len(failures) == 1
    assert failures[0]["criterion"] == "bad"
