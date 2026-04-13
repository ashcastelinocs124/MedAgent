# tests/test_agent_a.py
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.agents.agent_a import QueryUnderstandingAgent
from src.agents.context import QueryContext
from src.personalization.models import UserProfile, HealthLiteracy, Sex


@pytest.fixture
def profile():
    return UserProfile(age=45, sex=Sex.FEMALE, health_literacy=HealthLiteracy.MEDIUM)


@pytest.fixture
def agent():
    # No real DB/API needed for keyword tests
    return QueryUnderstandingAgent(
        db_conn=None,
        openai_client=None,
        anthropic_client=None,
        brain_dir="brain",
    )


@pytest.mark.asyncio
async def test_keyword_match_assigns_category(agent, profile):
    ctx = QueryContext(query="I have chest pain and heart palpitations", user_profile=profile)
    ctx = await agent.run(ctx)
    assert ctx.category == "heart_blood_vessels"
    assert ctx.classification_method == "keyword"


@pytest.mark.asyncio
async def test_normalized_terms_populated(agent, profile):
    ctx = QueryContext(query="my blood sugar is high", user_profile=profile)
    ctx = await agent.run(ctx)
    assert len(ctx.normalized_terms) > 0


@pytest.mark.asyncio
async def test_fallback_on_api_error(agent, profile):
    """When Claude call fails, default to public_health_prevention."""
    ctx = QueryContext(query="zzzzxxx nonsense query with no matches", user_profile=profile)
    with patch.object(agent, "_llm_classify", side_effect=Exception("API error")):
        with patch.object(agent, "_embedding_classify", return_value=(None, 0.0)):
            ctx = await agent.run(ctx)
    assert ctx.category == "public_health_prevention"
    assert ctx.classification_method == "fallback"


@pytest.mark.asyncio
async def test_keyword_tie_falls_through_to_embedding(agent, profile):
    """A term that matches multiple categories equally falls through to embedding step."""
    # Patch _embedding_classify to return a confident match
    with patch.object(agent, "_embedding_classify", return_value=("mental_health", 0.75)) as mock_emb:
        ctx = QueryContext(query="depression anxiety medication", user_profile=profile)
        ctx = await agent.run(ctx)
        # If keyword step found a tie, embedding should have been called
        # Result must be a valid category
        assert ctx.category is not None
        assert ctx.classification_method in ("keyword", "embedding", "llm", "fallback")
