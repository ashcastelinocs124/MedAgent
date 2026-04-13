"""Query-time graph merger — the interface Agent B calls.

Combines the base graph with the user's subgraph overlay to produce a
RetrievalPlan that tells Agent B which categories to load.

Thresholds:
    >= 0.60  ->  must_load (always retrieved)
    >= 0.35  ->  may_load  (retrieved if budget allows)
    <  0.35  ->  skipped
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import networkx as nx

from src.personalization.user_graph import UserSubgraph
from src.personalization.weight_modifier import compute_effective_weight

MUST_LOAD_THRESHOLD = 0.60
MAY_LOAD_THRESHOLD = 0.35


@dataclass
class RetrievalPlan:
    """The output Agent B uses to decide which categories to load."""

    primary_category: str
    must_load: list[str] = field(default_factory=list)
    may_load: list[str] = field(default_factory=list)
    effective_weights: dict[str, float] = field(default_factory=dict)
    explanation: list[str] = field(default_factory=list)


class QueryGraphMerger:
    """Merges base graph + user subgraph at query time."""

    def __init__(self, base_graph: nx.DiGraph) -> None:
        self.base_graph = base_graph

    def plan_retrieval(
        self,
        primary_category_id: str,
        user_subgraph: Optional[UserSubgraph] = None,
        now: Optional[datetime] = None,
    ) -> RetrievalPlan:
        """Produce a RetrievalPlan for Agent B.

        Args:
            primary_category_id: The category Agent A classified the query into.
            user_subgraph: The user's personalization overlay (None = generic user).
            now: Current time for query-history decay (defaults to datetime.now()).

        Returns:
            RetrievalPlan with must_load, may_load, weights, and explanations.
        """
        if now is None:
            now = datetime.now()

        primary_node = f"cat:{primary_category_id}"
        plan = RetrievalPlan(primary_category=primary_category_id)
        plan.explanation.append(f"Primary category: {primary_category_id} (always loaded)")

        if primary_node not in self.base_graph:
            return plan

        # Collect effective weights for all outgoing category-level edges
        candidate_weights: dict[str, float] = {}

        for _, target, edge_data in self.base_graph.out_edges(primary_node, data=True):
            if not target.startswith("cat:"):
                continue  # skip parent->child edges to subcategories

            base_weight = edge_data["data"].base_weight

            # Gather profile boosts from user subgraph
            profile_boosts = []
            query_count = 0
            last_query_time = None

            if user_subgraph:
                # Forward boosts: primary -> target
                profile_boosts = user_subgraph.get_boosts_for_edge(
                    primary_node, target
                )
                # Reverse boosts: target -> primary (bidirectional relevance)
                reverse_boosts = user_subgraph.get_boosts_for_edge(
                    target, primary_node
                )
                profile_boosts = profile_boosts + reverse_boosts

                # Check query history
                edge_key = (primary_node, target)
                if edge_key in user_subgraph.query_counts:
                    record = user_subgraph.query_counts[edge_key]
                    query_count = record.count
                    last_query_time = record.last_used

            eff_weight = compute_effective_weight(
                base_weight, profile_boosts, query_count, last_query_time, now
            )
            target_cat_id = target.replace("cat:", "")
            candidate_weights[target_cat_id] = eff_weight

        # Check if user-anchored categories should be promoted
        # (categories the user has conditions in, even if not linked from primary)
        if user_subgraph:
            for anchored_cat in user_subgraph.anchored_categories:
                cat_id = anchored_cat.replace("cat:", "")
                if cat_id == primary_category_id:
                    continue
                if cat_id not in candidate_weights:
                    # This category isn't directly linked from primary —
                    # add it with a base weight of 0 plus user boosts
                    profile_boosts = user_subgraph.get_boosts_for_edge(
                        primary_node, anchored_cat
                    )
                    # Also check boosts from anchored category to primary
                    reverse_boosts = user_subgraph.get_boosts_for_edge(
                        anchored_cat, primary_node
                    )
                    all_boosts = profile_boosts + reverse_boosts

                    if all_boosts:
                        eff_weight = compute_effective_weight(0.0, all_boosts)
                        candidate_weights[cat_id] = eff_weight
                        plan.explanation.append(
                            f"Promoted {cat_id}: user has condition in this category "
                            f"(effective weight {eff_weight:.2f})"
                        )

        # Threshold into must_load and may_load
        for cat_id, weight in sorted(
            candidate_weights.items(), key=lambda x: x[1], reverse=True
        ):
            plan.effective_weights[cat_id] = weight
            if weight >= MUST_LOAD_THRESHOLD:
                plan.must_load.append(cat_id)
                plan.explanation.append(
                    f"Must-load {cat_id}: effective weight {weight:.2f}"
                )
            elif weight >= MAY_LOAD_THRESHOLD:
                plan.may_load.append(cat_id)
                plan.explanation.append(
                    f"May-load {cat_id}: effective weight {weight:.2f}"
                )

        return plan
