"""Agentic sampler with OpenAI function calling in a ReAct-style loop.

Replaces the old linear BrainAugmentedSampler with real tool use.  The agent
iteratively calls tools (PubMed, Drug DB, Web Search, and optionally the Brain
knowledge graph) until it produces a final text answer.

Three experimental conditions:
    BASELINE       — no brain graph, no personalisation
    BRAIN_STEERED  — brain graph available, no user profile
    FULLY_STEERED  — brain graph + user profile + literacy-level instructions
"""

from __future__ import annotations

import json
import logging
import re
import time
from enum import Enum
from typing import Any

from openai import OpenAI

from ..types import MessageList, SamplerBase, SamplerResponse
from .profiles import PROFILE_PRESETS, build_profile_and_subgraph
from .tools import ToolRegistry
from .types import AgentTrace, ToolCall

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_REACT_ROUNDS = 10

_BASELINE_TOOLS = ["pubmed_search", "drug_interaction_db", "web_search"]
_ALL_TOOLS = ["brain_graph", "pubmed_search", "drug_interaction_db", "web_search"]

_RETRIEVAL_TOOLS = {"pubmed_search", "drug_interaction_db"}

_PMID_PATTERN = re.compile(r"^- (PMID \d+): (.+)$", re.MULTILINE)


def _parse_retrieval_items(tool_name: str, result: str) -> list:
    """Parse tool results into RetrievalItem objects for trace capture."""
    from .types import RetrievalItem

    if tool_name not in _RETRIEVAL_TOOLS:
        return []

    if result.startswith("Error"):
        return []

    if tool_name == "pubmed_search":
        items = []
        for match in _PMID_PATTERN.finditer(result):
            items.append(RetrievalItem(
                source=match.group(1),
                content=match.group(2),
                relevance_score=1.0,
            ))
        return items

    if tool_name == "drug_interaction_db":
        return [RetrievalItem(
            source="openfda",
            content=result,
            relevance_score=1.0,
        )]

    return []

# ---------------------------------------------------------------------------
# AgentCondition enum
# ---------------------------------------------------------------------------


class AgentCondition(Enum):
    """Experimental condition controlling what resources the agent can access."""

    BASELINE = "baseline"
    BRAIN_STEERED = "brain_steered"
    FULLY_STEERED = "fully_steered"


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_BASE_SYSTEM_PROMPT = (
    "You are a medical information agent. Your goal is to answer health "
    "questions accurately, citing evidence from authoritative sources.\n\n"
    "CRITICAL RULES:\n"
    "1. USE TOOLS to find evidence — do NOT answer from memory alone.\n"
    "2. Search PubMed for peer-reviewed evidence on the topic.\n"
    "3. Check the drug interaction database when medications are involved.\n"
    "4. If evidence is insufficient, say so explicitly.\n"
    "5. Never provide a diagnosis — frame responses as information.\n"
    "6. For emergencies, always advise calling 911 / emergency services.\n"
    "7. Cite your sources (PubMed IDs, database references).\n\n"
    "Think step by step. Use tools to gather evidence before answering."
)

_BRAIN_STEERED_ADDENDUM = (
    "\n\nADDITIONAL RESOURCE — Brain Knowledge Base:\n"
    "You have access to a curated health knowledge base via the 'brain_graph' "
    "tool. Use it to:\n"
    "- Load 'general_rules' for cross-category verification rules\n"
    "- Load specific category files for domain knowledge\n"
    "- Pass 'list' to see all available categories\n\n"
    "Available brain categories:\n{categories}\n\n"
    "STRATEGY: Start by loading the most relevant brain category for the "
    "question, then cross-reference with PubMed for current evidence."
)

_FULLY_STEERED_ADDENDUM = (
    "\n\nUSER PROFILE (personalise your response):\n"
    "- Age: {age}\n"
    "- Sex: {sex}\n"
    "- Conditions: {conditions}\n"
    "- Medications: {medications}\n"
    "- Health Literacy: {literacy}\n\n"
    "LANGUAGE INSTRUCTIONS: {literacy_instructions}\n\n"
    "Consider the user's existing conditions and medications when answering. "
    "Flag any potential interactions or condition-specific considerations."
)

_LITERACY_INSTRUCTIONS = {
    "low": (
        "Use plain, simple language (grade 5-6 reading level). "
        "No medical jargon. Short sentences. Explain any medical terms."
    ),
    "medium": (
        "Use accessible language (grade 8-10 reading level). "
        "You may use some medical terms but define them."
    ),
    "high": (
        "You may use full medical terminology. "
        "The user has a clinical or advanced background."
    ),
}


# ---------------------------------------------------------------------------
# AgenticSampler
# ---------------------------------------------------------------------------


