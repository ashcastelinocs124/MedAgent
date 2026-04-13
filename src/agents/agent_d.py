# src/agents/agent_d.py
"""Verification Agent (Agent D).

Scores confidence, deduplicates citations, raises uncertainty flags,
and attaches appropriate disclaimers.  Pure Python — no DB, no API calls.
"""
from __future__ import annotations

from src.agents.context import QueryContext, Citation

_TIER_WEIGHTS: dict[str, float] = {
    "TIER_A": 1.0,
    "TIER_B": 0.7,
    "TIER_C": 0.4,
    "TIER_D": 0.1,
}
_DEFAULT_WEIGHT = 0.1

# MedQuAD uses consumer-style questions → highest alignment with user queries.
# MedMCQA uses clinical MCQ format → structural noise lowers effective similarity.
_SOURCE_RELEVANCE_WEIGHT: dict[str, float] = {
    "medquad_records": 1.2,
    "pubmedqa_records": 1.0,
    "medmcqa_records": 0.85,
}

# Results below this cosine similarity threshold are noise — exclude from scoring.
_MIN_RELEVANCE = 0.35

_DISCLAIMER_HIGH = "Consider discussing this with your healthcare provider."
_DISCLAIMER_MED = (
    "This is general health information only. "
    "Please consult a healthcare professional for advice specific to your situation."
)
_DISCLAIMER_LOW = (
    "Limited evidence was found. This information may be incomplete. "
    "Please consult a qualified healthcare professional."
)

_NARROW_TI_DRUGS: frozenset[str] = frozenset({
    "warfarin", "digoxin", "lithium", "phenytoin", "theophylline",
    "carbamazepine", "cyclosporine", "tacrolimus", "methotrexate",
})


class VerificationAgent:
    """Agent D — verifies, scores, deduplicates, and annotates a QueryContext."""

    async def run(self, ctx: QueryContext) -> QueryContext:
        """Run verification on *ctx* (mutates and returns it).

        Args:
            ctx: Mutable pipeline context populated by Agents A–C.

        Returns:
            The same *ctx* with confidence, flags, disclaimer, verified_citations,
            and final_answer populated.
        """
        # Drop noise results before scoring — anything below 0.35 similarity
        # is not a meaningful match and would unfairly drag down the averages.
        # Fall back to the full list only if everything is below the threshold.
        scored = [r for r in ctx.search_results if r.relevance_score >= _MIN_RELEVANCE]
        results = scored or ctx.search_results

        # ------------------------------------------------------------------
        # 1. Confidence score
        #    Two independent components, blended equally:
        #      tier_avg      = mean tier weight across results  (source trustworthiness)
        #      relevance_avg = source-weighted mean similarity  (retrieval quality)
        #      source_bonus  = +0.05 per additional unique table, capped at 0.10
        #    confidence = 0.5 × tier_avg + 0.5 × relevance_avg + source_bonus
        # ------------------------------------------------------------------
        n = max(1, len(results))
        tier_avg = sum(
            _TIER_WEIGHTS.get(r.quality_tier, _DEFAULT_WEIGHT) for r in results
        ) / n
        relevance_avg = min(1.0, sum(
            r.relevance_score * _SOURCE_RELEVANCE_WEIGHT.get(r.source_table, 1.0)
            for r in results
        ) / n)
        unique_tables = len({r.source_table for r in results})
        source_bonus = min(0.10, 0.05 * (unique_tables - 1))
        confidence = min(1.0, max(0.0, 0.5 * tier_avg + 0.5 * relevance_avg + source_bonus))

        # ------------------------------------------------------------------
        # 2. Drug-interaction safety cap
        #    Medications category + single source table → cap at 0.80
        # ------------------------------------------------------------------
        if ctx.category == "medications_drug_safety" and unique_tables < 2:
            confidence = min(confidence, 0.80)

        ctx.confidence = confidence

        # ------------------------------------------------------------------
        # 3. Uncertainty flags
        # ------------------------------------------------------------------
        flags: list[str] = []

        if confidence < 0.55:
            flags.append("[UNCERTAINTY FLAG]")

        if ctx.category == "medications_drug_safety":
            all_text = " ".join(r.chunk_text.lower() for r in results)
            if any(drug in all_text for drug in _NARROW_TI_DRUGS):
                flags.append("[NARROW TI FLAG]")

        ctx.uncertainty_flags = flags

        # ------------------------------------------------------------------
        # 4. Disclaimer routing
        #    Thresholds calibrated to the new two-component formula:
        #      ≥0.80 → no disclaimer   (high tier + high sim, strong evidence)
        #      ≥0.60 → light reminder  (good tier or good sim, generally reliable)
        #      ≥0.45 → medium caution  (mixed quality, general information only)
        #      <0.45 → low evidence    (weak tier and weak sim)
        # ------------------------------------------------------------------
        if confidence >= 0.80:
            ctx.disclaimer = None
        elif confidence >= 0.60:
            ctx.disclaimer = _DISCLAIMER_HIGH
        elif confidence >= 0.45:
            ctx.disclaimer = _DISCLAIMER_MED
        else:
            ctx.disclaimer = _DISCLAIMER_LOW

        # ------------------------------------------------------------------
        # 5. Citation deduplication by composite key (source_table, record_id)
        #    Sorted by tier then descending relevance_score.
        # ------------------------------------------------------------------
        seen: set[tuple[str, str]] = set()
        deduped: list[Citation] = []
        for c in ctx.raw_citations:
            key = (c.source_table, c.record_id)
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        _tier_order: dict[str, int] = {"TIER_A": 0, "TIER_B": 1, "TIER_C": 2, "TIER_D": 3}
        deduped.sort(key=lambda c: (_tier_order.get(c.quality_tier, 9), -c.relevance_score))
        ctx.verified_citations = deduped

        # ------------------------------------------------------------------
        # 6. Final answer assembly
        #    At medium confidence (0.55–0.79) inject an epistemic hedge into
        #    the answer text so the response reads as appropriately tentative
        #    rather than definitive.  Disclaimer is surfaced separately by
        #    the frontend — do not append it here.
        # ------------------------------------------------------------------
        if 0.55 <= confidence < 0.80:
            hedge = (
                "*Based on the available evidence, the following information may apply "
                "to your situation — individual circumstances vary and a healthcare "
                "provider can give personalised guidance.*\n\n"
            )
            ctx.final_answer = hedge + (ctx.raw_answer or "")
        else:
            ctx.final_answer = ctx.raw_answer

        return ctx
