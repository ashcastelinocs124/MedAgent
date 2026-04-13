"""Test case generator for Agentic MedBench evaluation.

Transforms HealthBench examples into agentic test cases and generates
fresh multi-step scenarios.  Two main entry points:

1. **augment_healthbench_example** -- takes an existing HealthBench example
   (question + rubric) and augments it with agentic metadata (required tools,
   retrieval topics, reasoning checkpoints, difficulty level).
2. **generate_fresh_case** -- generates a completely new agentic test case
   from a topic string.

Both functions rely on an LLM (via ``SamplerBase``) to produce the agentic
metadata as structured JSON.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from ..types import MessageList, SamplerBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid tool names (for validation and prompt instructions)
# ---------------------------------------------------------------------------

_VALID_TOOLS = frozenset({
    "pubmed_search",
    "drug_interaction_db",
    "web_search",
    "brain_graph",
    "hybrid_db_search",
})

# ---------------------------------------------------------------------------
# AUGMENTATION_PROMPT
# ---------------------------------------------------------------------------

AUGMENTATION_PROMPT: str = (
    "You are a medical test-case augmentation assistant.  You will receive a "
    "health question and its grading rubric (criteria with point values).  "
    "Your job is to analyze the question and determine what agentic behaviour "
    "an ideal medical QA agent should exhibit when answering it.\n\n"
    "Output a single JSON object with exactly these keys:\n\n"
    "- **required_tools**: list of tools the agent should use.  Choose from: "
    "pubmed_search, drug_interaction_db, web_search, brain_graph, hybrid_db_search.  "
    "Use hybrid_db_search for structured medical QA retrieval from a curated database. "
    "Include only tools that are genuinely needed for the question.\n"
    "- **expected_retrieval_topics**: list of 2-5 key topics the agent "
    "should retrieve evidence about.  Be specific (e.g. \"ibuprofen dosage "
    "guidelines for adults\", not just \"ibuprofen\").\n"
    "- **reasoning_checkpoints**: list of 2-5 reasoning steps the agent "
    "should demonstrate in its trace.  Each checkpoint should be a brief "
    "sentence describing a critical reasoning step.\n"
    "- **difficulty**: one of \"standard\", \"hard\", or \"multi_step\".  Use "
    "\"standard\" for straightforward factual questions, \"hard\" for questions "
    "requiring nuanced clinical reasoning, and \"multi_step\" for questions "
    "that require multiple retrieval and synthesis steps.\n\n"
    "Respond ONLY with the JSON object.  No explanation, no markdown fences."
)

# ---------------------------------------------------------------------------
# GENERATION_PROMPT
# ---------------------------------------------------------------------------

GENERATION_PROMPT: str = (
    "You are a medical test-case generator.  Given a health topic, create a "
    "realistic multi-step medical question that an agentic QA system should "
    "be able to answer.  The question should require the agent to use tools, "
    "retrieve evidence, and reason through multiple steps.\n\n"
    "Output a single JSON object with exactly these keys:\n\n"
    "- **conversation**: a list of message objects, each with \"role\" and "
    "\"content\" keys.  The conversation should contain at least one user "
    "message with the medical question.\n"
    "- **required_tools**: list of tools the agent should use.  Choose from: "
    "pubmed_search, drug_interaction_db, web_search, brain_graph, hybrid_db_search.  "
    "Use hybrid_db_search for structured medical QA retrieval from a curated database.\n"
    "- **expected_retrieval_topics**: list of 2-5 key topics to retrieve.\n"
    "- **reasoning_checkpoints**: list of 2-5 reasoning steps the agent "
    "should demonstrate.\n"
    "- **answer_rubric**: object with \"positive_points\" (list of objects "
    "with \"criterion\" and \"points\") and \"negative_points\" (list of "
    "objects with \"criterion\" and \"points\"), and "
    "\"total_possible_points\" (integer).\n"
    "- **difficulty**: one of \"standard\", \"hard\", or \"multi_step\".\n"
    "- **tags**: list of descriptive tags for the test case (e.g. "
    "[\"cardiology\", \"drug_interaction\"]).\n\n"
    "Respond ONLY with the JSON object.  No explanation, no markdown fences."
)

# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------


def parse_augmented_case(raw: str) -> dict[str, Any]:
    """Parse JSON from LLM output, handling ````` ```json ``` ````` fences.

    Args:
        raw: Raw text from the LLM, which may contain the JSON wrapped in
            markdown code fences or surrounded by prose.

    Returns:
        Parsed dict from the JSON content.

    Raises:
        ValueError: If *raw* is empty or does not contain valid JSON.
        json.JSONDecodeError: If the extracted text is not valid JSON.
    """
    if not raw or not raw.strip():
        raise ValueError("Empty input: cannot parse augmented case from empty string.")

    cleaned = raw.strip()

    # Attempt 1: strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_pattern = re.compile(
        r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL
    )
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # Attempt 2: try to parse directly
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Attempt 3: find first JSON object embedded in prose
    obj_pattern = re.compile(r"\{.*\}", re.DOTALL)
    obj_match = obj_pattern.search(raw)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Failed to parse JSON from LLM output: {raw[:200]}"
    )


# ---------------------------------------------------------------------------
# HealthBench augmentation
# ---------------------------------------------------------------------------


def _build_augmentation_user_prompt(example: dict) -> str:
    """Build the user-role prompt for augmenting a HealthBench example.

    Args:
        example: HealthBench example dict with ``prompt``, ``rubrics``,
            ``prompt_id``, and ``example_tags``.

    Returns:
        Formatted prompt string showing the question and rubric summary.
    """
    # Extract the user question from the conversation
    prompt_messages: list[dict] = example.get("prompt", [])
    question_text = ""
    for msg in prompt_messages:
        if msg.get("role") == "user":
            question_text = msg.get("content", "")
            break

    if not question_text:
        question_text = "(no user question found)"

    # Summarise the rubric items
    rubrics = example.get("rubrics", [])
    rubric_lines: list[str] = []
    for item in rubrics:
        # Handle both dict and object (dataclass/namedtuple) forms
        if hasattr(item, "criterion"):
            criterion = item.criterion
            points = item.points
            tags = getattr(item, "tags", [])
        else:
            criterion = item.get("criterion", "")
            points = item.get("points", 0)
            tags = item.get("tags", [])

        tag_str = f" [tags: {', '.join(tags)}]" if tags else ""
        rubric_lines.append(f"  - [{points} pts] {criterion}{tag_str}")

    rubric_text = "\n".join(rubric_lines) if rubric_lines else "  (no rubric items)"

    return (
        f"## Health Question\n{question_text}\n\n"
        f"## Grading Rubric\n{rubric_text}\n\n"
        "Analyze this question and rubric, then output the JSON object "
        "with required_tools, expected_retrieval_topics, "
        "reasoning_checkpoints, and difficulty."
    )


def augment_healthbench_example(
    example: dict,
    augmenter_model: SamplerBase,
) -> dict[str, Any]:
    """Augment a HealthBench example with agentic metadata.

    Takes a HealthBench example (with ``prompt``, ``rubrics``, ``prompt_id``,
    ``example_tags``) and calls the augmenter model to generate agentic
    metadata such as required tools, retrieval topics, reasoning checkpoints,
    and difficulty level.

    Retries up to 3 times on parse failure.  On total failure, returns a
    fallback dict with minimal metadata.

    Args:
        example: HealthBench example dict.
        augmenter_model: A ``SamplerBase`` instance for the augmentation LLM.

    Returns:
        Dict with keys: ``id``, ``conversation``, ``answer_rubric``,
        ``required_tools``, ``expected_retrieval_topics``,
        ``reasoning_checkpoints``, ``difficulty``, ``source``, ``tags``.
    """
    user_prompt = _build_augmentation_user_prompt(example)
    messages: MessageList = [
        {"role": "system", "content": AUGMENTATION_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    prompt_id = example.get("prompt_id", str(uuid.uuid4()))
    example_tags = example.get("example_tags", [])

    # Build the answer rubric from the original rubrics
    rubrics = example.get("rubrics", [])
    positive_points: list[dict] = []
    negative_points: list[dict] = []
    total_possible = 0

    for item in rubrics:
        if hasattr(item, "criterion"):
            criterion = item.criterion
            points = item.points
        else:
            criterion = item.get("criterion", "")
            points = item.get("points", 0)

        entry = {"criterion": criterion, "points": abs(points)}
        if points >= 0:
            positive_points.append(entry)
            total_possible += points
        else:
            entry["points"] = points  # keep negative
            negative_points.append(entry)

    answer_rubric = {
        "positive_points": positive_points,
        "negative_points": negative_points,
        "total_possible_points": total_possible,
    }

    # Retry loop
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = augmenter_model(messages)
            augmentation = parse_augmented_case(response.response_text)

            return {
                "id": prompt_id,
                "conversation": example.get("prompt", []),
                "answer_rubric": answer_rubric,
                "required_tools": augmentation.get("required_tools", ["brain_graph"]),
                "expected_retrieval_topics": augmentation.get(
                    "expected_retrieval_topics", []
                ),
                "reasoning_checkpoints": augmentation.get(
                    "reasoning_checkpoints", []
                ),
                "difficulty": augmentation.get("difficulty", "standard"),
                "source": "healthbench_augmented",
                "tags": example_tags,
            }
        except Exception as exc:
            logger.warning(
                "Augmentation attempt %d/%d failed: %s",
                attempt + 1,
                max_retries,
                exc,
            )

    # Fallback: return with minimal metadata
    logger.error(
        "All augmentation attempts failed for prompt_id=%s. "
        "Returning fallback metadata.",
        prompt_id,
    )
    return {
        "id": prompt_id,
        "conversation": example.get("prompt", []),
        "answer_rubric": answer_rubric,
        "required_tools": ["brain_graph"],
        "expected_retrieval_topics": [],
        "reasoning_checkpoints": [],
        "difficulty": "standard",
        "source": "healthbench_augmented",
        "tags": example_tags,
    }


# ---------------------------------------------------------------------------
# Fresh case generation
# ---------------------------------------------------------------------------


def generate_fresh_case(
    topic: str,
    generator_model: SamplerBase,
) -> dict[str, Any] | None:
    """Generate a fresh agentic test case from a topic string.

    Creates a new multi-step medical question with full agentic metadata
    including conversation, rubric, required tools, retrieval topics,
    reasoning checkpoints, difficulty, and tags.

    Retries up to 3 times on parse failure.  Returns ``None`` on total
    failure.

    Args:
        topic: Health topic string (e.g. "aspirin and cardiovascular risk").
        generator_model: A ``SamplerBase`` instance for the generation LLM.

    Returns:
        Dict with keys: ``id``, ``conversation``, ``answer_rubric``,
        ``required_tools``, ``expected_retrieval_topics``,
        ``reasoning_checkpoints``, ``difficulty``, ``source``, ``tags``.
        Returns ``None`` if all retries fail.
    """
    user_prompt = (
        f"Generate a realistic agentic medical test case about the "
        f"following topic:\n\n{topic}\n\n"
        f"The test case should require multi-step reasoning, tool use, "
        f"and evidence retrieval."
    )

    messages: MessageList = [
        {"role": "system", "content": GENERATION_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = generator_model(messages)
            generated = parse_augmented_case(response.response_text)

            return {
                "id": str(uuid.uuid4()),
                "conversation": generated.get("conversation", []),
                "answer_rubric": generated.get("answer_rubric", {}),
                "required_tools": generated.get("required_tools", ["brain_graph"]),
                "expected_retrieval_topics": generated.get(
                    "expected_retrieval_topics", []
                ),
                "reasoning_checkpoints": generated.get(
                    "reasoning_checkpoints", []
                ),
                "difficulty": generated.get("difficulty", "standard"),
                "source": "generated",
                "tags": generated.get("tags", []),
            }
        except Exception as exc:
            logger.warning(
                "Generation attempt %d/%d failed for topic '%s': %s",
                attempt + 1,
                max_retries,
                topic,
                exc,
            )

    logger.error(
        "All generation attempts failed for topic '%s'. Returning None.",
        topic,
    )
    return None
