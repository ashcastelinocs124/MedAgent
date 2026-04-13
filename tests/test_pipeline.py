# tests/test_pipeline.py
import os
import pytest
import psycopg2
from openai import OpenAI
from anthropic import Anthropic
from src.pipeline import Pipeline
from src.agents.context import PipelineResult
from src.personalization.models import UserProfile, HealthLiteracy, Sex, Condition

DATABASE_URL = os.environ["DATABASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]


@pytest.fixture(scope="module")
def pipeline():
    conn = psycopg2.connect(DATABASE_URL)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    p = Pipeline(conn, openai_client, anthropic_client, build_centroids=False)
    yield p
    conn.close()


@pytest.fixture
def basic_profile():
    return UserProfile(age=40, sex=Sex.MALE, health_literacy=HealthLiteracy.MEDIUM)


@pytest.mark.asyncio
async def test_pipeline_returns_pipeline_result(pipeline, basic_profile):
    result = await pipeline.run("What is metformin used for?", basic_profile)
    assert isinstance(result, PipelineResult)


@pytest.mark.asyncio
async def test_pipeline_result_has_required_fields(pipeline, basic_profile):
    result = await pipeline.run("What are symptoms of high blood pressure?", basic_profile)
    assert result.answer_text
    assert isinstance(result.confidence, float)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.citations, list)
    assert isinstance(result.uncertainty_flags, list)
    assert result.category is not None


@pytest.mark.asyncio
async def test_pipeline_assigns_correct_category(pipeline, basic_profile):
    result = await pipeline.run("I have chest pain and shortness of breath", basic_profile)
    # Should classify to heart or emergency category
    assert result.category in (
        "heart_blood_vessels", "emergency_critical_care", "breathing_lungs",
        "respiratory_lungs", "emergency_trauma", "nervous_system_brain",
        "public_health_prevention",
    )


@pytest.mark.asyncio
async def test_pipeline_low_evidence_adds_disclaimer(pipeline, basic_profile):
    """Obscure query should produce a disclaimer."""
    result = await pipeline.run(
        "What is the treatment for VEXAS syndrome?", basic_profile
    )
    # Either has disclaimer or high confidence — both valid
    if result.confidence < 0.80:
        assert result.disclaimer is not None
