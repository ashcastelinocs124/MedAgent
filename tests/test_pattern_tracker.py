"""Tests for pattern tracker -- tag storage, counting, dedup, graduation."""
import pytest
from src.evaluation.pattern_tracker import PatternTracker


@pytest.fixture
def tracker(tmp_path):
    return PatternTracker(storage_path=tmp_path / "pattern_tracker.json")


def test_add_new_tag(tracker):
    tracker.add("missing_drug_warning", example_id="ex_001", example_summary="Failed to warn about drug interaction")
    entry = tracker.get("missing_drug_warning")
    assert entry is not None
    assert entry["count"] == 1
    assert entry["graduated"] is False
    assert len(entry["examples"]) == 1


def test_increment_existing_tag(tracker):
    tracker.add("missing_drug_warning", example_id="ex_001", example_summary="summary1")
    tracker.add("missing_drug_warning", example_id="ex_002", example_summary="summary2")
    entry = tracker.get("missing_drug_warning")
    assert entry["count"] == 2
    assert len(entry["examples"]) == 2


def test_graduation_at_threshold(tracker):
    for i in range(5):
        tracker.add("uncited_claim", example_id=f"ex_{i}", example_summary=f"summary_{i}")
    entry = tracker.get("uncited_claim")
    assert entry["count"] == 5
    assert entry["ready_to_graduate"] is True


def test_no_graduation_below_threshold(tracker):
    for i in range(4):
        tracker.add("uncited_claim", example_id=f"ex_{i}", example_summary=f"summary_{i}")
    entry = tracker.get("uncited_claim")
    assert entry["ready_to_graduate"] is False


def test_mark_graduated(tracker):
    for i in range(5):
        tracker.add("uncited_claim", example_id=f"ex_{i}", example_summary=f"summary_{i}")
    tracker.mark_graduated("uncited_claim")
    entry = tracker.get("uncited_claim")
    assert entry["graduated"] is True


def test_persistence(tmp_path):
    path = tmp_path / "tracker.json"
    t1 = PatternTracker(storage_path=path)
    t1.add("tag_a", "ex1", "s1")
    t1.save()
    t2 = PatternTracker(storage_path=path)
    assert t2.get("tag_a")["count"] == 1


def test_get_ungraduated_ready(tracker):
    for i in range(5):
        tracker.add("pattern_a", f"ex_{i}", f"s_{i}")
    for i in range(3):
        tracker.add("pattern_b", f"ex_{i}", f"s_{i}")
    ready = tracker.get_ready_to_graduate()
    assert "pattern_a" in ready
    assert "pattern_b" not in ready


def test_update_last_relevant(tracker):
    tracker.add("tag_a", "ex1", "s1")
    tracker.update_last_relevant("tag_a", run_id="eval_run_042")
    entry = tracker.get("tag_a")
    assert entry["last_relevant"] == "eval_run_042"


def test_get_stale(tracker):
    for i in range(5):
        tracker.add("old_pattern", f"ex_{i}", f"s_{i}")
    tracker.mark_graduated("old_pattern")
    tracker.update_last_relevant("old_pattern", run_id="eval_run_001")
    stale = tracker.get_stale(current_run_number=21, stale_threshold=20)
    assert "old_pattern" in stale
