"""Tests for edge weight modification math."""

import math
from datetime import datetime, timedelta

from src.personalization.weight_modifier import (
    MAX_BOOST,
    MAX_QUERY_BOOST,
    compute_effective_weight,
    query_decay_boost,
    soft_cap_boost,
)


class TestSoftCapBoost:
    def test_zero_input(self):
        assert soft_cap_boost(0.0) == 0.0

    def test_negative_input(self):
        assert soft_cap_boost(-0.5) == 0.0

    def test_small_boost(self):
        result = soft_cap_boost(0.10)
        # Small inputs should pass through nearly linearly
        assert 0.08 < result < 0.12

    def test_large_boost_caps(self):
        result = soft_cap_boost(2.0)
        assert result < MAX_BOOST
        assert result > 0.39  # very close to cap

    def test_approaches_max(self):
        result = soft_cap_boost(10.0)
        assert abs(result - MAX_BOOST) < 0.001

    def test_monotonically_increasing(self):
        values = [soft_cap_boost(x * 0.1) for x in range(20)]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1]

    def test_diminishing_returns(self):
        # First 0.2 of input should give more boost than second 0.2
        first = soft_cap_boost(0.2)
        second = soft_cap_boost(0.4) - first
        assert first > second


class TestQueryDecayBoost:
    def test_zero_count(self):
        assert query_decay_boost(0, 0.0) == 0.0

    def test_negative_count(self):
        assert query_decay_boost(-1, 0.0) == 0.0

    def test_fresh_query(self):
        # 5 queries just now -> 5 * 0.02 = 0.10
        assert abs(query_decay_boost(5, 0.0) - 0.10) < 0.001

    def test_half_life_decay(self):
        # After 90 days, boost should halve
        fresh = query_decay_boost(5, 0.0)
        decayed = query_decay_boost(5, 90.0)
        assert abs(decayed - fresh / 2) < 0.001

    def test_cap(self):
        # Even many queries should cap at MAX_QUERY_BOOST
        result = query_decay_boost(100, 0.0)
        assert result == MAX_QUERY_BOOST

    def test_old_query_near_zero(self):
        # After 360 days (4 half-lives), boost should be ~1/16 of original
        result = query_decay_boost(5, 360.0)
        assert result < 0.01


class TestComputeEffectiveWeight:
    def test_no_boosts(self):
        result = compute_effective_weight(0.85, [])
        assert result == 0.85

    def test_single_boost(self):
        result = compute_effective_weight(0.35, [0.25])
        expected = 0.35 + soft_cap_boost(0.25)
        assert abs(result - expected) < 0.001

    def test_multiple_boosts(self):
        result = compute_effective_weight(0.35, [0.25, 0.15, 0.10])
        expected = 0.35 + soft_cap_boost(0.50)
        assert abs(result - expected) < 0.001

    def test_caps_at_one(self):
        result = compute_effective_weight(0.85, [0.30, 0.30, 0.30])
        assert result == 1.0

    def test_with_query_boost(self):
        now = datetime.now()
        result = compute_effective_weight(
            0.35,
            [0.10],
            query_count=5,
            last_query_time=now,
            now=now,
        )
        profile_boost = soft_cap_boost(0.10)
        query_boost = query_decay_boost(5, 0.0)
        expected = min(0.35 + profile_boost + query_boost, 1.0)
        assert abs(result - expected) < 0.001

    def test_no_query_without_timestamp(self):
        result = compute_effective_weight(0.35, [], query_count=5)
        assert result == 0.35  # No last_query_time, so no query boost

    def test_zero_base_with_boosts(self):
        result = compute_effective_weight(0.0, [0.30])
        assert result > 0.0
        assert result < MAX_BOOST
