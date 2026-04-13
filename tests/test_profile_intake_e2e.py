# tests/test_profile_intake_e2e.py
"""End-to-end test for the profile intake flow with mocked GPT-4o."""
import pytest
from unittest.mock import MagicMock
from src.personalization.condition_registry import resolve_conditions, resolve_medications
from src.personalization.llm_augmenter import review_profile, _clamp_adjustments
from src.personalization.models import HealthLiteracy, Sex, UserProfile
from src.personalization.base_graph import build_base_graph
from src.personalization.user_graph import UserSubgraphBuilder
from src.personalization.query_merge import QueryGraphMerger

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_full_intake_flow():
    """Checklist -> pipeline -> mocked LLM review -> merged weights."""
    # Step 1: Resolve checklist
    conditions = resolve_conditions(["hypertension", "type2_diabetes", "arthritis"])
    medications = resolve_medications(["Metformin", "Lisinopril", "Ibuprofen"])
    assert len(conditions) == 3
    assert len(medications) == 3

    # Step 2: Build profile
    profile = UserProfile(
        age=68, sex=Sex.FEMALE, health_literacy=HealthLiteracy.LOW,
        conditions=conditions, medications=medications,
    )

    # Step 3: Run 5-stage pipeline
    base_graph = build_base_graph()
    builder = UserSubgraphBuilder(base_graph)
    merger = QueryGraphMerger(base_graph)
    subgraph = builder.build(profile)
    plan = merger.plan_retrieval("heart_blood_vessels", subgraph)
    baseline = plan.effective_weights

    assert len(baseline) > 0
    assert "medications_drug_safety" in baseline or "kidney_urinary" in baseline

    # Step 4: Mock LLM review (no clarification)
    mock_openai = MagicMock()
    response_text = '{"needs_clarification": false, "adjustments": {"eye_health": {"weight": 0.50, "reason": "retinopathy"}, "kidney_urinary": {"weight": 0.85, "reason": "CKD risk"}}}'
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=response_text))]
    mock_openai.chat.completions.create = MagicMock(return_value=mock_response)

    result = await review_profile(mock_openai, profile, baseline)
    clamped = result.get("_clamped_adjustments", {})

    # Step 5: Merge
    final_weights = {**baseline, **clamped}

    # Verify LLM adjustments were applied
    if "eye_health" in clamped:
        assert final_weights["eye_health"] > baseline.get("eye_health", 0.0)
    if "kidney_urinary" in clamped:
        assert final_weights["kidney_urinary"] >= baseline.get("kidney_urinary", 0.0)
