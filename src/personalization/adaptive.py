"""Adaptive learning from query history and profile updates.

Two evolution mechanisms:
    1. record_query: Increment counters on touched nodes, update timestamps.
       These feed into query-history boosts (time-decayed).
    2. recalculate_on_profile_update: Rebuild condition-based boosts while
       preserving query history state.

Decay is lazy — computed at query time from timestamps, not via background processes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.personalization.models import UserProfile
from src.personalization.user_graph import QueryRecord, UserSubgraph, UserSubgraphBuilder


class AdaptiveLearner:
    """Manages adaptive evolution of user subgraphs over time."""

    def __init__(self, builder: UserSubgraphBuilder) -> None:
        self.builder = builder

    def record_query(
        self,
        subgraph: UserSubgraph,
        touched_nodes: list[str],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a query event, updating counters on touched edges.

        For each pair of consecutive touched nodes, increments the query
        counter and updates the last-used timestamp. These counters drive
        the time-decayed query boost formula.

        Args:
            subgraph: The user's subgraph overlay to update in-place.
            touched_nodes: Ordered list of node IDs that were accessed
                           during this query (e.g., primary category + loaded categories).
            timestamp: When the query occurred (defaults to now).
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Update query counts for all edges between the primary node
        # and each subsequent touched node
        if len(touched_nodes) < 2:
            return

        primary = touched_nodes[0]
        for target in touched_nodes[1:]:
            edge_key = (primary, target)
            if edge_key not in subgraph.query_counts:
                subgraph.query_counts[edge_key] = QueryRecord()

            record = subgraph.query_counts[edge_key]
            record.count += 1
            record.last_used = timestamp

    def recalculate_on_profile_update(
        self,
        subgraph: UserSubgraph,
        new_profile: UserProfile,
    ) -> UserSubgraph:
        """Rebuild condition-based boosts from updated profile, preserving query history.

        When a user adds/removes conditions or medications, the profile-based
        boosts need to be recomputed from scratch. But query history (counters
        and timestamps) should be preserved since it reflects real usage patterns.

        Args:
            subgraph: The existing user subgraph with accumulated query history.
            new_profile: The updated user profile.

        Returns:
            A new UserSubgraph with fresh profile boosts and preserved query history.
        """
        # Preserve query history
        old_query_counts = subgraph.query_counts.copy()

        # Rebuild from updated profile
        new_subgraph = self.builder.build(new_profile)

        # Restore query history
        new_subgraph.query_counts = old_query_counts

        return new_subgraph
