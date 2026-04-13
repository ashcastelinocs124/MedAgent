"""User subgraph builder — the core personalization engine.

Builds a per-user overlay of EdgeBoost objects that modify base graph weights.
Uses a 5-stage pipeline:
    1. Anchor:      Map conditions -> subcategory nodes       (+0.25-0.30)
    2. Expand:      Follow Related links from anchored subs   (+0.15)
    3. Comorbidity: Known condition pair interactions          (+0.10-0.20)
    4. Demographic: Age-range and sex-based boosts            (+0.05-0.15)
    5. Medication:  Boost medications category + related cats  (+0.05-0.10)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import networkx as nx

from src.personalization.models import Condition, Sex, UserProfile


@dataclass
class EdgeBoost:
    """A single boost applied to a graph edge."""

    source: str  # source node ID
    target: str  # target node ID
    boost: float
    reason: str
    source_type: str  # "anchor", "expand", "comorbidity", "demographic", "medication"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QueryRecord:
    """Tracks query history for a specific edge."""

    count: int = 0
    last_used: Optional[datetime] = None


@dataclass
class UserSubgraph:
    """Per-user subgraph overlay containing edge boosts and query history."""

    user_id: str
    edge_boosts: list[EdgeBoost] = field(default_factory=list)
    query_counts: dict[tuple[str, str], QueryRecord] = field(default_factory=dict)
    anchored_subcategories: list[str] = field(default_factory=list)
    anchored_categories: list[str] = field(default_factory=list)
    built_at: Optional[datetime] = None

    def get_boosts_for_edge(self, source: str, target: str) -> list[float]:
        """Return all boost values for a specific edge."""
        return [
            eb.boost
            for eb in self.edge_boosts
            if eb.source == source and eb.target == target
        ]


# ─── Static tables ────────────────────────────────────────────────────────────

# Known comorbidity pairs: (condition_category_A, condition_category_B) -> list of
# (boosted_source, boosted_target, boost_value, reason)
COMORBIDITY_PAIRS: dict[frozenset[str], list[tuple[str, str, float, str]]] = {
    frozenset({"hormones_metabolism_nutrition", "kidney_urinary"}): [
        ("cat:hormones_metabolism_nutrition", "cat:heart_blood_vessels", 0.20,
         "Diabetes + CKD greatly increases cardiovascular risk"),
        ("cat:kidney_urinary", "cat:heart_blood_vessels", 0.20,
         "CKD + diabetes -> cardiorenal syndrome risk"),
        ("cat:hormones_metabolism_nutrition", "cat:eye_health", 0.15,
         "Diabetic retinopathy risk elevated with CKD"),
    ],
    frozenset({"hormones_metabolism_nutrition", "heart_blood_vessels"}): [
        ("cat:hormones_metabolism_nutrition", "cat:kidney_urinary", 0.15,
         "Diabetes + CVD increases CKD risk"),
        ("cat:heart_blood_vessels", "cat:kidney_urinary", 0.15,
         "Cardiovascular disease + diabetes -> renal monitoring"),
    ],
    frozenset({"heart_blood_vessels", "kidney_urinary"}): [
        ("cat:heart_blood_vessels", "cat:hormones_metabolism_nutrition", 0.15,
         "Cardiorenal syndrome -> monitor metabolic status"),
        ("cat:kidney_urinary", "cat:medications_drug_safety", 0.15,
         "CKD + CVD -> complex drug dosing"),
    ],
    frozenset({"mental_health", "hormones_metabolism_nutrition"}): [
        ("cat:mental_health", "cat:hormones_metabolism_nutrition", 0.10,
         "Depression-diabetes bidirectional relationship"),
        ("cat:hormones_metabolism_nutrition", "cat:mental_health", 0.10,
         "Thyroid disorders cause psychiatric symptoms"),
    ],
    frozenset({"breathing_lungs", "heart_blood_vessels"}): [
        ("cat:breathing_lungs", "cat:heart_blood_vessels", 0.15,
         "COPD + CVD -> pulmonary hypertension risk"),
        ("cat:heart_blood_vessels", "cat:breathing_lungs", 0.15,
         "Heart failure -> pulmonary edema monitoring"),
    ],
    frozenset({"cancer", "blood_immune"}): [
        ("cat:cancer", "cat:blood_immune", 0.15,
         "Cancer treatment affects immune/blood system"),
        ("cat:blood_immune", "cat:cancer", 0.15,
         "Hematologic conditions -> cancer screening"),
    ],
}

# Age-range -> category boosts
AGE_BOOSTS: list[tuple[range, str, float, str]] = [
    (range(0, 18), "cat:childrens_health", 0.15, "Pediatric age range"),
    (range(0, 18), "cat:public_health_prevention", 0.10, "Vaccination schedule"),
    (range(40, 200), "cat:cancer", 0.10, "Age-related cancer screening"),
    (range(50, 200), "cat:heart_blood_vessels", 0.10, "Cardiovascular risk increases with age"),
    (range(50, 200), "cat:bones_joints_muscles", 0.10, "Osteoporosis and arthritis risk"),
    (range(50, 200), "cat:eye_health", 0.05, "Age-related eye conditions"),
    (range(60, 200), "cat:brain_nervous_system", 0.10, "Neurodegenerative disease risk"),
    (range(60, 200), "cat:kidney_urinary", 0.05, "Renal function decline with age"),
]

# Sex-based category boosts
SEX_BOOSTS: dict[Sex, list[tuple[str, float, str]]] = {
    Sex.FEMALE: [
        ("cat:womens_reproductive", 0.15, "Female reproductive health"),
        ("cat:bones_joints_muscles", 0.05, "Higher osteoporosis risk in women"),
    ],
    Sex.MALE: [
        ("cat:kidney_urinary", 0.05, "Prostate health awareness"),
    ],
}


class UserSubgraphBuilder:
    """Builds a UserSubgraph from a UserProfile and the base graph."""

    def __init__(self, base_graph: nx.DiGraph) -> None:
        self.base_graph = base_graph

    def build(self, profile: UserProfile) -> UserSubgraph:
        """Build a complete user subgraph overlay via the 5-stage pipeline."""
        subgraph = UserSubgraph(
            user_id=profile.user_id,
            built_at=datetime.now(),
        )

        self._stage_anchor(profile, subgraph)
        self._stage_expand(profile, subgraph)
        self._stage_comorbidity(profile, subgraph)
        self._stage_demographic(profile, subgraph)
        self._stage_medication(profile, subgraph)

        return subgraph

    def _stage_anchor(self, profile: UserProfile, subgraph: UserSubgraph) -> None:
        """Stage 1: Map conditions to subcategory nodes, boost +0.25-0.30."""
        for condition in profile.conditions:
            if not condition.active:
                continue

            sub_node = f"sub:{condition.category_id}:{condition.subcategory_id}"
            cat_node = f"cat:{condition.category_id}"

            if sub_node not in self.base_graph:
                continue

            subgraph.anchored_subcategories.append(sub_node)
            if cat_node not in subgraph.anchored_categories:
                subgraph.anchored_categories.append(cat_node)

            # Boost all edges FROM this subcategory's parent category
            for _, target, edge_data in self.base_graph.out_edges(cat_node, data=True):
                if target.startswith("sub:"):
                    continue  # skip parent->child edges
                boost_val = 0.30 if edge_data["data"].edge_type == "strong" else 0.25
                subgraph.edge_boosts.append(EdgeBoost(
                    source=cat_node,
                    target=target,
                    boost=boost_val,
                    reason=f"User has {condition.name} in {condition.category_id}",
                    source_type="anchor",
                ))

    def _stage_expand(self, profile: UserProfile, subgraph: UserSubgraph) -> None:
        """Stage 2: Follow Related links from anchored subcategories, boost +0.15."""
        for sub_node in subgraph.anchored_subcategories:
            for _, target, edge_data in self.base_graph.out_edges(sub_node, data=True):
                if edge_data["data"].edge_type != "related":
                    continue

                subgraph.edge_boosts.append(EdgeBoost(
                    source=sub_node,
                    target=target,
                    boost=0.15,
                    reason=f"Related link from anchored subcategory {sub_node}",
                    source_type="expand",
                ))

    def _stage_comorbidity(
        self, profile: UserProfile, subgraph: UserSubgraph
    ) -> None:
        """Stage 3: Look up condition pairs in static table, boost +0.10-0.20."""
        active_cats = set()
        for c in profile.conditions:
            if c.active:
                active_cats.add(c.category_id)

        # Check every pair of active condition categories
        cat_list = sorted(active_cats)
        for i in range(len(cat_list)):
            for j in range(i + 1, len(cat_list)):
                pair = frozenset({cat_list[i], cat_list[j]})
                if pair in COMORBIDITY_PAIRS:
                    for source, target, boost_val, reason in COMORBIDITY_PAIRS[pair]:
                        if source in self.base_graph and target in self.base_graph:
                            subgraph.edge_boosts.append(EdgeBoost(
                                source=source,
                                target=target,
                                boost=boost_val,
                                reason=reason,
                                source_type="comorbidity",
                            ))

    def _stage_demographic(
        self, profile: UserProfile, subgraph: UserSubgraph
    ) -> None:
        """Stage 4: Age-range and sex-based category boosts, +0.05-0.15."""
        if profile.age is not None:
            for age_range, target, boost_val, reason in AGE_BOOSTS:
                if profile.age in age_range and target in self.base_graph:
                    # Boost from every anchored category to this target
                    # If no anchored categories, boost from all categories
                    sources = subgraph.anchored_categories or [
                        n for n in self.base_graph.nodes if n.startswith("cat:")
                    ]
                    for source in sources:
                        if source != target:
                            subgraph.edge_boosts.append(EdgeBoost(
                                source=source,
                                target=target,
                                boost=boost_val,
                                reason=f"{reason} (age {profile.age})",
                                source_type="demographic",
                            ))

        if profile.sex in SEX_BOOSTS:
            for target, boost_val, reason in SEX_BOOSTS[profile.sex]:
                if target in self.base_graph:
                    sources = subgraph.anchored_categories or [
                        n for n in self.base_graph.nodes if n.startswith("cat:")
                    ]
                    for source in sources:
                        if source != target:
                            subgraph.edge_boosts.append(EdgeBoost(
                                source=source,
                                target=target,
                                boost=boost_val,
                                reason=reason,
                                source_type="demographic",
                            ))

    def _stage_medication(
        self, profile: UserProfile, subgraph: UserSubgraph
    ) -> None:
        """Stage 5: Boost medications_drug_safety + related condition categories."""
        if not profile.medications:
            return

        meds_node = "cat:medications_drug_safety"
        if meds_node not in self.base_graph:
            return

        for med in profile.medications:
            # Each medication boosts medications_drug_safety from its condition's category
            med_cat_node = f"cat:{med.category_id}"
            if med_cat_node in self.base_graph and med_cat_node != meds_node:
                subgraph.edge_boosts.append(EdgeBoost(
                    source=med_cat_node,
                    target=meds_node,
                    boost=0.10,
                    reason=f"User takes {med.name} ({med.category_id})",
                    source_type="medication",
                ))

            # Also boost the condition category from medications
            if med_cat_node in self.base_graph and med_cat_node != meds_node:
                subgraph.edge_boosts.append(EdgeBoost(
                    source=meds_node,
                    target=med_cat_node,
                    boost=0.05,
                    reason=f"Medication {med.name} relates to {med.category_id}",
                    source_type="medication",
                ))
