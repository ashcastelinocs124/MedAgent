"""Edge weight modification math for the user subgraph overlay.

Pure math module — depends only on numeric inputs, no graph or profile objects.

Formulas:
    Profile boost (soft-cap):
        boost = MAX_BOOST * (1 - e^(-raw_sum / MAX_BOOST))
        MAX_BOOST = 0.40

    Query-history boost (time-decay):
        boost = count * 0.02 * 0.5^(days_elapsed / 90)
        Capped at 0.15

    Effective weight:
        min(base_weight + profile_boost + query_boost, 1.0)
"""

from __future__ import annotations

import math
from datetime import datetime

MAX_BOOST = 0.40
MAX_QUERY_BOOST = 0.15
QUERY_BOOST_PER_HIT = 0.02
QUERY_HALF_LIFE_DAYS = 90


def soft_cap_boost(raw_sum: float) -> float:
    """Apply soft-cap to accumulated profile boosts.

    Uses the formula: MAX_BOOST * (1 - e^(-raw_sum / MAX_BOOST))

    This prevents runaway accumulation while allowing multiple boost
    sources to combine with diminishing returns.

    Args:
        raw_sum: Sum of all raw boosts from profile sources
                 (anchor + expand + comorbidity + demographic + medication).

    Returns:
        Capped boost value in [0, MAX_BOOST).
    """
    if raw_sum <= 0:
        return 0.0
    return MAX_BOOST * (1 - math.exp(-raw_sum / MAX_BOOST))


def query_decay_boost(count: int, days_elapsed: float) -> float:
    """Compute query-history boost with exponential time decay.

    Uses the formula: count * 0.02 * 0.5^(days_elapsed / 90)

    Recent queries matter more; boosts halve every 90 days.
    Capped at MAX_QUERY_BOOST (0.15).

    Args:
        count: Number of times this edge was touched by queries.
        days_elapsed: Days since the most recent query touching this edge.

    Returns:
        Query boost value in [0, MAX_QUERY_BOOST].
    """
    if count <= 0 or days_elapsed < 0:
        return 0.0
    raw = count * QUERY_BOOST_PER_HIT * (0.5 ** (days_elapsed / QUERY_HALF_LIFE_DAYS))
    return min(raw, MAX_QUERY_BOOST)


def compute_effective_weight(
    base_weight: float,
    profile_boosts: list[float],
    query_count: int = 0,
    last_query_time: datetime | None = None,
    now: datetime | None = None,
) -> float:
    """Compute the effective edge weight combining base + profile + query boosts.

    Args:
        base_weight: Original edge weight from the base graph.
        profile_boosts: List of raw boost values from profile sources.
        query_count: Number of past queries that touched this edge.
        last_query_time: Timestamp of the most recent query on this edge.
        now: Current time (defaults to datetime.now()).

    Returns:
        Effective weight clamped to [0.0, 1.0].
    """
    # Profile boost with soft-cap
    raw_sum = sum(b for b in profile_boosts if b > 0)
    profile_boost = soft_cap_boost(raw_sum)

    # Query-history boost with time decay
    query_boost = 0.0
    if query_count > 0 and last_query_time is not None:
        if now is None:
            now = datetime.now()
        days_elapsed = max(0.0, (now - last_query_time).total_seconds() / 86400)
        query_boost = query_decay_boost(query_count, days_elapsed)

    return min(base_weight + profile_boost + query_boost, 1.0)
