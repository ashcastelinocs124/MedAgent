# src/pipeline.py
"""Pipeline Orchestrator — wires all four agents together.

Instantiate once at application startup; call ``run()`` per query.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2
    from openai import OpenAI

from src.agents.context import QueryContext, PipelineResult
from src.agents.agent_a import QueryUnderstandingAgent
from src.agents.agent_b import RetrievalPlanningAgent
from src.agents.agent_c import SynthesisAgent
from src.agents.agent_d import VerificationAgent
from src.search.hybrid import HybridSearcher
from src.personalization.base_graph import build_base_graph
from src.personalization.user_graph import UserSubgraphBuilder
from src.personalization.query_merge import QueryGraphMerger
from src.personalization.adaptive import AdaptiveLearner
from src.personalization.models import UserProfile


class Pipeline:
    """Orchestrates the four-agent pipeline. Instantiate once; call run() per query.

    Args:
        db_conn: Active psycopg2 connection to the shared RDS Postgres database.
        openai_client: Initialised ``openai.OpenAI`` client (used for embeddings
            and all LLM calls — GPT-4o).
        anthropic_client: Deprecated, ignored. Kept for backward compatibility.
        brain_dir: Path to the ``brain/`` directory. Defaults to ``"brain"`` (relative
            to the process working directory, or an absolute path).
    """

    def __init__(
        self,
        db_conn,
        openai_client: "OpenAI",
        anthropic_client: object | None = None,  # deprecated, ignored
        brain_dir: str = "brain",
        build_centroids: bool = True,
        use_gpt4o: bool = True,
        memory_dir: str | None = None,
    ) -> None:
        # Build shared graph components once at startup (read-only, shared across queries)
        base_graph = build_base_graph()
        builder = UserSubgraphBuilder(base_graph)
        merger = QueryGraphMerger(base_graph)
        self._adaptive = AdaptiveLearner(builder)

        searcher = HybridSearcher(db_conn, openai_client, embeddings_table="embeddings_v2")

        # Create user memory store if memory_dir is provided
        memory_store = None
        if memory_dir:
            from src.personalization.user_memory import UserMemoryStore
            memory_store = UserMemoryStore(base_dir=memory_dir)

        self._agent_a = QueryUnderstandingAgent(
            db_conn=db_conn,
            openai_client=openai_client,
            anthropic_client=None,
            brain_dir=brain_dir,
            memory_store=memory_store,
        )
        if build_centroids:
            try:
                self._agent_a.build_centroids()  # precompute category centroids from DB
            except Exception:
                # build_centroids is a performance optimisation; failure is non-fatal.
                # Agent A will fall back to embedding + LLM classification without centroids.
                pass

        self._agent_b = RetrievalPlanningAgent(
            builder=builder,
            merger=merger,
            brain_dir=brain_dir,
            memory_store=memory_store,
        )
        self._agent_c = SynthesisAgent(
            searcher=searcher,
            anthropic_client=None,
            openai_client=openai_client,
        )
        self._agent_d = VerificationAgent()

    async def run(
        self,
        query: str,
        user_profile: UserProfile,
        return_context: bool = False,
        weight_overrides: dict[str, float] | None = None,
        model: str = "gpt-5.4",
    ) -> "PipelineResult | tuple[PipelineResult, QueryContext]":
        """Run a consumer health query through the full four-agent pipeline.

        Args:
            query: The raw consumer health question (plain English).
            user_profile: The user's profile (age, sex, conditions, health literacy).
            return_context: If True, return ``(PipelineResult, QueryContext)`` instead
                of just ``PipelineResult``.  Used by ``PipelineSampler`` to map
                intermediate agent state into an eval trace.
            weight_overrides: Optional dict mapping category slugs to pre-computed
                weights (0.0--1.0).  Passed through to Agent B; when provided,
                these replace the merger's effective_weights.

        Returns:
            ``PipelineResult`` by default.  ``(PipelineResult, QueryContext)`` when
            *return_context* is True.
        """
        ctx = QueryContext(query=query, user_profile=user_profile, model=model)

        ctx = await self._agent_a.run(ctx)
        ctx = await self._agent_b.run(ctx, weight_overrides=weight_overrides)
        ctx = await self._agent_c.run(ctx)
        ctx = await self._agent_d.run(ctx)

        # Adaptive learning: record actual brain categories from retrieved results
        if ctx.user_subgraph and ctx.search_results:
            touched = list({f"cat:{r.primary_category}" for r in ctx.search_results})
            try:
                self._adaptive.record_query(ctx.user_subgraph, touched_nodes=touched)
            except Exception:
                pass  # adaptive learning failure must not break the pipeline

        result = PipelineResult.from_context(ctx)
        if return_context:
            return result, ctx
        return result
