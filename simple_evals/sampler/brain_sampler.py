"""Brain-augmented sampler for HealthBench evaluation.

Uses a four-agent pipeline instead of one-shot:
  Agent A (Query Understanding) → Agent B (Retrieval Planning) →
  Agent C (Evidence Synthesis) → Agent D (Verification)
"""

import time
from typing import Any

import openai
from openai import OpenAI

from ..types import MessageList, SamplerBase, SamplerResponse

from src.personalization.base_graph import build_base_graph, get_category_nodes
from src.personalization.models import HealthLiteracy, Sex, UserProfile
from src.personalization.query_merge import QueryGraphMerger
from src.personalization.user_graph import UserSubgraphBuilder
from src.chat import load_brain_context, get_category_display_names


# ── Agent System Prompts ────────────────────────────────────────────────────

AGENT_A_SYSTEM = """You are Agent A — Query Understanding.

Your job is to parse a consumer health question and produce a structured analysis.

Given a user's health question, output the following in this exact format:

NORMALIZED_QUERY: <restate the query in clear medical terminology>
MEDICAL_TERMS: <comma-separated list of relevant medical terms>
CATEGORY: <the single best category slug from the list below>
INTENT: <one of: factual_lookup, symptom_assessment, treatment_info, medication_question, lifestyle_advice, emergency, prevention>
AMBIGUITY: <none | low | high — does the query need clarification?>
EMERGENCY: <yes | no — does this suggest an emergency situation?>

Available categories:
{categories}
"""

AGENT_B_SYSTEM = """You are Agent B — Retrieval Planning & Evidence Extraction.

You receive Agent A's query analysis and relevant medical knowledge base sections.
Your job is to extract the most relevant evidence from the knowledge base that directly answers the query.

Output the following in this exact format:

EVIDENCE:
1. [SOURCE_TIER: <1|2|3|4>] <specific fact or guideline relevant to the query>
2. [SOURCE_TIER: <1|2|3|4>] <next relevant fact>
... (extract 5-15 key evidence items)

SOURCE_PRIORITY: <which source types should be weighted highest for this query>
KEY_RULES: <any specific rules from the knowledge base that apply (e.g., drug interactions need 2+ sources)>
CROSS_CATEGORY_NOTES: <relevant information from related categories, if any>
"""

AGENT_C_SYSTEM = """You are Agent C — Evidence Synthesis.

You receive:
- The original user query
- Agent A's query analysis (normalized terms, intent, category)
- Agent B's extracted evidence (with source tiers)

Your job is to synthesize the evidence into a clear, helpful response for the user.

Rules:
- Write at an appropriate reading level based on the query complexity
- Cite source tiers inline: mark claims with [Tier 1], [Tier 2], etc.
- Never fabricate medical facts — only use evidence provided by Agent B
- Frame everything as information, never as diagnosis
- If evidence is limited, say so explicitly
- For emergency indicators, always prepend: "If this is an emergency, call 911."
- Structure the response with clear sections if the topic is complex
- Include practical next steps when appropriate

Output your draft response directly — this will be reviewed by Agent D.
"""

AGENT_D_SYSTEM = """You are Agent D — Verification & Final Output.

You receive:
- The original user query
- Agent B's extracted evidence
- Agent C's draft response

Your job is to verify the draft and produce the final response.

Verification checklist:
1. ACCURACY: Does every claim in the draft match the evidence from Agent B? Flag any unsupported claims.
2. COMPLETENESS: Are there important evidence items from Agent B that the draft missed?
3. CONTRADICTIONS: Are there any contradictory claims? If so, surface both perspectives.
4. CONFIDENCE: Rate overall confidence (high/medium/low) based on source tiers used.
5. SAFETY: Check for emergency language, appropriate disclaimers, no diagnostic claims.
6. CITATIONS: Are source tiers properly referenced?

After verification, output the FINAL response to the user. Rules:
- If confidence is HIGH (mostly Tier 1-2 sources): provide the answer directly.
- If confidence is MEDIUM (Tier 2-3 sources): add "Consider discussing with your healthcare provider."
- If confidence is LOW (Tier 3-4 or limited sources): add "We recommend consulting a healthcare professional for personalized guidance."
- Remove the [Tier N] markers from the final output — the user doesn't need to see those.
- Keep the response clear, well-structured, and actionable.
- If Agent C's draft had errors, correct them. If it was good, you may keep it largely as-is.

Output ONLY the final response text. No meta-commentary.
"""


