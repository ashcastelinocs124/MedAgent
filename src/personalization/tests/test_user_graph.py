"""Tests for user subgraph building."""

from src.personalization.user_graph import UserSubgraphBuilder


class TestDiabeticCKDSubgraph:
    """Test subgraph for a 55-year-old male with diabetes + CKD."""

    def test_anchored_subcategories(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        assert "sub:hormones_metabolism_nutrition:diabetes_type_1_type_2_gestational" in subgraph.anchored_subcategories
        assert "sub:kidney_urinary:chronic_kidney_disease" in subgraph.anchored_subcategories

    def test_anchored_categories(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        assert "cat:hormones_metabolism_nutrition" in subgraph.anchored_categories
        assert "cat:kidney_urinary" in subgraph.anchored_categories

    def test_has_anchor_boosts(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        anchor_boosts = [eb for eb in subgraph.edge_boosts if eb.source_type == "anchor"]
        assert len(anchor_boosts) > 0

    def test_has_expand_boosts(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        expand_boosts = [eb for eb in subgraph.edge_boosts if eb.source_type == "expand"]
        assert len(expand_boosts) > 0

    def test_comorbidity_boosts_heart(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        # Diabetes + CKD should boost heart via comorbidity
        comorbidity_boosts = [
            eb for eb in subgraph.edge_boosts
            if eb.source_type == "comorbidity" and eb.target == "cat:heart_blood_vessels"
        ]
        assert len(comorbidity_boosts) > 0

    def test_comorbidity_boosts_eye(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        # Diabetes + CKD should boost eye health via comorbidity
        eye_boosts = [
            eb for eb in subgraph.edge_boosts
            if eb.source_type == "comorbidity" and eb.target == "cat:eye_health"
        ]
        assert len(eye_boosts) > 0

    def test_demographic_boosts(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        # Age 55 should trigger cancer screening and cardiovascular boosts
        demo_boosts = [eb for eb in subgraph.edge_boosts if eb.source_type == "demographic"]
        assert len(demo_boosts) > 0

        # Should include cancer (age 40+)
        cancer_demo = [eb for eb in demo_boosts if eb.target == "cat:cancer"]
        assert len(cancer_demo) > 0

    def test_medication_boosts(self, base_graph, diabetic_ckd_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(diabetic_ckd_profile)

        med_boosts = [eb for eb in subgraph.edge_boosts if eb.source_type == "medication"]
        assert len(med_boosts) > 0

        # Lisinopril (heart category) should boost medications_drug_safety
        meds_safety_boosts = [
            eb for eb in med_boosts if eb.target == "cat:medications_drug_safety"
        ]
        assert len(meds_safety_boosts) > 0


class TestYoungFemaleSubgraph:
    """Test subgraph for a 25-year-old female with anxiety."""

    def test_sex_boosts(self, base_graph, young_female_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(young_female_profile)

        # Female should get womens_reproductive boost
        sex_boosts = [
            eb for eb in subgraph.edge_boosts
            if eb.source_type == "demographic" and eb.target == "cat:womens_reproductive"
        ]
        assert len(sex_boosts) > 0

    def test_no_age_cancer_boost(self, base_graph, young_female_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(young_female_profile)

        # Age 25 should NOT trigger cancer screening boost
        cancer_demo = [
            eb for eb in subgraph.edge_boosts
            if eb.source_type == "demographic" and eb.target == "cat:cancer"
        ]
        assert len(cancer_demo) == 0


class TestGenericSubgraph:
    """Test subgraph for a user with no conditions."""

    def test_no_anchor_boosts(self, base_graph, generic_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(generic_profile)

        anchor_boosts = [eb for eb in subgraph.edge_boosts if eb.source_type == "anchor"]
        assert len(anchor_boosts) == 0

    def test_no_comorbidity_boosts(self, base_graph, generic_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(generic_profile)

        comorbidity_boosts = [
            eb for eb in subgraph.edge_boosts if eb.source_type == "comorbidity"
        ]
        assert len(comorbidity_boosts) == 0

    def test_no_medication_boosts(self, base_graph, generic_profile):
        builder = UserSubgraphBuilder(base_graph)
        subgraph = builder.build(generic_profile)

        med_boosts = [eb for eb in subgraph.edge_boosts if eb.source_type == "medication"]
        assert len(med_boosts) == 0
