# tests/test_agent_b_memory.py
"""Tests for Agent B's memory injection and graduation."""
import pytest
from unittest.mock import MagicMock

from src.agents.agent_b import RetrievalPlanningAgent
from src.agents.context import QueryContext
from src.personalization.models import UserProfile, HealthLiteracy, Sex, Condition
from src.personalization.user_memory import UserMemoryStore

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def memory_store(tmp_path):
    return UserMemoryStore(base_dir=tmp_path / "users")


@pytest.fixture
def mock_builder():
    builder = MagicMock()
    subgraph = MagicMock()
    subgraph.boosts = {}
    builder.build.return_value = subgraph
    return builder


@pytest.fixture
def mock_merger():
    merger = MagicMock()
    plan = MagicMock()
    plan.effective_weights = {"heart_blood_vessels": 0.5}
    plan.must_load = ["heart_blood_vessels"]
    plan.may_load = []
    merger.plan_retrieval.return_value = plan
    return merger


@pytest.fixture
def agent(mock_builder, mock_merger, memory_store):
    return RetrievalPlanningAgent(
        builder=mock_builder,
        merger=mock_merger,
        brain_dir="brain",
        memory_store=memory_store,
    )


@pytest.fixture
def profile():
    return UserProfile(
        user_id="user_mem_test",
        age=55,
        sex=Sex.MALE,
        health_literacy=HealthLiteracy.MEDIUM,
        conditions=[
            Condition(
                name="Hypertension",
                category_id="heart_blood_vessels",
                subcategory_id="hypertension",
            )
        ],
    )


@pytest.mark.anyio
async def test_memory_applies_temporary_boost(agent, profile, memory_store):
    """Short-term memory facts apply temporary category boosts."""
    memory_store.add_fact("user_mem_test", "Father had stroke at 60", "nervous_system_brain")

    ctx = QueryContext(query="headache treatment", user_profile=profile)
    ctx.category = "nervous_system_brain"

    await agent.run(ctx)

    plan = ctx.retrieval_plan
    weights = plan.effective_weights
    assert "nervous_system_brain" in weights
    # Should be base (0.3 default) + 0.10 boost = 0.40
    assert weights["nervous_system_brain"] >= 0.40


@pytest.mark.anyio
async def test_memory_filters_profile_overlap(agent, profile, memory_store):
    """Facts that overlap with profile conditions are filtered out."""
    memory_store.add_fact("user_mem_test", "Has hypertension", "heart_blood_vessels")
    memory_store.add_fact("user_mem_test", "Smoker for 20 years", "respiratory_chest")

    novel = memory_store.get_novel_facts(
        "user_mem_test",
        profile_conditions=["Hypertension"],
        profile_medications=[],
    )
    assert len(novel) == 1
    assert "smoker" in novel[0]["fact"].lower()


@pytest.mark.anyio
async def test_graduated_facts_apply_permanent_boost(agent, profile, memory_store):
    """Graduated facts result in permanent weight adjustments."""
    for _ in range(5):
        memory_store.add_fact(
            "user_mem_test", "Vegetarian diet", "hormones_metabolism_nutrition"
        )

    graduated = memory_store.get_graduated("user_mem_test")
    assert len(graduated) == 1

    ctx = QueryContext(query="nutrition advice", user_profile=profile)
    ctx.category = "hormones_metabolism_nutrition"

    await agent.run(ctx)

    plan = ctx.retrieval_plan
    weights = plan.effective_weights
    # Graduated boost is 0.15, base 0.3 = 0.45
    assert "hormones_metabolism_nutrition" in weights
    assert weights["hormones_metabolism_nutrition"] == pytest.approx(0.45, abs=1e-9)


@pytest.mark.anyio
async def test_no_memory_store_no_error(mock_builder, mock_merger, profile):
    """Agent B without memory_store works as before."""
    agent = RetrievalPlanningAgent(
        builder=mock_builder,
        merger=mock_merger,
        brain_dir="brain",
    )
    ctx = QueryContext(query="test query", user_profile=profile)
    ctx.category = "heart_blood_vessels"
    await agent.run(ctx)
    assert ctx.retrieval_plan is not None


@pytest.mark.anyio
async def test_multiple_facts_same_category_accumulate(agent, profile, memory_store):
    """Multiple novel facts in the same category accumulate their boosts."""
    memory_store.add_fact("user_mem_test", "Father had stroke at 60", "nervous_system_brain")
    memory_store.add_fact("user_mem_test", "Frequent migraines", "nervous_system_brain")

    ctx = QueryContext(query="headache treatment", user_profile=profile)
    ctx.category = "nervous_system_brain"

    await agent.run(ctx)

    plan = ctx.retrieval_plan
    weights = plan.effective_weights
    # Two facts at 0.10 each on base 0.3 = 0.50
    assert weights["nervous_system_brain"] >= 0.50


@pytest.mark.anyio
async def test_memory_boost_capped_at_095(agent, profile, memory_store):
    """Memory boosts cannot push a weight above 0.95."""
    # Add many facts in the same category
    for i in range(10):
        memory_store.add_fact(
            "user_mem_test", f"Neuro fact {i}", "nervous_system_brain"
        )

    ctx = QueryContext(query="headache treatment", user_profile=profile)
    ctx.category = "nervous_system_brain"

    await agent.run(ctx)

    plan = ctx.retrieval_plan
    weights = plan.effective_weights
    assert weights.get("nervous_system_brain", 0) <= 0.95
