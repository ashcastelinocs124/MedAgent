"""Shared fixtures for personalization tests."""

from __future__ import annotations

from datetime import date

import pytest

from src.personalization.base_graph import build_base_graph
from src.personalization.models import (
    Condition,
    HealthLiteracy,
    Medication,
    Sex,
    UserProfile,
)
from src.personalization.user_graph import UserSubgraphBuilder


@pytest.fixture(scope="session")
def base_graph():
    """Build the base graph once for the entire test session."""
    return build_base_graph()


@pytest.fixture
def builder(base_graph):
    """Create a UserSubgraphBuilder with the base graph."""
    return UserSubgraphBuilder(base_graph)


@pytest.fixture
def diabetic_ckd_profile() -> UserProfile:
    """A 55-year-old male with Type 2 Diabetes and CKD."""
    return UserProfile(
        user_id="test-diabetes-ckd",
        age=55,
        sex=Sex.MALE,
        health_literacy=HealthLiteracy.MEDIUM,
        conditions=[
            Condition(
                name="Type 2 Diabetes",
                category_id="hormones_metabolism_nutrition",
                subcategory_id="diabetes_type_1_type_2_gestational",
                icd10_code="E11",
                diagnosed_date=date(2020, 3, 15),
                active=True,
            ),
            Condition(
                name="Chronic Kidney Disease",
                category_id="kidney_urinary",
                subcategory_id="chronic_kidney_disease",
                icd10_code="N18",
                diagnosed_date=date(2022, 7, 1),
                active=True,
            ),
        ],
        medications=[
            Medication(
                name="Metformin",
                category_id="hormones_metabolism_nutrition",
                related_condition="Type 2 Diabetes",
            ),
            Medication(
                name="Lisinopril",
                category_id="heart_blood_vessels",
                related_condition="Chronic Kidney Disease",
            ),
        ],
    )


@pytest.fixture
def young_female_profile() -> UserProfile:
    """A 25-year-old female with anxiety."""
    return UserProfile(
        user_id="test-young-female",
        age=25,
        sex=Sex.FEMALE,
        health_literacy=HealthLiteracy.HIGH,
        conditions=[
            Condition(
                name="Generalized Anxiety",
                category_id="mental_health",
                subcategory_id="anxiety_ocd",
                active=True,
            ),
        ],
        medications=[
            Medication(
                name="Sertraline",
                category_id="mental_health",
                related_condition="Generalized Anxiety",
            ),
        ],
    )


@pytest.fixture
def generic_profile() -> UserProfile:
    """A user with no conditions or medications."""
    return UserProfile(
        user_id="test-generic",
        age=30,
        sex=Sex.PREFER_NOT_TO_SAY,
    )
