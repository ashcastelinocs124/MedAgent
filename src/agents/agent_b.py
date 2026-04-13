# src/agents/agent_b.py
"""Retrieval Planning Agent (Agent B).

Consumes the QueryContext produced by Agent A and:
1. Builds a per-user subgraph overlay via UserSubgraphBuilder.
2. Calls QueryGraphMerger.plan_retrieval() to get a RetrievalPlan.
3. Assembles brain_context by loading the primary category file, any
   may_load category files (within a token budget), and general_rules.md.

All three outputs (user_subgraph, retrieval_plan, brain_context) are written
back onto the QueryContext and returned.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.personalization.user_graph import UserSubgraphBuilder
    from src.personalization.query_merge import QueryGraphMerger
    from src.personalization.user_memory import UserMemoryStore

from src.agents.context import QueryContext

_TOKEN_BUDGET_CHARS = 32_000   # ~8000 tokens × 4 chars/token
_GENERAL_RULES_FILE = "general_rules.md"


class RetrievalPlanningAgent:
    """Agent B — Retrieval Planning.

    Args:
        builder: A UserSubgraphBuilder pre-loaded with the shared base graph.
        merger: A QueryGraphMerger pre-loaded with the shared base graph.
        brain_dir: Path to the brain/ directory (default: "brain", relative to
            the working directory at call time, or an absolute path).
        memory_store: Optional UserMemoryStore for injecting short-term memory
            boosts and graduated permanent weight adjustments.
    """

    _MEMORY_BOOST = 0.10  # temporary boost per short-term memory fact

    def __init__(
        self,
        builder: "UserSubgraphBuilder",
        merger: "QueryGraphMerger",
        brain_dir: str = "brain",
        memory_store: "UserMemoryStore | None" = None,
    ) -> None:
        self._builder = builder
        self._merger = merger
        self._brain_dir = Path(brain_dir)
        self._memory_store = memory_store
        self._general_rules: str = self._load_file(self._brain_dir / _GENERAL_RULES_FILE)

    # ── private helpers ────────────────────────────────────────────────────────

    def _load_file(self, path: Path) -> str:
        """Read a file to a string; return empty string if not found."""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _load_category_file(self, slug: str) -> str:
        """Load a brain category file by its slug."""
        return self._load_file(self._brain_dir / "categories" / f"{slug}.md")

    def _compute_memory_boosts(self, facts: list[dict]) -> dict[str, float]:
        """Compute category boosts from short-term memory facts.

        Each novel fact contributes ``_MEMORY_BOOST`` to its category.
        Multiple facts in the same category accumulate additively.

        Args:
            facts: List of novel fact dicts (each has a ``category`` key).

        Returns:
            Dict mapping category slugs to cumulative boost values.
        """
        boosts: dict[str, float] = {}
        for fact in facts:
            cat = fact.get("category", "")
            if cat:
                boosts[cat] = boosts.get(cat, 0.0) + self._MEMORY_BOOST
        return boosts

    def _apply_graduated_weights(self, ctx: QueryContext, graduated: list[dict]) -> None:
        """Apply permanent weight adjustments from graduated memory facts.

        Graduated facts represent strongly established user context and receive
        a larger boost (0.15) than temporary short-term facts.  Weights are
        clamped to [0, 0.95].

        Args:
            ctx: The current QueryContext (must have ``retrieval_plan`` set).
            graduated: List of graduated fact dicts (each has a ``category`` key).
        """
        retrieval_plan = ctx.retrieval_plan
        current_weights = getattr(retrieval_plan, "effective_weights", {}) or {}
        for fact in graduated:
            cat = fact.get("category", "")
            if cat:
                current_weights[cat] = min(
                    current_weights.get(cat, 0.3) + 0.15, 0.95
                )
        retrieval_plan.effective_weights = current_weights

    # ── public interface ───────────────────────────────────────────────────────

    async def run(
        self,
        ctx: QueryContext,
        weight_overrides: dict[str, float] | None = None,
    ) -> QueryContext:
        """Execute retrieval planning and populate ctx in-place.

        Sets:
            ctx.user_subgraph  — UserSubgraph built from ctx.user_profile
            ctx.retrieval_plan — RetrievalPlan from QueryGraphMerger
            ctx.brain_context  — Assembled markdown context (≤ _TOKEN_BUDGET_CHARS)

        Args:
            ctx: QueryContext with ctx.category and ctx.user_profile already set
                 (populated by Agent A).
            weight_overrides: Optional dict mapping category slugs to pre-computed
                weights (0.0–1.0). When provided, these replace the merger's
                effective_weights and re-threshold must_load/may_load.

        Returns:
            The same QueryContext with Agent B fields populated.
        """
        # Stage 1: build personalised user subgraph
        user_subgraph = self._builder.build(ctx.user_profile)
        ctx.user_subgraph = user_subgraph

        # Stage 2: produce retrieval plan
        retrieval_plan = self._merger.plan_retrieval(
            primary_category_id=ctx.category,
            user_subgraph=user_subgraph,
        )
        ctx.retrieval_plan = retrieval_plan

        # Apply LLM-adjusted weight overrides if provided
        if weight_overrides:
            retrieval_plan.effective_weights = weight_overrides
            retrieval_plan.must_load = [
                c for c, w in weight_overrides.items() if w >= 0.60
            ]
            retrieval_plan.may_load = [
                c for c, w in weight_overrides.items() if 0.35 <= w < 0.60
            ]

        # Stage 2b: Inject temporary boosts from user short-term memory
        if self._memory_store is not None and ctx.user_profile:
            user_id = getattr(ctx.user_profile, "user_id", None)
            if user_id:
                profile_conditions = [
                    c.name for c in (ctx.user_profile.conditions or [])
                ]
                profile_medications = [
                    m.name for m in (ctx.user_profile.medications or [])
                ]
                novel_facts = self._memory_store.get_novel_facts(
                    user_id, profile_conditions, profile_medications,
                )
                if novel_facts:
                    memory_boosts = self._compute_memory_boosts(novel_facts)
                    current_weights = (
                        getattr(retrieval_plan, "effective_weights", {}) or {}
                    )
                    for cat, boost in memory_boosts.items():
                        current_weights[cat] = min(
                            current_weights.get(cat, 0.3) + boost, 0.95
                        )
                    retrieval_plan.effective_weights = current_weights

                # Check for graduated facts -> permanent graph changes
                graduated = self._memory_store.get_graduated(user_id)
                if graduated:
                    self._apply_graduated_weights(ctx, graduated)

        # Stage 3: assemble brain_context within token budget
        primary_content = self._load_category_file(ctx.category or "")
        budget = _TOKEN_BUDGET_CHARS
        sections: list[str] = []

        # 3a. Primary category file — always included first
        if primary_content:
            chunk = primary_content[:budget]
            sections.append(chunk)
            budget -= len(chunk)

        # 3b. may_load category files — included if budget allows
        may_load: list[str] = getattr(retrieval_plan, "may_load", None) or []
        for cat_id in may_load:
            if budget <= 0:
                break
            content = self._load_category_file(cat_id)
            if content:
                chunk = content[:budget]
                sections.append(chunk)
                budget -= len(chunk)

        # 3c. General rules — appended last, truncated to remaining budget
        if budget > 0 and self._general_rules:
            sections.append(self._general_rules[:budget])

        ctx.brain_context = "\n\n---\n\n".join(sections)
        return ctx
