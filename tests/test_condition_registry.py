# tests/test_condition_registry.py
import pytest
from src.personalization.condition_registry import (
    CONDITION_CHECKLIST,
    MEDICATION_KEYWORDS,
    resolve_conditions,
    resolve_medications,
    match_freetext_conditions,
)
from src.personalization.models import Condition, Medication


class TestConditionChecklist:
    def test_all_items_have_valid_category(self):
        """Every checklist item must map to one of the 20 brain categories."""
        valid_categories = {
            "heart_blood_vessels", "brain_nervous_system", "mental_health",
            "digestive_liver", "breathing_lungs", "blood_immune", "cancer",
            "infections", "bones_joints_muscles", "kidney_urinary",
            "womens_reproductive", "childrens_health", "eye_health",
            "ear_nose_throat", "skin_dermatology", "medications_drug_safety",
            "hormones_metabolism_nutrition", "emergency_critical_care",
            "dental_oral", "public_health_prevention",
        }
        for item in CONDITION_CHECKLIST:
            assert item["category_id"] in valid_categories, (
                f"{item['key']} has invalid category_id: {item['category_id']}"
            )

    def test_all_items_have_required_fields(self):
        for item in CONDITION_CHECKLIST:
            assert "key" in item
            assert "name" in item
            assert "category_id" in item
            assert "subcategory_id" in item
            assert "group" in item

    def test_at_least_40_items(self):
        assert len(CONDITION_CHECKLIST) >= 40

    def test_no_duplicate_keys(self):
        keys = [item["key"] for item in CONDITION_CHECKLIST]
        assert len(keys) == len(set(keys))


class TestResolveConditions:
    def test_resolves_known_keys(self):
        selected = ["hypertension", "type2_diabetes"]
        conditions = resolve_conditions(selected)
        assert len(conditions) == 2
        assert all(isinstance(c, Condition) for c in conditions)
        assert conditions[0].category_id == "heart_blood_vessels"
        assert conditions[1].category_id == "hormones_metabolism_nutrition"

    def test_ignores_unknown_keys(self):
        conditions = resolve_conditions(["hypertension", "nonexistent_key"])
        assert len(conditions) == 1

    def test_empty_input(self):
        assert resolve_conditions([]) == []


class TestResolveMedications:
    def test_metformin(self):
        meds = resolve_medications(["Metformin"])
        assert len(meds) == 1
        assert meds[0].category_id == "hormones_metabolism_nutrition"

    def test_case_insensitive(self):
        meds = resolve_medications(["LISINOPRIL"])
        assert len(meds) == 1
        assert meds[0].category_id == "heart_blood_vessels"

    def test_unknown_med_falls_back(self):
        meds = resolve_medications(["SomeUnknownDrug123"])
        assert len(meds) == 1
        assert meds[0].category_id == "medications_drug_safety"

    def test_empty_input(self):
        assert resolve_medications([]) == []


class TestFreetextMatcher:
    def test_matches_celiac(self):
        conditions = match_freetext_conditions("I also have celiac disease")
        assert len(conditions) >= 1
        assert conditions[0].category_id == "digestive_liver"

    def test_matches_multiple(self):
        conditions = match_freetext_conditions("celiac disease and rosacea")
        assert len(conditions) >= 2

    def test_no_match_returns_empty(self):
        conditions = match_freetext_conditions("nothing relevant here xyz")
        assert conditions == []

    def test_empty_string(self):
        assert match_freetext_conditions("") == []
