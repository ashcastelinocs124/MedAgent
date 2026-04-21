# tests/test_agent_c.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.agents.agent_c import SynthesisAgent
from src.agents.context import QueryContext, SearchResult
from src.personalization.models import UserProfile, HealthLiteracy, Sex


@pytest.fixture
def profile():
    return UserProfile(age=45, sex=Sex.FEMALE, health_literacy=HealthLiteracy.LOW)


@pytest.fixture
def mock_searcher():
    searcher = MagicMock()
    searcher.search.return_value = [
        SearchResult(
            record_id="1", source_table="medmcqa_records",
            primary_category="medications_drug_safety",
            quality_tier="TIER_A", chunk_text="Metformin reduces blood sugar.",
            relevance_score=0.9, rrf_score=0.03,
        )
    ]
    return searcher


@pytest.fixture
def mock_openai():
    client = MagicMock()
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(
        content="Metformin is used to treat type 2 diabetes by lowering blood sugar."
    ))]
    client.chat.completions.create.return_value = resp
    return client


@pytest.fixture
def agent(mock_searcher, mock_openai):
    return SynthesisAgent(searcher=mock_searcher, openai_client=mock_openai)


@pytest.mark.asyncio
async def test_agent_c_calls_search(agent, mock_searcher, profile):
    ctx = QueryContext(query="What is metformin?", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.normalized_terms = ["metformin"]
    ctx.classification_method = "keyword"
    ctx.brain_context = "Drug safety rules here."
    ctx.retrieval_plan = MagicMock(must_load=["medications_drug_safety"], may_load=[])
    ctx.user_subgraph = None
    ctx = await agent.run(ctx)
    mock_searcher.search.assert_called_once()
    assert len(ctx.search_results) == 1


@pytest.mark.asyncio
async def test_agent_c_sets_raw_answer(agent, profile):
    ctx = QueryContext(query="What is metformin?", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.normalized_terms = ["metformin"]
    ctx.classification_method = "keyword"
    ctx.brain_context = "Drug safety rules."
    ctx.retrieval_plan = MagicMock(must_load=[], may_load=[])
    ctx.user_subgraph = None
    ctx = await agent.run(ctx)
    assert ctx.raw_answer
    assert len(ctx.raw_answer) > 10


@pytest.mark.asyncio
async def test_prompt_includes_literacy_instruction(agent, profile):
    """Low literacy users should get a simple language instruction in the prompt."""
    ctx = QueryContext(query="What is metformin?", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.normalized_terms = ["metformin"]
    ctx.classification_method = "keyword"
    ctx.brain_context = ""
    ctx.retrieval_plan = MagicMock(must_load=[], may_load=[])
    ctx.user_subgraph = None

    captured_prompt = []
    def capture(*args, **kwargs):
        # OpenAI system prompt is the first message in the messages list
        msgs = kwargs.get("messages", [])
        system_msg = next((m["content"] for m in msgs if m.get("role") == "system"), "")
        captured_prompt.append(system_msg)
        resp = MagicMock()
        resp.choices = [MagicMock(message=MagicMock(content="Simple answer."))]
        return resp

    agent._openai.chat.completions.create = capture
    await agent.run(ctx)
    assert any("simple" in p.lower() or "plain" in p.lower() or "grade" in p.lower() for p in captured_prompt)
