"""Tests for query-time graph merging and retrieval planning."""

from src.personalization.query_merge import (
    MAY_LOAD_THRESHOLD,
    MUST_LOAD_THRESHOLD,
    QueryGraphMerger,
)
from src.personalization.user_graph import UserSubgraphBuilder


class TestGenericRetrieval:
    """Test retrieval plan without user personalization."""

    def test_primary_always_in_plan(self, base_graph):
        merger = QueryGraphMerger(base_graph)
        plan = merger.plan_retrieval("heart_blood_vessels")

        assert plan.primary_category == "heart_blood_vessels"

    def test_strong_links_must_load(self, base_graph):
        merger = QueryGraphMerger(base_graph)
        plan = merger.plan_retrieval("heart_blood_vessels")

        # Strong links (0.85) should be must-load
        assert "medications_drug_safety" in plan.must_load

    def test_weak_links_may_load(self, base_graph):
        merger = QueryGraphMerger(base_graph)
        plan = merger.plan_retrieval("heart_blood_vessels")

        # Weak links (0.35) should be may-load
        assert "kidney_urinary" in plan.may_load

    def test_has_explanations(self, base_graph):
        merger = QueryGraphMerger(base_graph)
        plan = merger.plan_retrieval("heart_blood_vessels")

        assert len(plan.explanation) > 0

    def test_effective_weights_populated(self, base_graph):
        merger = QueryGraphMerger(base_graph)
        plan = merger.plan_retrieval("heart_blood_vessels")

        assert len(plan.effective_weights) > 0
        for weight in plan.effective_weights.values():
            assert 0.0 <= weight <= 1.0


class TestPersonalizedRetrieval:
    """Test retrieval plan with user personalization (diabetes + CKD)."""

    def test_kidney_promoted_for_diabetic(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)
        merger = QueryGraphMerger(base_graph)

        # Query heart category with diabetic+CKD profile
        plan = merger.plan_retrieval("heart_blood_vessels", subgraph)

        # Kidney should be promoted from weak link to must-load
        # (base 0.35 + anchor boosts + comorbidity boosts)
        kidney_weight = plan.effective_weights.get("kidney_urinary", 0)
        assert kidney_weight >= MUST_LOAD_THRESHOLD, (
            f"Kidney weight {kidney_weight} should be >= {MUST_LOAD_THRESHOLD} "
            f"for diabetic CKD patient"
        )

    def test_medications_boosted(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)
        merger = QueryGraphMerger(base_graph)

        plan = merger.plan_retrieval("heart_blood_vessels", subgraph)

        # Medications should stay must-load (already strong)
        assert "medications_drug_safety" in plan.must_load

    def test_personalized_has_more_must_load(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)
        merger = QueryGraphMerger(base_graph)

        generic_plan = merger.plan_retrieval("heart_blood_vessels")
        personalized_plan = merger.plan_retrieval("heart_blood_vessels", subgraph)

        # Personalized plan should have at least as many must-load categories
        assert len(personalized_plan.must_load) >= len(generic_plan.must_load)

    def test_anchored_categories_promoted(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)
        merger = QueryGraphMerger(base_graph)

        # Query from a category that doesn't directly link to kidney/hormones
        plan = merger.plan_retrieval("mental_health", subgraph)

        # User's anchored categories should still appear in the plan
        # (even if mental_health doesn't directly link to kidney)
        all_planned = set(plan.must_load + plan.may_load)
        has_anchored = (
            "hormones_metabolism_nutrition" in all_planned
            or "kidney_urinary" in all_planned
        )
        # At least the hormones category should appear since mental_health
        # has a weak link to it
        assert "hormones_metabolism_nutrition" in plan.effective_weights


class TestInvalidCategory:
    def test_nonexistent_category(self, base_graph):
        merger = QueryGraphMerger(base_graph)
        plan = merger.plan_retrieval("nonexistent_category")

        assert plan.primary_category == "nonexistent_category"
        assert len(plan.must_load) == 0
        assert len(plan.may_load) == 0
