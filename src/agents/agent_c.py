# src/agents/agent_c.py
"""Evidence Synthesis Agent (Agent C).

Runs hybrid search using the retrieval plan from Agent B, then calls
GPT-4o to synthesize a personalized answer grounded in the retrieved
evidence. Populates ctx.search_results, ctx.raw_answer, and
ctx.raw_citations.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI
    from src.search.hybrid import HybridSearcher

from src.agents.context import Citation, QueryContext

_LITERACY_INSTRUCTIONS: dict[str, str] = {
    "LOW": "Use very simple language. Aim for a 6th-grade reading level. Avoid medical jargon.",
    "MEDIUM": "Use plain language. Aim for a 10th-grade reading level. Define medical terms when used.",
    "HIGH": "You may use clinical terminology. The reader has strong health literacy.",
}
_DEFAULT_LITERACY = "MEDIUM"
_TOP_K = 8


class SynthesisAgent:
    """Agent C — synthesizes an evidence-based, personalized answer.

    Args:
        searcher: A HybridSearcher instance used to retrieve relevant records.
        anthropic_client: Deprecated, ignored. Kept for backward compatibility.
        openai_client: An initialised OpenAI client used to call GPT-4o.
    """

    def __init__(
        self,
        searcher: "HybridSearcher",
        anthropic_client: object | None = None,  # deprecated, ignored
        openai_client: "OpenAI | None" = None,
    ) -> None:
        self._searcher = searcher
        self._openai = openai_client

    async def run(self, ctx: QueryContext) -> QueryContext:
        """Execute synthesis and populate ctx in-place.

        Args:
            ctx: Mutable pipeline context object.  Must have category,
                normalized_terms, brain_context, retrieval_plan, and
                user_profile set by prior agents.

        Returns:
            The same ctx object with search_results, raw_answer, and
            raw_citations populated.
        """
        # Run hybrid search in a thread (psycopg2 is synchronous/blocking)
        results = await asyncio.to_thread(
            self._searcher.search,
            ctx.normalized_terms or [ctx.query],
            ctx.category or "public_health_prevention",
            ctx.retrieval_plan,
            _TOP_K,
        )
        ctx.search_results = results

        # Build system prompt personalised to user literacy
        system_prompt = self._build_system_prompt(ctx)

        # Format retrieved evidence for the user message
        evidence = self._format_evidence(results)

        # Call OpenAI for synthesis — model selected per-query via ctx.model
        model = getattr(ctx, "model", None) or "gpt-5.4"
        user_message = f"Query: {ctx.query}\n\nEvidence:\n{evidence}"
        response = await asyncio.to_thread(
            self._openai.chat.completions.create,
            model=model,
            max_completion_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        ctx.raw_answer = response.choices[0].message.content.strip()

        # Extract citations from search results
        ctx.raw_citations = [
            Citation(
                record_id=r.record_id,
                source_table=r.source_table,
                quality_tier=r.quality_tier,
                text_snippet=r.chunk_text[:200],
                relevance_score=r.relevance_score,
            )
            for r in results
        ]
        return ctx

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, ctx: QueryContext) -> str:
        """Construct a system prompt that encodes literacy level and context.

        Args:
            ctx: Current pipeline context.

        Returns:
            A formatted system prompt string.
        """
        literacy_level = getattr(ctx.user_profile, "health_literacy", None)
        # HealthLiteracy enum values are lowercase strings ("low"/"medium"/"high")
        literacy_str = str(literacy_level.value).upper() if literacy_level else _DEFAULT_LITERACY
        literacy_instruction = _LITERACY_INSTRUCTIONS.get(
            literacy_str, _LITERACY_INSTRUCTIONS[_DEFAULT_LITERACY]
        )

        parts = [
            "You are a healthcare information assistant. Your job is to synthesize"
            " evidence-based answers to health questions.",
            f"\nLanguage level: {literacy_instruction}",
            "\nDo NOT include inline citation tags or source references in your answer."
            " Citations are handled separately by the system.",
            "\nNever fabricate information. Only use the provided evidence.",
            "\nFormat your answer in clean markdown: use ## for headings, **bold** for"
            " key terms, and bullet points for lists. Do not use horizontal rules (---).",
            "\n## Context-Seeking\n"
            "If the query is vague and lacks critical context (specific condition, patient age,"
            " symptom duration, current medications, or severity), prepend 1-2 focused"
            " clarifying questions BEFORE your answer, under a ## Clarifying Questions heading."
            " Only ask if the missing context would materially change your advice."
            " Do not ask questions if the query is self-contained.",
            "\n## Completeness and Depth\n"
            "Your response must address ALL of the following that are relevant:\n"
            "- **Red flags or emergency warning signs** that require immediate care\n"
            "- **Specific treatment options, medications, or next steps** (name specific drugs,"
            " dosages, or procedures — not generic categories)\n"
            "- **When to seek professional help** (primary care vs. specialist vs. ER)\n"
            "- **Mechanism or explanation** of why something happens, not just what to do\n"
            "Be specific and thorough. A vague or partial answer scores poorly."
            " If evidence supports it, include dosages, timelines, or measurable thresholds.",
        ]

        if ctx.brain_context:
            parts.append(f"\nKnowledge base context:\n{ctx.brain_context[:8000]}")

        # Build rich user context so the LLM can tailor depth and terminology
        profile = ctx.user_profile
        user_context_parts: list[str] = []
        if hasattr(profile, "age") and profile.age:
            user_context_parts.append(f"Age: {profile.age}")
        if hasattr(profile, "sex") and profile.sex and str(profile.sex.value) != "prefer_not_to_say":
            user_context_parts.append(f"Sex: {profile.sex.value}")
        if hasattr(profile, "conditions") and profile.conditions:
            cond_names = [c.name for c in profile.conditions[:10]]
            user_context_parts.append(f"Active conditions: {', '.join(cond_names)}")
        if hasattr(profile, "medications") and profile.medications:
            med_names = [m.name for m in profile.medications[:10]]
            user_context_parts.append(f"Current medications: {', '.join(med_names)}")
        if user_context_parts:
            parts.append("\n## User Context\n" + "\n".join(user_context_parts))

        return "\n".join(parts)

    def _format_evidence(self, results: list) -> str:
        """Format search results into a numbered evidence block.

        Args:
            results: List of SearchResult objects.

        Returns:
            A formatted string suitable for inclusion in an LLM message.
        """
        if not results:
            return "No specific evidence retrieved."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] [{r.quality_tier}] ({r.source_table}): {r.chunk_text[:400]}")
        return "\n\n".join(lines)
