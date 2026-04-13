# tests/test_agent_a_memory.py
"""Tests for Agent A's user memory extraction."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.agent_a import QueryUnderstandingAgent
from src.agents.context import QueryContext
from src.personalization.models import UserProfile, HealthLiteracy, Sex, Condition
from src.personalization.user_memory import UserMemoryStore


@pytest.fixture
def memory_store(tmp_path):
    return UserMemoryStore(base_dir=tmp_path / "users")


@pytest.fixture
def agent(memory_store):
    return QueryUnderstandingAgent(
        db_conn=None,
        openai_client=None,
        anthropic_client=None,
        brain_dir="brain",
        memory_store=memory_store,
    )


@pytest.fixture
def profile():
    return UserProfile(
        user_id="test_user_123",
        age=45,
        sex=Sex.FEMALE,
        health_literacy=HealthLiteracy.MEDIUM,
        conditions=[Condition(name="Type 2 Diabetes", category_id="hormones_metabolism_nutrition", subcategory_id="diabetes")],
    )


async def test_extract_user_facts_finds_new_context(agent, profile):
    """Memory extraction finds caregiver context not in profile."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "new_facts": [{"fact": "Primary caregiver for mother with Alzheimer's", "category": "nervous_system_brain"}]
    })
    # Need an openai client for extraction
    agent._openai = MagicMock()

    with patch("src.agents.agent_a.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_response
        facts = await agent._extract_user_facts(
            query="What medications help with Alzheimer's? My mom was just diagnosed and I'm taking care of her.",
            profile=profile,
        )
    assert len(facts) == 1
    assert "caregiver" in facts[0]["fact"].lower() or "alzheimer" in facts[0]["fact"].lower()


async def test_extract_user_facts_returns_empty_when_nothing_new(agent, profile):
    """Returns empty when query only references known conditions."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({"new_facts": []})
    agent._openai = MagicMock()

    with patch("src.agents.agent_a.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_response
        facts = await agent._extract_user_facts(
            query="What foods should I avoid with diabetes?",
            profile=profile,
        )
    assert facts == []


async def test_extract_user_facts_silent_on_failure(agent, profile):
    """LLM failure returns empty list, no exception."""
    agent._openai = MagicMock()

    with patch("src.agents.agent_a.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.side_effect = Exception("API error")
        facts = await agent._extract_user_facts(
            query="Some query",
            profile=profile,
        )
    assert facts == []


async def test_run_writes_memory(agent, profile, memory_store):
    """Full run() writes extracted facts to memory store."""
    ctx = QueryContext(query="My father had a heart attack at 50, should I get screened?", user_profile=profile)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "new_facts": [{"fact": "Father had heart attack at age 50", "category": "heart_blood_vessels"}]
    })
    agent._openai = MagicMock()

    with patch("src.agents.agent_a.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_response
        await agent.run(ctx)

    facts = memory_store.get_facts("test_user_123")
    assert len(facts) == 1
    assert "heart attack" in facts[0]["fact"].lower()
