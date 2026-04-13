# tests/test_context.py
from src.agents.context import QueryContext, PipelineResult, SearchResult, Citation
from src.personalization.models import UserProfile, HealthLiteracy, Sex


def make_profile():
    return UserProfile(age=45, sex=Sex.FEMALE, health_literacy=HealthLiteracy.MEDIUM)


def make_search_result():
    return SearchResult(
        record_id="123",
        source_table="medmcqa_records",
        primary_category="medications_drug_safety",
        quality_tier="TIER_A",
        chunk_text="Metformin is a biguanide used for type 2 diabetes.",
        relevance_score=0.85,
        rrf_score=0.0,
    )


def test_query_context_initializes():
    profile = make_profile()
    ctx = QueryContext(query="What is metformin?", user_profile=profile)
    assert ctx.query == "What is metformin?"
    assert ctx.category is None
    assert ctx.search_results == []


def test_search_result_fields():
    r = make_search_result()
    assert r.quality_tier == "TIER_A"
    assert r.primary_category == "medications_drug_safety"


def test_pipeline_result_from_context():
    profile = make_profile()
    ctx = QueryContext(query="What is metformin?", user_profile=profile)
    ctx.category = "medications_drug_safety"
    ctx.classification_method = "keyword"
    ctx.normalized_terms = ["metformin"]
    ctx.brain_context = "some brain context"
    ctx.retrieval_plan = None
    ctx.user_subgraph = None
    ctx.search_results = [make_search_result()]
    ctx.raw_answer = "Metformin lowers blood sugar."
    ctx.raw_citations = []
    ctx.confidence = 0.88
    ctx.disclaimer = "Consider discussing with your provider."
    ctx.uncertainty_flags = []
    ctx.final_answer = "Metformin lowers blood sugar.\n\nConsider discussing with your provider."
    ctx.verified_citations = [
        Citation(
            record_id="123",
            source_table="medmcqa_records",
            quality_tier="TIER_A",
            text_snippet="Metformin is a biguanide...",
            relevance_score=0.85,
        )
    ]
    result = PipelineResult.from_context(ctx)
    assert result.answer_text == ctx.final_answer
    assert result.confidence == 0.88
    assert result.category == "medications_drug_safety"
    assert len(result.citations) == 1