class BrainAugmentedSampler(SamplerBase):
    """Sampler that runs the four-agent pipeline over the brain knowledge graph."""

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        profile: UserProfile | None = None,
    ):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Build the brain pipeline
        print("  Building base graph...")
        self.base_graph = build_base_graph()
        self.category_names = get_category_display_names(self.base_graph)
        self.merger = QueryGraphMerger(self.base_graph)

        # Build categories string for Agent A
        self.categories_str = "\n".join(
            f"- {slug}: {display}" for slug, display in sorted(self.category_names.items())
        )

        # Use provided profile or default generic profile
        if profile is None:
            profile = UserProfile(
                age=40,
                sex=Sex.PREFER_NOT_TO_SAY,
                health_literacy=HealthLiteracy.MEDIUM,
            )
        self.profile = profile

        # Build user subgraph
        builder = UserSubgraphBuilder(self.base_graph)
        self.user_subgraph = builder.build(profile)

        print(f"  Brain sampler ready: {self.base_graph.number_of_nodes()} nodes, "
              f"{len(self.category_names)} categories (4-agent pipeline)")

    def _extract_question(self, message_list: MessageList) -> str:
        """Extract the user's question from the message list."""
        for msg in reversed(message_list):
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    texts = [c["text"] for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    return " ".join(texts)
        return ""

    def _call_llm(self, system_prompt: str, user_content: str, max_tokens: int = 2048) -> str:
        """Make a single LLM call with retry logic."""
        trial = 0
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=self.temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty response")
                return content
            except openai.BadRequestError as e:
                print(f"Bad Request: {e}")
                return "No response (bad request)."
            except Exception as e:
                exception_backoff = 2**trial
                print(f"Error (retry {trial}, wait {exception_backoff}s): {e}")
                time.sleep(exception_backoff)
                trial += 1

    def _parse_category_from_agent_a(self, agent_a_output: str) -> str:
        """Extract the category slug from Agent A's output."""
        for line in agent_a_output.split("\n"):
            if line.strip().startswith("CATEGORY:"):
                slug = line.split(":", 1)[1].strip().lower().strip("`\"' ")
                if slug in self.category_names:
                    return slug
                for cat_slug in self.category_names:
                    if cat_slug in slug or slug in cat_slug:
                        return cat_slug
        # Fallback: try to find any category slug in the output
        for cat_slug in self.category_names:
            if cat_slug in agent_a_output.lower():
                return cat_slug
        return list(self.category_names.keys())[0]

    def __call__(self, message_list: MessageList) -> SamplerResponse:
        question = self._extract_question(message_list)

        # Format full conversation for context
        convo_str = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in message_list
        )

        # ── Agent A: Query Understanding ────────────────────────────────
        agent_a_system = AGENT_A_SYSTEM.format(categories=self.categories_str)
        agent_a_output = self._call_llm(agent_a_system, convo_str, max_tokens=500)

        # Parse category from Agent A
        category = self._parse_category_from_agent_a(agent_a_output)

        # ── Run graph merger to plan retrieval ──────────────────────────
        plan = self.merger.plan_retrieval(category, self.user_subgraph)
        brain_context = load_brain_context(plan)

        # ── Agent B: Retrieval Planning & Evidence Extraction ───────────
        agent_b_input = (
            f"AGENT A ANALYSIS:\n{agent_a_output}\n\n"
            f"RETRIEVAL PLAN:\n"
            f"  Primary: {plan.primary_category}\n"
            f"  Must-load: {plan.must_load}\n"
            f"  Explanation: {'; '.join(plan.explanation)}\n\n"
            f"KNOWLEDGE BASE CONTENT:\n{brain_context}"
        )
        agent_b_output = self._call_llm(AGENT_B_SYSTEM, agent_b_input, max_tokens=2048)

        # ── Agent C: Evidence Synthesis ─────────────────────────────────
        agent_c_input = (
            f"ORIGINAL QUERY:\n{convo_str}\n\n"
            f"AGENT A ANALYSIS:\n{agent_a_output}\n\n"
            f"AGENT B EVIDENCE:\n{agent_b_output}"
        )
        agent_c_output = self._call_llm(AGENT_C_SYSTEM, agent_c_input, max_tokens=self.max_tokens)

        # ── Agent D: Verification & Final Output ────────────────────────
        agent_d_input = (
            f"ORIGINAL QUERY:\n{convo_str}\n\n"
            f"AGENT B EVIDENCE:\n{agent_b_output}\n\n"
            f"AGENT C DRAFT RESPONSE:\n{agent_c_output}"
        )
        final_response = self._call_llm(AGENT_D_SYSTEM, agent_d_input, max_tokens=self.max_tokens)

        # Return in HealthBench's expected format
        return SamplerResponse(
            response_text=final_response,
            response_metadata={"usage": None},
            actual_queried_message_list=message_list,
        )
