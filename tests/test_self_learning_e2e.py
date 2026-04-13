"""End-to-end tests for both self-learning systems."""
import json
import pytest
from pathlib import Path

from src.evaluation.pattern_tracker import PatternTracker
from src.evaluation.pattern_analyzer import PatternAnalyzer
from src.personalization.user_memory import UserMemoryStore


class TestGeneralSelfLearning:
    """Test the full general learning loop: failures -> tags -> graduation."""

    def test_full_loop_graduation(self, tmp_path):
        """5 similar failures graduate into a learning."""
        tracker = PatternTracker(storage_path=tmp_path / "tracker.json")
        learnings = tmp_path / "learnings.md"
        learnings.write_text("# Learnings\n", encoding="utf-8")

        for i in range(5):
            tracker.add(
                "missing_dosage_information",
                f"prompt_{i:03d}",
                f"Response failed to include dosage guidelines (example {i})",
            )

        ready = tracker.get_ready_to_graduate()
        assert "missing_dosage_information" in ready
        assert ready["missing_dosage_information"]["count"] == 5

        tracker.mark_graduated("missing_dosage_information")
        assert tracker.get("missing_dosage_information")["graduated"] is True
        assert tracker.get_ready_to_graduate() == {}

    def test_below_threshold_does_not_graduate(self, tmp_path):
        """4 occurrences should not trigger graduation."""
        tracker = PatternTracker(storage_path=tmp_path / "tracker.json")
        for i in range(4):
            tracker.add("partial_pattern", f"p_{i}", f"summary_{i}")
        assert tracker.get_ready_to_graduate() == {}

    def test_staleness_detection(self, tmp_path):
        """Graduated pattern becomes stale after 20 runs without seeing it."""
        tracker = PatternTracker(storage_path=tmp_path / "tracker.json")
        for i in range(5):
            tracker.add("old_pattern", f"p_{i}", f"s_{i}")
        tracker.mark_graduated("old_pattern")
        tracker.update_last_relevant("old_pattern", "eval_run_001")

        assert tracker.get_stale(current_run_number=10, stale_threshold=20) == []
        assert "old_pattern" in tracker.get_stale(current_run_number=21, stale_threshold=20)

    def test_extract_failures_filters_correctly(self, tmp_path):
        """Only failed positive-point rubric items are extracted."""
        data = {
            "metadata": {
                "example_level_metadata": [
                    {
                        "prompt_id": "test_1",
                        "prompt": [{"role": "user", "content": "test"}],
                        "completion": [{"role": "assistant", "content": "resp"}],
                        "score": 0.5,
                        "rubric_items": [
                            {"criterion": "passed", "points": 1.0, "tags": [], "criteria_met": True, "explanation": "ok"},
                            {"criterion": "failed_positive", "points": 1.0, "tags": [], "criteria_met": False, "explanation": "missed"},
                            {"criterion": "failed_negative", "points": -0.5, "tags": [], "criteria_met": False, "explanation": "bad but negative"},
                        ],
                    }
                ]
            }
        }
        results_path = tmp_path / "results.json"
        results_path.write_text(json.dumps(data))

        analyzer = PatternAnalyzer(
            results_path=results_path,
            tracker_path=tmp_path / "tracker.json",
        )
        failures = analyzer.extract_failures()
        assert len(failures) == 1
        assert failures[0]["criterion"] == "failed_positive"


class TestSpecificUserMemory:
    """Test the full user memory loop: extraction -> storage -> graduation."""

    def test_full_graduation_loop(self, tmp_path):
        """User fact mentioned 5 times graduates to permanent memory."""
        store = UserMemoryStore(base_dir=tmp_path / "users")
        user_id = "e2e_user"

        for _ in range(4):
            store.add_fact(user_id, "Follows ketogenic diet", "hormones_metabolism_nutrition")

        facts = store.get_facts(user_id)
        assert len(facts) == 1
        assert facts[0]["mentions"] == 4
        assert store.get_graduated(user_id) == []

        store.add_fact(user_id, "Follows ketogenic diet", "hormones_metabolism_nutrition")

        assert store.get_facts(user_id) == []
        graduated = store.get_graduated(user_id)
        assert len(graduated) == 1
        assert graduated[0]["fact"] == "Follows ketogenic diet"

    def test_novel_filtering_against_profile(self, tmp_path):
        """Only novel facts (not in profile) are surfaced."""
        store = UserMemoryStore(base_dir=tmp_path / "users")
        store.add_fact("filter_user", "Has diabetes", "hormones_metabolism_nutrition")
        store.add_fact("filter_user", "Father had stroke", "nervous_system_brain")

        novel = store.get_novel_facts(
            "filter_user",
            profile_conditions=["Diabetes"],
            profile_medications=[],
        )
        assert len(novel) == 1
        assert "stroke" in novel[0]["fact"].lower()

    def test_contradictory_update_resets_mentions(self, tmp_path):
        """Updating a fact resets its mention count."""
        store = UserMemoryStore(base_dir=tmp_path / "users")
        store.add_fact("u1", "Takes metformin", "hormones_metabolism_nutrition")
        store.add_fact("u1", "Takes metformin", "hormones_metabolism_nutrition")
        store.add_fact("u1", "Takes metformin", "hormones_metabolism_nutrition")
        assert store.get_facts("u1")[0]["mentions"] == 3

        store.update_fact("u1", "Takes metformin", "Stopped taking metformin", "hormones_metabolism_nutrition")
        facts = store.get_facts("u1")
        assert facts[0]["mentions"] == 1
        assert facts[0]["fact"] == "Stopped taking metformin"

    def test_eviction_at_capacity(self, tmp_path):
        """At max capacity (20), lowest-mention oldest fact is evicted."""
        store = UserMemoryStore(base_dir=tmp_path / "users")
        for i in range(20):
            store.add_fact("cap_user", f"Fact {i}", "general")

        # Boost one fact's mentions so it's not evicted
        store.add_fact("cap_user", "Fact 5", "general")

        # Add one more to trigger eviction
        store.add_fact("cap_user", "Fact 20", "general")

        facts = store.get_facts("cap_user")
        assert len(facts) == 20
        fact_texts = [f["fact"] for f in facts]
        assert "Fact 20" in fact_texts
        # Fact 5 should survive (mentions=2)
        assert "Fact 5" in fact_texts

    def test_persistence_across_instances(self, tmp_path):
        """Memory persists when store is recreated."""
        base = tmp_path / "users"
        s1 = UserMemoryStore(base_dir=base)
        s1.add_fact("persist_user", "Has asthma", "respiratory")

        s2 = UserMemoryStore(base_dir=base)
        facts = s2.get_facts("persist_user")
        assert len(facts) == 1
        assert facts[0]["fact"] == "Has asthma"
