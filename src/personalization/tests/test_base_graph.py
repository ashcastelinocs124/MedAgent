"""Tests for base graph construction from brain markdown files."""

from src.personalization.base_graph import (
    get_category_nodes,
    get_subcategory_nodes,
    get_subcategories_for_category,
    slugify,
)


class TestSlugify:
    def test_simple(self):
        assert slugify("Heart & Blood Vessels") == "heart_blood_vessels"

    def test_parenthetical(self):
        result = slugify("Diabetes (Type 1, Type 2, Gestational)")
        assert result == "diabetes_type_1_type_2_gestational"

    def test_slash(self):
        result = slugify("Nephrotic / Nephritic Syndrome")
        assert result == "nephrotic_nephritic_syndrome"

    def test_ampersand(self):
        assert slugify("Bones, Joints & Muscles") == "bones_joints_muscles"

    def test_apostrophe(self):
        result = slugify("Cushing's Syndrome")
        assert result == "cushings_syndrome"


class TestBaseGraph:
    def test_category_count(self, base_graph):
        cats = get_category_nodes(base_graph)
        assert len(cats) == 20

    def test_subcategory_count(self, base_graph):
        subs = get_subcategory_nodes(base_graph)
        assert len(subs) == 175

    def test_total_nodes(self, base_graph):
        assert base_graph.number_of_nodes() == 195

    def test_has_edges(self, base_graph):
        assert base_graph.number_of_edges() > 400

    def test_heart_category_exists(self, base_graph):
        assert "cat:heart_blood_vessels" in base_graph

    def test_heart_has_subcategories(self, base_graph):
        subs = get_subcategories_for_category(base_graph, "heart_blood_vessels")
        assert len(subs) == 8
        assert "sub:heart_blood_vessels:hypertension_blood_pressure" in subs

    def test_strong_link_weight(self, base_graph):
        edge_data = base_graph["cat:heart_blood_vessels"]["cat:medications_drug_safety"]["data"]
        assert edge_data.edge_type == "strong"
        assert edge_data.base_weight == 0.85

    def test_weak_link_weight(self, base_graph):
        edge_data = base_graph["cat:heart_blood_vessels"]["cat:kidney_urinary"]["data"]
        assert edge_data.edge_type == "weak"
        assert edge_data.base_weight == 0.35

    def test_related_link_exists(self, base_graph):
        # Hypertension subcategory has a Related link to kidney_urinary
        sub_node = "sub:heart_blood_vessels:hypertension_blood_pressure"
        assert base_graph.has_edge(sub_node, "cat:kidney_urinary")
        edge_data = base_graph[sub_node]["cat:kidney_urinary"]["data"]
        assert edge_data.edge_type == "related"
        assert edge_data.base_weight == 0.60

    def test_parent_child_edges(self, base_graph):
        # Category -> subcategory edge exists
        assert base_graph.has_edge(
            "cat:heart_blood_vessels",
            "sub:heart_blood_vessels:hypertension_blood_pressure",
        )
        # Subcategory -> category edge exists (bidirectional)
        assert base_graph.has_edge(
            "sub:heart_blood_vessels:hypertension_blood_pressure",
            "cat:heart_blood_vessels",
        )

    def test_all_categories_have_subcategories(self, base_graph):
        for cat_node in get_category_nodes(base_graph):
            cat_id = cat_node.replace("cat:", "")
            subs = get_subcategories_for_category(base_graph, cat_id)
            assert len(subs) >= 7, f"{cat_node} has only {len(subs)} subcategories"

    def test_node_data_attributes(self, base_graph):
        node_data = base_graph.nodes["cat:heart_blood_vessels"]["data"]
        assert node_data.node_type == "category"
        assert node_data.category_id == "heart_blood_vessels"
        assert node_data.display_name == "Heart & Blood Vessels"
        assert len(node_data.subcategories) == 8
