# tests/test_agent_d.py
import pytest
from src.agents.agent_d import VerificationAgent
from src.agents.context import QueryContext, SearchResult, Citation
from src.personalization.models import UserProfile, HealthLiteracy, Sex


@pytest.fixture
def agent():
    return VerificationAgent()


@pytest.fixture
def profile():
    return UserProfile(age=45, sex=Sex.FEMALE, health_literacy=HealthLiteracy.MEDIUM)


def make_result(tier: str, score: float, table: str = "medmcqa_records", rid: str = "1"):
    return SearchResult(rid, table, "medications_drug_safety", tier, "text", score, 0.03)


def make_citation(tier: str, table: str = "medmcqa_records", rid: str = "1"):
    return Citation(rid, table, tier, "snippet", 0.9)


@pytest.mark.asyncio
async def test_high_confidence_tier_a_results(agent, profile):
    ctx = QueryContext(query="q", user_profile=profile)
    ctx.category = "heart_blood_vessels"
    ctx.search_results = [make_result("TIER_A", 1.0, rid=str(i)) for i in range(5)]
    ctx.raw_answer = "Answer text."
    ctx.raw_citations = [make_citation("TIER_A", rid=str(i)) for i in range(5)]
    ctx = await agent.run(ctx)
    assert ctx.confidence >= 0.95
    assert ctx.disclaimer is None


@pytest.mark.asyncio
async def test_low_confidence_adds_disclaimer(agent, profile):
    ctx = QueryContext(query="q", user_profile=profile)
    ctx.category = "mental_health"
    ctx.search_results = [make_result("TIER_D", 0.2, rid=str(i)) for i in range(2)]
    ctx.raw_answer = "Answer."
    ctx.raw_citations = [make_citation("TIER_D", rid=str(i)) for i in range(2)]
    ctx = await agent.run(ctx)
    assert ctx.confidence < 0.5
    assert ctx.disclaimer is not None
    assert "consult" in ctx.disclaimer.lower() or "limited" in ctx.disclaimer.lower()


@pytest.mark.asyncio
async def test_drug_interaction_cap(agent, profile):
    """Medications category with single source table → confidence capped at 0.75."""
    ctx = QueryContext(query="drug interaction", user_profile=profile)
    ctx.category = "medications_drug_safety"
    # All results from same source_table
    ctx.search_results = [make_result("TIER_A", 1.0, table="medmcqa_records", rid=str(i)) for i in range(5)]
    ctx.raw_answer = "Answer."
    ctx.raw_citations = [make_citation("TIER_A", rid=str(i)) for i in range(5)]
    ctx = await agent.run(ctx)
    assert ctx.confidence <= 0.75


@pytest.mark.asyncio
async def test_deduplication_by_composite_key(agent, profile):
    """Duplicate (source_table, record_id) pairs should be collapsed."""
    ctx = QueryContext(query="q", user_profile=profile)
    ctx.category = "heart_blood_vessels"
    ctx.search_results = [
        make_result("TIER_A", 0.9, rid="42"),
        make_result("TIER_A", 0.9, rid="42"),  # duplicate
        make_result("TIER_B", 0.7, rid="99"),
    ]
    ctx.raw_answer = "Answer."
    ctx.raw_citations = [
        make_citation("TIER_A", rid="42"),
        make_citation("TIER_A", rid="42"),  # duplicate
        make_citation("TIER_B", rid="99"),
    ]
    ctx = await agent.run(ctx)
    assert len(ctx.verified_citations) == 2  # deduped


@pytest.mark.asyncio
async def test_uncertainty_flag_added_below_80_percent(agent, profile):
    ctx = QueryContext(query="q", user_profile=profile)
    ctx.category = "mental_health"
    ctx.search_results = [make_result("TIER_C", 0.4, rid=str(i)) for i in range(3)]
    ctx.raw_answer = "Answer."
    ctx.raw_citations = []
    ctx = await agent.run(ctx)
    assert "[UNCERTAINTY FLAG]" in ctx.uncertainty_flags


@pytest.mark.asyncio
async def test_narrow_ti_flag_added_for_narrow_index_drugs(agent, profile):
    """Results mentioning warfarin in medications category → [NARROW TI FLAG]."""
    ctx = QueryContext(query="warfarin dosing", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.search_results = [
        SearchResult("1", "medmcqa_records", "medications_drug_safety", "TIER_A",
                     "Warfarin is a narrow therapeutic index drug requiring careful monitoring.",
                     0.9, 0.03)
    ]
    ctx.raw_answer = "Answer."
    ctx.raw_citations = []
    ctx = await agent.run(ctx)
    assert "[NARROW TI FLAG]" in ctx.uncertainty_flags


@pytest.mark.asyncio
async def test_disclaimer_appended_to_final_answer(agent, profile):
    ctx = QueryContext(query="q", user_profile=profile)
    ctx.category = "mental_health"
    ctx.search_results = [make_result("TIER_D", 0.1, rid="1")]
    ctx.raw_answer = "Some answer."
    ctx.raw_citations = []
    ctx = await agent.run(ctx)
    assert ctx.disclaimer in ctx.final_answer
