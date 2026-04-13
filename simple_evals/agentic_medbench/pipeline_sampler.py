"""PipelineSampler — wraps the four-agent Pipeline as a SamplerBase.

Bridges the async Pipeline to the synchronous SamplerBase interface expected
by AgenticMedBenchEval.  Maps QueryContext fields into AgentTrace so all five
grading dimensions receive meaningful data instead of empty lists.

Threading note:
    asyncio.run() creates a new event loop per call, which is correct for
    multi-threaded use. However, psycopg2 connections are not thread-safe.
    Always use n_threads=1 when running AgenticMedBenchEval with this sampler.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from simple_evals.types import MessageList, SamplerBase, SamplerResponse
from simple_evals.agentic_medbench.profiles import PROFILE_PRESETS
from simple_evals.agentic_medbench.types import AgentTrace, ToolCall, RetrievalItem

from src.personalization.models import UserProfile


def _extract_query(message_list: MessageList) -> str:
    """Return the content of the last user-role message as a plain string.

    Handles both string content and list-of-parts content (e.g. multimodal).
    Returns an empty string if no user message is found.
    """
    for message in reversed(message_list):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part.get("text", "")
    return ""


def _build_agent_trace(query: str, ctx: Any) -> AgentTrace:
    """Map a QueryContext to an AgentTrace for eval grading.

    Each of the four pipeline agents contributes to the trace:
    - Agent A  → reasoning_trace entries for classification + term normalisation
    - Agent B  → reasoning_trace entry for retrieval plan + brain_graph tool call
    - Agent C  → reasoning_trace entry for hybrid search + hybrid_db_search tool call
    - Agent D  → reasoning_trace entries for confidence + uncertainty flags
    - Citations → retrieval_results (one RetrievalItem per verified citation)
    """
    t = time.time()  # Single timestamp shared across tool calls — reconstruction
                     # artefact; does not reflect actual agent wall-clock ordering.
    tool_calls: list[ToolCall] = []
    reasoning_trace: list[str] = []

    # --- Agent A: query understanding ----------------------------------------
    category = ctx.category or "unknown"
    method = ctx.classification_method or "unknown"
    reasoning_trace.append(
        f"Agent A: classified query as '{category}' using {method} method"
    )
    if ctx.normalized_terms:
        reasoning_trace.append(
            f"Agent A: normalized terms -> {', '.join(ctx.normalized_terms)}"
        )
    else:
        reasoning_trace.append("Agent A: no term normalization applied")

    # --- Agent B: retrieval planning -----------------------------------------
    retrieval_plan = ctx.retrieval_plan
    must_load = getattr(retrieval_plan, "must_load", []) if retrieval_plan else []
    may_load = getattr(retrieval_plan, "may_load", []) if retrieval_plan else []
    reasoning_trace.append(
        f"Agent B: retrieval plan built — must_load={must_load}, may_load={may_load}"
    )
    tool_calls.append(ToolCall(
        tool_name="brain_graph",
        arguments={"category": category},
        result=(ctx.brain_context[:500] if ctx.brain_context else "(no brain context loaded)"),
        timestamp=t,
    ))

    # --- Agent C: evidence synthesis -----------------------------------------
    n_results = len(ctx.search_results) if ctx.search_results else 0
    sources = {r.source_table for r in ctx.search_results} if ctx.search_results else set()
    reasoning_trace.append(
        f"Agent C: hybrid search (pgvector + FTS, RRF fusion) returned {n_results} results"
        + (f" from {', '.join(sorted(sources))}" if sources else "")
    )
    tool_calls.append(ToolCall(
        tool_name="hybrid_db_search",
        arguments={"query": query, "category": category},
        result=f"Retrieved {n_results} results via RRF fusion",
        timestamp=t,
    ))

    # --- Agent D: verification -----------------------------------------------
    confidence = getattr(ctx, "confidence", 0.0)
    disclaimer = getattr(ctx, "disclaimer", None)
    reasoning_trace.append(
        f"Agent D: confidence={confidence:.2f} — "
        f"disclaimer={'applied' if disclaimer else 'none'}"
    )
    uncertainty_flags = getattr(ctx, "uncertainty_flags", [])
    if uncertainty_flags:
        reasoning_trace.append(
            f"Agent D: uncertainty flags -> {', '.join(uncertainty_flags)}"
        )

    # --- Retrieval results from verified citations ---------------------------
    retrieval_results: list[RetrievalItem] = [
        RetrievalItem(
            source=c.source_table,
            content=c.text_snippet,
            relevance_score=c.relevance_score,
        )
        for c in (ctx.verified_citations or [])
    ]

    return AgentTrace(
        final_answer=ctx.final_answer or "",
        tool_calls=tool_calls,
        reasoning_trace=reasoning_trace,
        corrections=[],
        retrieval_results=retrieval_results,
    )


class PipelineSampler(SamplerBase):
    """Wraps the four-agent Pipeline as a SamplerBase for AgenticMedBenchEval.

    Args:
        pipeline: An initialised ``Pipeline`` instance.
        profile_name: Key into ``PROFILE_PRESETS``; one of
            ``"default"``, ``"low_literacy_patient"``,
            ``"high_literacy_nurse"``, ``"elderly_comorbid"``.

    Raises:
        ValueError: If *profile_name* is not a key in ``PROFILE_PRESETS``.

    Threading note:
        Use ``n_threads=1`` in ``AgenticMedBenchEval`` when using this sampler.
        psycopg2 connections are not thread-safe.
    """

    def __init__(self, pipeline: Any, profile_name: str = "default") -> None:
        if profile_name not in PROFILE_PRESETS:
            raise ValueError(
                f"Unknown profile '{profile_name}'. "
                f"Valid profiles: {sorted(PROFILE_PRESETS)}"
            )
        self.pipeline = pipeline
        self.profile_name = profile_name
        self.user_profile: UserProfile = PROFILE_PRESETS[profile_name]

    def __call__(self, message_list: MessageList) -> SamplerResponse:
        """Run the pipeline and return a SamplerResponse with a full AgentTrace.

        Args:
            message_list: Conversation messages; the last user message is used
                as the pipeline query.

        Returns:
            ``SamplerResponse`` with ``response_text`` set to the pipeline's
            final answer and ``response_metadata["agent_trace"]`` populated
            with the mapped ``AgentTrace`` dict.
        """
        query = _extract_query(message_list) or "No query provided."

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None and loop.is_running():
            raise RuntimeError(
                "PipelineSampler.__call__ must not be called from a running event loop. "
                "Use asyncio.run() from a synchronous context with n_threads=1 only."
            )

        result, ctx = asyncio.run(
            self.pipeline.run(query, self.user_profile, return_context=True)
        )

        trace = _build_agent_trace(query, ctx)

        return SamplerResponse(
            response_text=result.answer_text,
            actual_queried_message_list=list(message_list),
            response_metadata={"agent_trace": trace.to_dict()},
        )
