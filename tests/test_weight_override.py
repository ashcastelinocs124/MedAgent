# tests/test_weight_override.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.agents.agent_b import RetrievalPlanningAgent
from src.agents.context import QueryContext
from src.personalization.models import UserProfile, Sex, HealthLiteracy
from src.personalization.base_graph import build_base_graph
from src.personalization.user_graph import UserSubgraphBuilder
from src.personalization.query_merge import QueryGraphMerger

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
def base_graph():
    return build_base_graph()


@pytest.fixture(scope="module")
def agent(base_graph):
    builder = UserSubgraphBuilder(base_graph)
    merger = QueryGraphMerger(base_graph)
    return RetrievalPlanningAgent(builder=builder, merger=merger, brain_dir="brain")


@pytest.mark.anyio
async def test_weight_overrides_applied(agent):
    """When weight_overrides are provided, they replace pipeline weights."""
    profile = UserProfile(age=45, sex=Sex.MALE)
    ctx = QueryContext(query="test", user_profile=profile)
    ctx.category = "heart_blood_vessels"

    overrides = {
        "kidney_urinary": 0.90,
        "eye_health": 0.50,
        "medications_drug_safety": 0.95,
    }

    ctx = await agent.run(ctx, weight_overrides=overrides)

    assert ctx.retrieval_plan.effective_weights["kidney_urinary"] == 0.90
    assert ctx.retrieval_plan.effective_weights["eye_health"] == 0.50
    assert "kidney_urinary" in ctx.retrieval_plan.must_load


@pytest.mark.anyio
async def test_no_overrides_uses_pipeline(agent):
    """Without overrides, pipeline weights are used normally."""
    profile = UserProfile(age=45, sex=Sex.MALE)
    ctx = QueryContext(query="test", user_profile=profile)
    ctx.category = "heart_blood_vessels"

    ctx = await agent.run(ctx)

    # Pipeline should produce some weights
    assert len(ctx.retrieval_plan.effective_weights) > 0
