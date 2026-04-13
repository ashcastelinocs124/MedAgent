"""Predefined user profile presets for Agentic MedBench evaluation.

Provides four user profiles that span different health literacy levels,
ages, and medical complexity.  Each can be paired with a UserSubgraph
built from the brain's base graph so that the evaluation matrix covers
personalisation behaviour.
"""

from __future__ import annotations

from typing import Optional

import networkx as nx

from src.personalization.base_graph import build_base_graph
from src.personalization.models import (
    Condition,
    HealthLiteracy,
    Medication,
    Sex,
    UserProfile,
)
from src.personalization.user_graph import UserSubgraph, UserSubgraphBuilder

# ---------------------------------------------------------------------------
# Profile presets
# ---------------------------------------------------------------------------

PROFILE_PRESETS: dict[str, UserProfile] = {
    "default": UserProfile(
        age=40,
        sex=Sex.PREFER_NOT_TO_SAY,
        health_literacy=HealthLiteracy.MEDIUM,
        conditions=[],
        medications=[],
    ),
    "low_literacy_patient": UserProfile(
        age=55,
        sex=Sex.MALE,
        health_literacy=HealthLiteracy.LOW,
        conditions=[
            Condition(
                name="Type 2 Diabetes",
                category_id="hormones_metabolism_nutrition",
                subcategory_id="diabetes_type_1_type_2_gestational",
            ),
            Condition(
                name="Hypertension",
                category_id="heart_blood_vessels",
                subcategory_id="hypertension_blood_pressure",
            ),
        ],
        medications=[
            Medication(
                name="Metformin",
                category_id="hormones_metabolism_nutrition",
            ),
            Medication(
                name="Lisinopril",
                category_id="heart_blood_vessels",
            ),
        ],
    ),
    "high_literacy_nurse": UserProfile(
        age=32,
        sex=Sex.FEMALE,
        health_literacy=HealthLiteracy.HIGH,
        conditions=[],
        medications=[],
    ),
    "elderly_comorbid": UserProfile(
        age=72,
        sex=Sex.MALE,
        health_literacy=HealthLiteracy.MEDIUM,
        conditions=[
            Condition(
                name="Congestive Heart Failure",
                category_id="heart_blood_vessels",
                subcategory_id="heart_failure",
            ),
            Condition(
                name="COPD",
                category_id="breathing_lungs",
                subcategory_id="copd",
            ),
            Condition(
                name="Arthritis",
                category_id="bones_joints_muscles",
                subcategory_id="arthritis_oa_ra",
            ),
        ],
        medications=[
            Medication(
                name="Furosemide",
                category_id="heart_blood_vessels",
            ),
            Medication(
                name="Albuterol",
                category_id="breathing_lungs",
            ),
            Medication(
                name="Ibuprofen",
                category_id="bones_joints_muscles",
            ),
        ],
    ),
}

# ---------------------------------------------------------------------------
# Cached base graph (built once, shared across all calls)
# ---------------------------------------------------------------------------

_BASE_GRAPH_CACHE: Optional[nx.DiGraph] = None


def _get_base_graph() -> nx.DiGraph:
    """Return the cached base graph, building it on first access."""
    global _BASE_GRAPH_CACHE  # noqa: PLW0603
    if _BASE_GRAPH_CACHE is None:
        _BASE_GRAPH_CACHE = build_base_graph()
    return _BASE_GRAPH_CACHE


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------


def build_profile_and_subgraph(
    profile_name: str,
) -> tuple[UserProfile, UserSubgraph]:
    """Look up a preset profile and build its personalised subgraph.

    Args:
        profile_name: Key into ``PROFILE_PRESETS``.

    Returns:
        A ``(UserProfile, UserSubgraph)`` pair ready for evaluation.

    Raises:
        KeyError: If *profile_name* is not a recognised preset.
    """
    profile = PROFILE_PRESETS[profile_name]
    base_graph = _get_base_graph()
    builder = UserSubgraphBuilder(base_graph)
    subgraph = builder.build(profile)
    return profile, subgraph
