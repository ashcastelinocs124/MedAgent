# tests/test_llm_augmenter.py
import pytest
from unittest.mock import MagicMock
from src.personalization.llm_augmenter import (
    _clamp_adjustments,
    _parse_response,
    _format_profile,
    _format_weights,
    _MAX_BOOST,
    _MAX_REDUCTION,
    _WEIGHT_FLOOR,
    _WEIGHT_CEILING,
    review_profile,
    apply_answers,
)
from src.personalization.models import (
    Condition, HealthLiteracy, Medication, Sex, UserProfile,
)


class TestClampAdjustments:
    def test_within_bounds(self):
        baseline = {"kidney_urinary": 0.50}
        adjustments = {"kidney_urinary": {"weight": 0.70, "reason": "test"}}
        result = _clamp_adjustments(adjustments, baseline)
        assert result["kidney_urinary"] == 0.70

    def test_boost_capped_at_max(self):
        baseline = {"kidney_urinary": 0.50}
        adjustments = {"kidney_urinary": {"weight": 0.95, "reason": "test"}}
        result = _clamp_adjustments(adjustments, baseline)
        # delta = 0.45, capped to 0.30 -> 0.50 + 0.30 = 0.80
        assert result["kidney_urinary"] == 0.80

    def test_reduction_capped_at_max(self):
        baseline = {"heart_blood_vessels": 0.90}
        adjustments = {"heart_blood_vessels": {"weight": 0.50, "reason": "test"}}
        result = _clamp_adjustments(adjustments, baseline)
        # delta = -0.40, capped to -0.20 -> 0.90 - 0.20 = 0.70
        assert result["heart_blood_vessels"] == 0.70

    def test_floor_enforced(self):
        baseline = {"eye_health": 0.10}
        adjustments = {"eye_health": {"weight": 0.0, "reason": "test"}}
        result = _clamp_adjustments(adjustments, baseline)
        assert result["eye_health"] == _WEIGHT_FLOOR

    def test_ceiling_enforced(self):
        baseline = {"heart_blood_vessels": 0.80}
        adjustments = {"heart_blood_vessels": {"weight": 1.0, "reason": "test"}}
        result = _clamp_adjustments(adjustments, baseline)
        assert result["heart_blood_vessels"] == _WEIGHT_CEILING

    def test_unknown_category_ignored(self):
        baseline = {"kidney_urinary": 0.50}
        adjustments = {"nonexistent": {"weight": 0.90, "reason": "test"}}
        result = _clamp_adjustments(adjustments, baseline)
        # nonexistent has baseline 0.0 -> 0.0 + min(0.90, 0.30) = 0.30
        assert result["nonexistent"] == 0.30

    def test_empty_adjustments(self):
        assert _clamp_adjustments({}, {"a": 0.5}) == {}


class TestParseResponse:
    def test_clean_json(self):
        text = '{"needs_clarification": false, "adjustments": {}}'
        result = _parse_response(text)
        assert result["needs_clarification"] is False

    def test_json_with_markdown_fences(self):
        text = '```json\n{"needs_clarification": true}\n```'
        result = _parse_response(text)
        assert result["needs_clarification"] is True

    def test_json_with_leading_text(self):
        text = 'Here is the result:\n{"adjustments": {"a": {"weight": 0.5}}}'
        result = _parse_response(text)
        assert "adjustments" in result

    def test_no_json_returns_empty(self):
        assert _parse_response("no json here") == {}

    def test_empty_string(self):
        assert _parse_response("") == {}


class TestFormatProfile:
    def test_formats_with_conditions(self):
        profile = UserProfile(
            age=68, sex=Sex.FEMALE, health_literacy=HealthLiteracy.LOW,
            conditions=[Condition(name="Diabetes", category_id="hormones_metabolism_nutrition",
                                  subcategory_id="diabetes", active=True)],
        )
        text = _format_profile(profile)
        assert "68" in text
        assert "female" in text
        assert "low" in text
        assert "Diabetes" in text

    def test_formats_without_conditions(self):
        profile = UserProfile(age=30)
        text = _format_profile(profile)
        assert "none reported" in text