class AgenticSampler(SamplerBase):
    """Agentic sampler that uses OpenAI function calling in a ReAct loop.

    Depending on the ``condition``, the agent has access to different tools
    and receives different system prompts:

    - BASELINE: pubmed_search, drug_interaction_db, web_search
    - BRAIN_STEERED: all tools including brain_graph; system prompt lists
      available brain categories
    - FULLY_STEERED: all tools + user profile injected into system prompt
      with literacy-level instructions
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        condition: AgentCondition = AgentCondition.BASELINE,
        profile_name: str = "default",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.condition = condition
        self.profile_name = profile_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # OpenAI client
        self.client = OpenAI()

        # Tool registry
        self.registry = ToolRegistry()

        # Select available tools based on condition
        if condition == AgentCondition.BASELINE:
            self.available_tools = list(_BASELINE_TOOLS)
        else:
            self.available_tools = list(_ALL_TOOLS)

        # Get schemas for the selected tools
        self.tool_schemas = self.registry.get_schemas(self.available_tools)

        # Brain graph resources (only for BRAIN_STEERED and FULLY_STEERED)
        self.base_graph = None
        self.category_names: dict[str, str] | None = None
        self.merger = None
        self.profile = None
        self.user_subgraph = None

        if condition in (AgentCondition.BRAIN_STEERED, AgentCondition.FULLY_STEERED):
            self._init_brain_resources()

        if condition == AgentCondition.FULLY_STEERED:
            self._init_profile(profile_name)

    # -- Initialisation helpers -----------------------------------------------

    def _init_brain_resources(self) -> None:
        """Build the base graph, category names, and query merger."""
        from src.personalization.base_graph import build_base_graph
        from src.personalization.query_merge import QueryGraphMerger
        from src.chat import get_category_display_names

        self.base_graph = build_base_graph()
        self.category_names = get_category_display_names(self.base_graph)
        self.merger = QueryGraphMerger(self.base_graph)

    def _init_profile(self, profile_name: str) -> None:
        """Build the user profile and personalised subgraph."""
        profile, subgraph = build_profile_and_subgraph(profile_name)
        self.profile = profile
        self.user_subgraph = subgraph

    # -- System prompt construction -------------------------------------------

    def _build_system_prompt(self) -> str:
        """Construct the system prompt based on the current condition."""
        prompt = _BASE_SYSTEM_PROMPT

        if self.condition in (
            AgentCondition.BRAIN_STEERED,
            AgentCondition.FULLY_STEERED,
        ):
            categories_str = "\n".join(
                f"  - {slug}: {display}"
                for slug, display in sorted(self.category_names.items())
            )
            prompt += _BRAIN_STEERED_ADDENDUM.format(categories=categories_str)

        if self.condition == AgentCondition.FULLY_STEERED and self.profile is not None:
            conditions_str = (
                ", ".join(c.name for c in self.profile.conditions)
                or "none reported"
            )
            medications_str = (
                ", ".join(m.name for m in self.profile.medications)
                or "none reported"
            )
            literacy_key = self.profile.health_literacy.value
            prompt += _FULLY_STEERED_ADDENDUM.format(
                age=self.profile.age,
                sex=self.profile.sex.value,
                conditions=conditions_str,
                medications=medications_str,
                literacy=self.profile.health_literacy.value,
                literacy_instructions=_LITERACY_INSTRUCTIONS.get(
                    literacy_key, _LITERACY_INSTRUCTIONS["medium"]
                ),
            )

        return prompt

    # -- ReAct loop -----------------------------------------------------------

    def __call__(self, message_list: MessageList) -> SamplerResponse:
        """Run the ReAct loop and return a SamplerResponse.

        The agent iterates up to ``_MAX_REACT_ROUNDS`` times. Each round:
        1. Send messages + tool schemas to the model.
        2. If the model returns tool calls, execute them and append results.
        3. If the model returns text content, treat it as the final answer.

        Args:
            message_list: The user messages to respond to.

        Returns:
            A ``SamplerResponse`` with ``response_text`` set to the final
            answer and ``response_metadata`` containing the serialised
            ``AgentTrace``.
        """
        system_prompt = self._build_system_prompt()

        # Build the full conversation with the system prompt prepended
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *message_list,
        ]

        trace = AgentTrace(final_answer="")

        for round_idx in range(_MAX_REACT_ROUNDS):
            logger.debug(
                "ReAct round %d/%d — sending %d messages",
                round_idx + 1,
                _MAX_REACT_ROUNDS,
                len(messages),
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tool_schemas,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            choice = response.choices[0]
            assistant_message = choice.message

            # If the model produced tool calls, execute them
            if assistant_message.tool_calls:
                # Append the assistant message (with tool_calls) to history
                messages.append(assistant_message.model_dump())

                for tc in assistant_message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        arguments = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    timestamp = time.time()
                    result = self.registry.execute(tool_name, arguments)

                    # Record in trace
                    trace.tool_calls.append(
                        ToolCall(
                            tool_name=tool_name,
                            arguments=arguments,
                            result=result,
                            timestamp=timestamp,
                        )
                    )

                    # Populate retrieval results from retrieval tools
                    retrieval_items = _parse_retrieval_items(tool_name, result)
                    trace.retrieval_results.extend(retrieval_items)

                    # Capture reasoning trace from tool call
                    trace.reasoning_trace.append(
                        f"Round {round_idx + 1}: Called {tool_name}("
                        f"{json.dumps(arguments)[:200]})"
                    )

                    # Append tool result to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        }
                    )

                    logger.debug(
                        "Tool call: %s(%s) -> %d chars",
                        tool_name,
                        json.dumps(arguments)[:100],
                        len(result),
                    )

            # If the model produced text content (and no tool calls), that is
            # the final answer
            elif assistant_message.content:
                trace.final_answer = assistant_message.content
                break

            # Edge case: model returned neither tool calls nor content
            else:
                logger.warning(
                    "Round %d: model returned neither tool calls nor content.",
                    round_idx + 1,
                )
                trace.final_answer = (
                    "I was unable to generate a response. "
                    "Please try rephrasing your question."
                )
                break

            # Also capture any reasoning text alongside tool calls
            if assistant_message.content:
                trace.reasoning_trace.append(assistant_message.content)

        else:
            # Exhausted all rounds without a final text answer
            trace.final_answer = (
                "I reached the maximum number of research steps without "
                "arriving at a final answer. Here is what I found so far: "
                + "; ".join(
                    f"[{tc.tool_name}] {tc.result[:200]}"
                    for tc in trace.tool_calls[-3:]
                )
            )

        return SamplerResponse(
            response_text=trace.final_answer,
            actual_queried_message_list=messages,
            response_metadata={"agent_trace": trace.to_dict()},
        )
