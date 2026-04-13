# tests/test_agent_b.py
import pytest
from unittest.mock import MagicMock
from src.agents.agent_b import RetrievalPlanningAgent
from src.agents.context import QueryContext
from src.personalization.models import UserProfile, HealthLiteracy, Sex
from src.personalization.base_graph import build_base_graph
from src.personalization.user_graph import UserSubgraphBuilder
from src.personalization.query_merge import QueryGraphMerger

# Use anyio (installed) rather than pytest-asyncio for async test support.
# Pin to asyncio backend — trio is not installed in this environment.
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


@pytest.fixture
def profile():
    return UserProfile(age=45, sex=Sex.FEMALE, health_literacy=HealthLiteracy.MEDIUM)


@pytest.mark.anyio
async def test_agent_b_sets_brain_context(agent, profile):
    ctx = QueryContext(query="chest pain", user_profile=profile)
    ctx.category = "heart_blood_vessels"
    ctx.normalized_terms = ["chest pain"]
    ctx.classification_method = "keyword"
    ctx = await agent.run(ctx)
    assert len(ctx.brain_context) > 100
    assert ctx.retrieval_plan is not None


@pytest.mark.anyio
async def test_brain_context_contains_category_content(agent, profile):
    ctx = QueryContext(query="drug interaction", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.normalized_terms = ["drug interaction"]
    ctx.classification_method = "keyword"
    ctx = await agent.run(ctx)
    # Should contain content from the medications category file
    assert "medication" in ctx.brain_context.lower() or "drug" in ctx.brain_context.lower()


@pytest.mark.anyio
async def test_brain_context_under_token_budget(agent, profile):
    ctx = QueryContext(query="cancer treatment", user_profile=profile)
    ctx.category = "cancer"
    ctx.normalized_terms = ["cancer"]
    ctx.classification_method = "keyword"
    ctx = await agent.run(ctx)
    # Rough check: 8000 tokens * ~4 chars/token = ~32000 chars
    assert len(ctx.brain_context) < 35_000


@pytest.mark.anyio
async def test_user_subgraph_set_on_context(agent, profile):
    ctx = QueryContext(query="diabetes medication", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.normalized_terms = ["diabetes"]
    ctx.classification_method = "keyword"
    ctx = await agent.run(ctx)
    assert ctx.user_subgraph is not None
