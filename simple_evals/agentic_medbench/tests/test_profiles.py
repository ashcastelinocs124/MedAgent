"""Tests for user profile presets and subgraph builder helper."""

from __future__ import annotations

import pytest

from simple_evals.agentic_medbench.profiles import (
    PROFILE_PRESETS,
    build_profile_and_subgraph,
)
from src.personalization.models import HealthLiteracy, Sex, UserProfile
from src.personalization.user_graph import UserSubgraph


class TestProfilePresetsExist:
    """Verify the four required profiles are present with correct names."""

    EXPECTED_NAMES = {"default", "low_literacy_patient", "high_literacy_nurse", "elderly_comorbid"}

    def test_four_profiles_exist(self) -> None:
        assert set(PROFILE_PRESETS.keys()) == self.EXPECTED_NAMES

    def test_all_profiles_are_user_profile_instances(self) -> None:
        for name, profile in PROFILE_PRESETS.items():
            assert isinstance(profile, UserProfile), f"{name} is not a UserProfile"


class TestDefaultProfile:
    """The default profile should have no conditions or medications."""

    @pytest.fixture()
    def profile(self) -> UserProfile:
        return PROFILE_PRESETS["default"]

    def test_age(self, profile: UserProfile) -> None:
        assert profile.age == 40

    def test_sex(self, profile: UserProfile) -> None:
        assert profile.sex is Sex.PREFER_NOT_TO_SAY

    def test_health_literacy(self, profile: UserProfile) -> None:
        assert profile.health_literacy is HealthLiteracy.MEDIUM

    def test_no_conditions(self, profile: UserProfile) -> None:
        assert profile.conditions == []

    def test_no_medications(self, profile: UserProfile) -> None:
        assert profile.medications == []


class TestLowLiteracyPatientProfile:
    """The low-literacy patient profile has diabetes + hypertension."""

    @pytest.fixture()
    def profile(self) -> UserProfile:
        return PROFILE_PRESETS["low_literacy_patient"]

    def test_age(self, profile: UserProfile) -> None:
        assert profile.age == 55

    def test_sex(self, profile: UserProfile) -> None:
        assert profile.sex is Sex.MALE

    def test_health_literacy(self, profile: UserProfile) -> None:
        assert profile.health_literacy is HealthLiteracy.LOW

    def test_two_conditions(self, profile: UserProfile) -> None:
        assert len(profile.conditions) == 2

    def test_two_medications(self, profile: UserProfile) -> None:
        assert len(profile.medications) == 2

    def test_condition_names(self, profile: UserProfile) -> None:
        names = {c.name for c in profile.conditions}
        assert names == {"Type 2 Diabetes", "Hypertension"}

    def test_medication_names(self, profile: UserProfile) -> None:
        names = {m.name for m in profile.medications}
        assert names == {"Metformin", "Lisinopril"}


class TestHighLiteracyNurseProfile:
    """The nurse profile is a healthy, high-literacy professional."""

    @pytest.fixture()
    def profile(self) -> UserProfile:
        return PROFILE_PRESETS["high_literacy_nurse"]

    def test_age(self, profile: UserProfile) -> None:
        assert profile.age == 32

    def test_sex(self, profile: UserProfile) -> None:
        assert profile.sex is Sex.FEMALE

    def test_health_literacy(self, profile: UserProfile) -> None:
        assert profile.health_literacy is HealthLiteracy.HIGH

    def test_no_conditions(self, profile: UserProfile) -> None:
        assert profile.conditions == []

    def test_no_medications(self, profile: UserProfile) -> None:
        assert profile.medications == []


class TestElderlyComorbidProfile:
    """The elderly comorbid profile has 3 conditions and 3 medications."""

    @pytest.fixture()
    def profile(self) -> UserProfile:
        return PROFILE_PRESETS["elderly_comorbid"]

    def test_age(self, profile: UserProfile) -> None:
        assert profile.age == 72

    def test_sex(self, profile: UserProfile) -> None:
        assert profile.sex is Sex.MALE

    def test_health_literacy(self, profile: UserProfile) -> None:
        assert profile.health_literacy is HealthLiteracy.MEDIUM

    def test_three_conditions(self, profile: UserProfile) -> None:
        assert len(profile.conditions) == 3

    def test_three_medications(self, profile: UserProfile) -> None:
        assert len(profile.medications) == 3

    def test_condition_names(self, profile: UserProfile) -> None:
        names = {c.name for c in profile.conditions}
        assert names == {"Congestive Heart Failure", "COPD", "Arthritis"}

    def test_medication_names(self, profile: UserProfile) -> None:
        names = {m.name for m in profile.medications}
        assert names == {"Furosemide", "Albuterol", "Ibuprofen"}


class TestBuildProfileAndSubgraph:
    """Test the build_profile_and_subgraph convenience function."""

    def test_returns_tuple(self) -> None:
        result = build_profile_and_subgraph("default")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_default_returns_valid_profile_and_subgraph(self) -> None:
        profile, subgraph = build_profile_and_subgraph("default")
        assert isinstance(profile, UserProfile)
        assert isinstance(subgraph, UserSubgraph)
        assert profile.age == 40
        assert subgraph.user_id == profile.user_id

    def test_elderly_comorbid_has_anchored_categories(self) -> None:
        profile, subgraph = build_profile_and_subgraph("elderly_comorbid")
        assert isinstance(subgraph, UserSubgraph)
        assert len(subgraph.anchored_categories) > 0
        # The three conditions span three distinct categories
        expected_cats = {
            "cat:heart_blood_vessels",
            "cat:breathing_lungs",
            "cat:bones_joints_muscles",
        }
        assert expected_cats == set(subgraph.anchored_categories)

    def test_elderly_comorbid_has_edge_boosts(self) -> None:
        _, subgraph = build_profile_and_subgraph("elderly_comorbid")
        assert len(subgraph.edge_boosts) > 0

    def test_unknown_profile_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            build_profile_and_subgraph("nonexistent_profile")

    def test_base_graph_is_cached(self) -> None:
        """Calling build_profile_and_subgraph twice should reuse the same graph."""
        # Import the module to inspect the cache
        import simple_evals.agentic_medbench.profiles as profiles_mod

        # Build once to populate the cache
        build_profile_and_subgraph("default")
        cached_graph = profiles_mod._BASE_GRAPH_CACHE

        # Build again
        build_profile_and_subgraph("high_literacy_nurse")
        assert profiles_mod._BASE_GRAPH_CACHE is cached_graph
