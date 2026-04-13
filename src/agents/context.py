# src/agents/context.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """A single result from HybridSearcher. record_id is unique within source_table only."""
    record_id: str
    source_table: str       # "medmcqa_records" | "pubmedqa_records" | "medquad_records"
    primary_category: str   # brain category slug, e.g. "medications_drug_safety"
    quality_tier: str       # "TIER_A" | "TIER_B" | "TIER_C" | "TIER_D"
    chunk_text: str
    relevance_score: float  # raw similarity or ts_rank score, 0–1 normalized
    rrf_score: float        # set after RRF fusion


@dataclass
class Citation:
    record_id: str
    source_table: str
    quality_tier: str
    text_snippet: str       # first 200 chars of chunk_text
    relevance_score: float


@dataclass
class PipelineResult:
    answer_text: str
    citations: list[Citation]
    confidence: float
    disclaimer: str | None
    uncertainty_flags: list[str]
    category: str
    debug: dict[str, Any]

    @classmethod
    def from_context(cls, ctx: "QueryContext") -> "PipelineResult":
        retrieval_plan = ctx.retrieval_plan
        return cls(
            answer_text=ctx.final_answer,
            citations=ctx.verified_citations,
            confidence=ctx.confidence,
            disclaimer=ctx.disclaimer,
            uncertainty_flags=ctx.uncertainty_flags,
            category=ctx.category,
            debug={
                "classification_method": ctx.classification_method,
                "normalized_terms": ctx.normalized_terms,
                "search_result_count": len(ctx.search_results),
                "graph_must_load": getattr(retrieval_plan, "must_load", []),
                "graph_may_load": getattr(retrieval_plan, "may_load", []),
                "graph_effective_weights": getattr(retrieval_plan, "effective_weights", {}),
                "search_results_debug": [
                    {
                        "record_id": r.record_id,
                        "source_table": r.source_table,
                        "primary_category": r.primary_category,
                        "quality_tier": r.quality_tier,
                        "relevance_score": round(r.relevance_score, 4),
                        "rrf_score": round(r.rrf_score, 6),
                    }
                    for r in ctx.search_results
                ],
            },
        )


@dataclass
class QueryContext:
    """Mutable context object passed through all four agents."""
    # Input
    query: str
    user_profile: Any  # UserProfile from src.personalization.models

    # Set by Agent A
    normalized_terms: list[str] = field(default_factory=list)
    category: str | None = None
    classification_method: str | None = None  # "keyword"|"embedding"|"llm"|"fallback"

    # Set by Agent B
    retrieval_plan: Any = None   # RetrievalPlan from src.personalization.query_merge
    brain_context: str = ""
    user_subgraph: Any = None    # UserSubgraph from src.personalization.user_graph

    # Set by Agent C
    search_results: list[SearchResult] = field(default_factory=list)
    raw_answer: str = ""
    raw_citations: list[Citation] = field(default_factory=list)

    # Set by Agent D
    confidence: float = 0.0
    disclaimer: str | None = None
    uncertainty_flags: list[str] = field(default_factory=list)
    final_answer: str = ""
    verified_citations: list[Citation] = field(default_factory=list)
