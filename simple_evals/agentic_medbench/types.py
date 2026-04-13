"""Core data models for Agentic MedBench evaluation.

Defines the dataclasses that represent an agent's execution trace (tool calls,
reasoning steps, corrections, retrieval results) and the unified scoring
function that combines per-dimension scores into a single metric.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Dimension weights for the unified score
# ---------------------------------------------------------------------------

DIMENSION_WEIGHTS: dict[str, float] = {
    "answer_quality": 0.35,
    "tool_selection": 0.15,
    "retrieval_quality": 0.20,
    "reasoning_trace": 0.20,
    "self_correction": 0.10,
}


# ---------------------------------------------------------------------------
# Trace component dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ToolCall:
    """A single tool invocation recorded during agent execution."""

    tool_name: str
    arguments: dict[str, Any]
    result: str
    timestamp: float


@dataclass
class Correction:
    """A self-correction the agent made during reasoning."""

    original: str
    corrected: str
    reason: str


@dataclass
class RetrievalItem:
    """A single item returned by a retrieval step."""

    source: str
    content: str
    relevance_score: float


# ---------------------------------------------------------------------------
# Agent execution trace
# ---------------------------------------------------------------------------


@dataclass
class AgentTrace:
    """Full execution trace for an agent responding to a medical query.

    Captures the final answer together with all intermediate artefacts:
    tool calls, reasoning steps, self-corrections, and retrieved evidence.
    """

    final_answer: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)
    retrieval_results: list[RetrievalItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the trace to a plain dict (no dataclass instances)."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Unified scoring
# ---------------------------------------------------------------------------


def compute_unified_score(dimensions: dict[str, float]) -> float:
    """Compute a weighted unified score from per-dimension scores.

    Args:
        dimensions: Mapping of dimension name to its score (typically 0-1).
            Must contain exactly the keys defined in ``DIMENSION_WEIGHTS``.

    Returns:
        Weighted sum of dimension scores.

    Raises:
        ValueError: If ``dimensions`` keys do not match ``DIMENSION_WEIGHTS``.
    """
    expected_keys = set(DIMENSION_WEIGHTS.keys())
    provided_keys = set(dimensions.keys())

    if provided_keys != expected_keys:
        missing = expected_keys - provided_keys
        extra = provided_keys - expected_keys
        parts: list[str] = []
        if missing:
            parts.append(f"missing: {sorted(missing)}")
        if extra:
            parts.append(f"unexpected: {sorted(extra)}")
        raise ValueError(
            f"Dimension keys mismatch. {'; '.join(parts)}. "
            f"Expected exactly: {sorted(expected_keys)}"
        )

    return sum(
        dimensions[dim] * weight for dim, weight in DIMENSION_WEIGHTS.items()
    )
