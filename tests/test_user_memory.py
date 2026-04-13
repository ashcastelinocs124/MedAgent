"""Tests for per-user short-term memory store."""
import pytest
from pathlib import Path
from src.personalization.user_memory import UserMemoryStore


@pytest.fixture
def store(tmp_path):
    return UserMemoryStore(base_dir=tmp_path / "users")


def test_add_fact(store):
    store.add_fact("user_001", "Primary caregiver for mother with Alzheimer's", "nervous_system_brain")
    facts = store.get_facts("user_001")
    assert len(facts) == 1
    assert facts[0]["fact"] == "Primary caregiver for mother with Alzheimer's"
    assert facts[0]["mentions"] == 1


def test_increment_existing_fact(store):
    store.add_fact("user_001", "Father had colon cancer", "cancer_oncology")
    store.add_fact("user_001", "Father had colon cancer", "cancer_oncology")
    facts = store.get_facts("user_001")
    assert len(facts) == 1
    assert facts[0]["mentions"] == 2


def test_graduation_at_threshold(store):
    for _ in range(5):
        store.add_fact("user_001", "Vegetarian diet", "hormones_metabolism_nutrition")
    facts = store.get_facts("user_001")
    graduated = store.get_graduated("user_001")
    assert len(facts) == 0
    assert len(graduated) == 1
    assert graduated[0]["fact"] == "Vegetarian diet"


def test_update_contradictory_fact(store):
    store.add_fact("user_001", "Takes metformin daily", "hormones_metabolism_nutrition")
    store.add_fact("user_001", "Takes metformin daily", "hormones_metabolism_nutrition")
    assert store.get_facts("user_001")[0]["mentions"] == 2
    store.update_fact("user_001", "Takes metformin daily", "Stopped taking metformin", "hormones_metabolism_nutrition")
    facts = store.get_facts("user_001")
    assert len(facts) == 1
    assert facts[0]["fact"] == "Stopped taking metformin"
    assert facts[0]["mentions"] == 1


def test_max_facts_evicts_lowest(store):
    for i in range(20):
        store.add_fact("user_001", f"Fact {i}", "general")
    store.add_fact("user_001", "Fact 20", "general")
    facts = store.get_facts("user_001")
    assert len(facts) == 20
    fact_texts = [f["fact"] for f in facts]
    assert "Fact 0" not in fact_texts
    assert "Fact 20" in fact_texts


def test_empty_user(store):
    assert store.get_facts("nonexistent") == []


def test_persistence(tmp_path):
    base = tmp_path / "users"
    s1 = UserMemoryStore(base_dir=base)
    s1.add_fact("u1", "Has asthma", "respiratory")
    s2 = UserMemoryStore(base_dir=base)
    facts = s2.get_facts("u1")
    assert len(facts) == 1
    assert facts[0]["fact"] == "Has asthma"


def test_novel_facts_filtering(store):
    store.add_fact("u1", "Has diabetes", "hormones_metabolism_nutrition")
    store.add_fact("u1", "Father had stroke", "nervous_system_brain")
    novel = store.get_novel_facts(
        "u1",
        profile_conditions=["Diabetes"],
        profile_medications=[],
    )
    assert len(novel) == 1
    assert "stroke" in novel[0]["fact"].lower()