class TestFormatWeights:
    def test_sorted_descending(self):
        weights = {"a": 0.3, "b": 0.9, "c": 0.5}
        text = _format_weights(weights)
        lines = text.strip().split("\n")
        assert "b" in lines[0]
        assert "a" in lines[-1]


# ── GPT-4o Integration Tests (mocked) ────────────────────────────────────

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_openai():
    """Mock OpenAI client that returns a canned response."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_profile():
    return UserProfile(
        age=68, sex=Sex.FEMALE, health_literacy=HealthLiteracy.LOW,
        conditions=[
            Condition(name="Hypertension", category_id="heart_blood_vessels",
                      subcategory_id="hypertension_blood_pressure", active=True),
            Condition(name="Type 2 Diabetes", category_id="hormones_metabolism_nutrition",
                      subcategory_id="diabetes_type_1_type_2_gestational", active=True),
        ],
        medications=[
            Medication(name="Metformin", category_id="hormones_metabolism_nutrition"),
        ],
    )


@pytest.fixture
def sample_weights():
    return {
        "heart_blood_vessels": 0.90,
        "hormones_metabolism_nutrition": 0.85,
        "kidney_urinary": 0.50,
        "eye_health": 0.20,
    }


class TestReviewProfile:
    @pytest.mark.anyio
    async def test_no_clarification_needed(self, mock_openai, sample_profile, sample_weights):
        """When LLM returns adjustments without questions."""
        response_text = '{"needs_clarification": false, "adjustments": {"eye_health": {"weight": 0.50, "reason": "retinopathy"}}}'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=response_text))]
        mock_openai.chat.completions.create = MagicMock(return_value=mock_response)

        result = await review_profile(mock_openai, sample_profile, sample_weights)
        assert result["needs_clarification"] is False
        assert "eye_health" in result.get("_clamped_adjustments", {})

    @pytest.mark.anyio
    async def test_clarification_needed(self, mock_openai, sample_profile, sample_weights):
        """When LLM asks a question."""
        response_text = '{"needs_clarification": true, "questions": [{"question": "Kidney problems?", "target_categories": ["kidney_urinary"], "options": ["Yes", "No"], "why": "CKD risk"}], "preliminary_adjustments": {"eye_health": {"weight": 0.45, "reason": "retinopathy"}}}'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=response_text))]
        mock_openai.chat.completions.create = MagicMock(return_value=mock_response)

        result = await review_profile(mock_openai, sample_profile, sample_weights)
        assert result["needs_clarification"] is True
        assert len(result["questions"]) == 1
        assert "_clamped_preliminary" in result

    @pytest.mark.anyio
    async def test_api_failure_returns_empty(self, mock_openai, sample_profile, sample_weights):
        """When GPT-4o call fails, return empty dict (fallback to pipeline)."""
        mock_openai.chat.completions.create = MagicMock(side_effect=Exception("API down"))

        result = await review_profile(mock_openai, sample_profile, sample_weights)
        assert result == {}


class TestApplyAnswers:
    @pytest.mark.anyio
    async def test_applies_answers(self, mock_openai, sample_profile, sample_weights):
        """Verify answers + prior reasoning produce clamped adjustments."""
        response_text = '{"adjustments": {"kidney_urinary": {"weight": 0.85, "reason": "confirmed CKD"}}}'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=response_text))]
        mock_openai.chat.completions.create = MagicMock(return_value=mock_response)

        review_result = {
            "questions": [{"question": "Kidney?", "target_categories": ["kidney_urinary"],
                           "options": ["Yes", "No"], "why": "CKD risk"}],
            "preliminary_adjustments": {},
        }

        result = await apply_answers(
            mock_openai, sample_profile, sample_weights,
            review_result, ["Yes"],
        )
        assert "kidney_urinary" in result
        assert result["kidney_urinary"] <= _WEIGHT_CEILING
