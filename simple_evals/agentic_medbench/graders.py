"""Grader agents for Agentic MedBench evaluation.

Provides five specialist graders, each evaluating a different dimension of an
agent's execution trace:

1. **AnswerGrader** -- final answer quality against an answer rubric.
2. **ToolGrader** -- whether the agent selected the right tools.
3. **RetrievalGrader** -- topic coverage and relevance of retrieved evidence.
4. **ReasoningGrader** -- checkpoint hit rate and logical coherence.
5. **SelfCorrectionGrader** -- ability to catch and fix its own errors.

All graders share a common ``BaseGrader`` ABC that handles model invocation,
retry logic, response parsing, and score clipping.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from ..types import SamplerBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Maximum retry attempts for grader model calls
# ---------------------------------------------------------------------------

_MAX_RETRIES: int = 3

# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _parse_grader_response(text: str) -> dict[str, Any]:
    """Parse a grader model's response into a structured dict.

    Handles three common formats:
    1. Raw JSON string.
    2. JSON wrapped in markdown code fences (````` ```json ... ``` `````).
    3. JSON object embedded in surrounding prose.

    Args:
        text: Raw text from the grader model.

    Returns:
        Parsed dict.  On any parse failure the function returns
        ``{"score": 0.0, "explanation": "<error message>"}``.
    """
    if not text or not text.strip():
        return {"score": 0.0, "explanation": "Empty grader response."}

    cleaned = text.strip()

    # Attempt 1: strip markdown code fences
    fence_pattern = re.compile(
        r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL
    )
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # Attempt 2: try to parse the (possibly fence-stripped) text directly
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            parsed.setdefault("score", 0.0)
            parsed.setdefault("explanation", "")
            return parsed
    except json.JSONDecodeError:
        pass

    # Attempt 3: find the first JSON object embedded in prose
    obj_pattern = re.compile(r"\{[^{}]*\}", re.DOTALL)
    obj_match = obj_pattern.search(text)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group(0))
            if isinstance(parsed, dict):
                parsed.setdefault("score", 0.0)
                parsed.setdefault("explanation", "")
                return parsed
        except json.JSONDecodeError:
            pass

    return {"score": 0.0, "explanation": f"Failed to parse grader output: {text[:200]}"}


# ---------------------------------------------------------------------------
# Base grader
# ---------------------------------------------------------------------------


class BaseGrader(ABC):
    """Abstract base class for all grader agents.

    Subclasses must define ``system_prompt`` and implement
    ``build_user_prompt``.  The ``grade`` method handles model invocation,
    retry logic (up to ``_MAX_RETRIES``), response parsing, and score
    clipping to [0, 1].
    """

    system_prompt: str

    @abstractmethod
    def build_user_prompt(self, agent_trace: dict, test_case: dict) -> str:
        """Build the user-role prompt from an agent trace and test case.

        Args:
            agent_trace: Dict with keys ``final_answer``, ``tool_calls``,
                ``reasoning_trace``, ``corrections``, ``retrieval_results``.
            test_case: Dict with rubric / checkpoint fields relevant to
                this grader dimension.

        Returns:
            A formatted prompt string.
        """

    def grade(
        self,
        agent_trace: dict,
        test_case: dict,
        grader_model: SamplerBase,
    ) -> dict[str, Any]:
        """Grade an agent trace by calling the grader model.

        Retries up to ``_MAX_RETRIES`` times if the model response cannot
        be parsed into valid JSON containing a ``score`` field.  The final
        score is clipped to [0, 1].

        Args:
            agent_trace: The agent's execution trace.
            test_case: The test case with rubric/checkpoint data.
            grader_model: A ``SamplerBase`` instance used to generate
                the grading evaluation.

        Returns:
            Dict with at least ``score`` (float) and ``explanation`` (str).
        """
        user_prompt = self.build_user_prompt(agent_trace, test_case)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_result: dict[str, Any] = {
            "score": 0.0,
            "explanation": "All grader retries exhausted.",
        }

        for attempt in range(_MAX_RETRIES):
            try:
                response = grader_model(messages)
                parsed = _parse_grader_response(response.response_text)

                # A parsed result with score > 0 (or explicit 0) is valid
                # as long as parsing didn't fail outright.
                if "Failed to parse" not in parsed.get("explanation", ""):
                    parsed["score"] = max(0.0, min(1.0, float(parsed["score"])))
                    return parsed

                last_result = parsed
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Grader attempt %d/%d failed: %s",
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                )
                last_result = {
                    "score": 0.0,
                    "explanation": f"Grader error: {exc}",
                }

        # All retries exhausted -- clip and return the last result
        last_result["score"] = max(0.0, min(1.0, float(last_result["score"])))
        return last_result


# ---------------------------------------------------------------------------
# AnswerGrader
# ---------------------------------------------------------------------------


class AnswerGrader(BaseGrader):
    """Grades the agent's final answer against an answer rubric.

    Evaluates each rubric criterion (positive and negative points) and
    computes ``score = achieved_points / total_possible_points``.
    """

    system_prompt: str = (
        "You are an expert medical answer grader. You will receive an agent's "
        "final answer and a detailed rubric with positive and negative scoring "
        "criteria.\n\n"
        "Instructions:\n"
        "1. Evaluate the answer against EACH rubric criterion.\n"
        "2. For positive points: award the full points if the criterion is met, "
        "0 if not.\n"
        "3. For negative points: apply the penalty if the criterion is violated.\n"
        "4. Compute: score = max(0, achieved_points) / total_possible_points\n"
        "5. Clip the score to [0, 1].\n\n"
        "Respond with a JSON object:\n"
        '{"score": <float 0-1>, "explanation": "<detailed evaluation>"}'
    )

    def build_user_prompt(self, agent_trace: dict, test_case: dict) -> str:
        final_answer = agent_trace.get("final_answer", "(no answer provided)")
        rubric = test_case.get("answer_rubric", {})

        positive = rubric.get("positive_points", [])
        negative = rubric.get("negative_points", [])
        total = rubric.get("total_possible_points", "unknown")

        positive_text = "\n".join(
            f"  - [{p.get('points', 0)} pts] {p.get('criterion', '')}"
            for p in positive
        )
        negative_text = "\n".join(
            f"  - [{p.get('points', 0)} pts] {p.get('criterion', '')}"
            for p in negative
        )

        return (
            f"## Agent's Final Answer\n{final_answer}\n\n"
            f"## Answer Rubric\n"
            f"Total possible points: {total}\n\n"
            f"### Positive criteria:\n{positive_text}\n\n"
            f"### Negative criteria:\n{negative_text}\n\n"
            "Evaluate the answer against every criterion and return your "
            "JSON verdict."
        )


# ---------------------------------------------------------------------------
# ToolGrader
# ---------------------------------------------------------------------------


class ToolGrader(BaseGrader):
    """Grades whether the agent selected and used the correct tools.

    Evaluates whether the agent called all required tools and whether the
    arguments passed to each tool were appropriate.
    """

    system_prompt: str = (
        "You are an expert tool-usage grader for a medical QA agent. You will "
        "receive the agent's tool call log and the list of required tools.\n\n"
        "Instructions:\n"
        "1. Check whether EACH required tool was called.\n"
        "2. Evaluate whether the arguments passed to each tool were appropriate "
        "for the medical question.\n"
        "3. Note any unnecessary or harmful tool calls.\n"
        "4. Compute a score from 0 to 1 reflecting tool selection quality.\n\n"
        "Respond with a JSON object:\n"
        '{"score": <float 0-1>, "explanation": "<evaluation>", '
        '"required_tools_used": [<list>], "required_tools_missed": [<list>]}'
    )

    def build_user_prompt(self, agent_trace: dict, test_case: dict) -> str:
        tool_calls = agent_trace.get("tool_calls", [])
        required_tools = test_case.get("required_tools", [])

        calls_text = ""
        for i, tc in enumerate(tool_calls, 1):
            calls_text += (
                f"  {i}. Tool: {tc.get('tool_name', 'unknown')}\n"
                f"     Arguments: {json.dumps(tc.get('arguments', {}))}\n"
                f"     Result: {tc.get('result', '(no result)')}\n\n"
            )

        if not calls_text:
            calls_text = "  (no tool calls recorded)\n"

        required_text = ", ".join(required_tools) if required_tools else "(none specified)"

        return (
            f"## Agent's Tool Calls\n{calls_text}\n"
            f"## Required Tools\n{required_text}\n\n"
            "Evaluate tool selection and return your JSON verdict."
        )


# ---------------------------------------------------------------------------
# RetrievalGrader
# ---------------------------------------------------------------------------


class RetrievalGrader(BaseGrader):
    """Grades the quality and coverage of the agent's retrieved evidence.

    Evaluates whether the retrieval results cover the expected topics and
    whether the retrieved content is relevant to the medical question.
    """

    system_prompt: str = (
        "You are an expert retrieval quality grader for a medical QA agent. "
        "You will receive the agent's retrieval results and the expected "
        "retrieval topics.\n\n"
        "Instructions:\n"
        "1. Check topic coverage: how many expected topics are represented "
        "in the retrieved results?\n"
        "2. Evaluate relevance: are the retrieved items actually relevant to "
        "the expected topics?\n"
        "3. Note any critical topics that were missed.\n"
        "4. Compute a score from 0 to 1 reflecting retrieval quality.\n\n"
        "Respond with a JSON object:\n"
        '{"score": <float 0-1>, "explanation": "<evaluation>"}'
    )

    def build_user_prompt(self, agent_trace: dict, test_case: dict) -> str:
        retrieval_results = agent_trace.get("retrieval_results", [])
        expected_topics = test_case.get("expected_retrieval_topics", [])

        results_text = ""
        for i, rr in enumerate(retrieval_results, 1):
            results_text += (
                f"  {i}. Source: {rr.get('source', 'unknown')}\n"
                f"     Content: {rr.get('content', '(empty)')}\n"
                f"     Relevance score: {rr.get('relevance_score', 'N/A')}\n\n"
            )

        if not results_text:
            results_text = "  (no retrieval results recorded)\n"

        topics_text = "\n".join(f"  - {t}" for t in expected_topics) if expected_topics else "  (none specified)"

        return (
            f"## Agent's Retrieval Results\n{results_text}\n"
            f"## Expected Retrieval Topics\n{topics_text}\n\n"
            "Evaluate retrieval coverage and relevance, then return your "
            "JSON verdict."
        )


# ---------------------------------------------------------------------------
# ReasoningGrader
# ---------------------------------------------------------------------------


class ReasoningGrader(BaseGrader):
    """Grades the agent's reasoning trace against expected checkpoints.

    Evaluates checkpoint hit rate (how many expected reasoning steps were
    demonstrated) and overall logical coherence of the reasoning chain.
    """

    system_prompt: str = (
        "You are an expert reasoning quality grader for a medical QA agent. "
        "You will receive the agent's reasoning trace and the expected "
        "reasoning checkpoints.\n\n"
        "Instructions:\n"
        "1. Check checkpoint hit rate: for each expected checkpoint, determine "
        "whether the agent's reasoning demonstrates that step.\n"
        "2. Evaluate logical coherence: does the reasoning flow logically "
        "from question to answer?\n"
        "3. Note any critical reasoning gaps.\n"
        "4. Compute a score from 0 to 1 reflecting reasoning quality.\n\n"
        "Respond with a JSON object:\n"
        '{"score": <float 0-1>, "explanation": "<evaluation>"}'
    )

    def build_user_prompt(self, agent_trace: dict, test_case: dict) -> str:
        reasoning_trace = agent_trace.get("reasoning_trace", [])
        checkpoints = test_case.get("reasoning_checkpoints", [])

        trace_text = ""
        for i, step in enumerate(reasoning_trace, 1):
            trace_text += f"  {i}. {step}\n"

        if not trace_text:
            trace_text = "  (no reasoning trace recorded)\n"

        checkpoint_text = "\n".join(
            f"  - {cp}" for cp in checkpoints
        ) if checkpoints else "  (none specified)"

        return (
            f"## Agent's Reasoning Trace\n{trace_text}\n"
            f"## Expected Reasoning Checkpoints\n{checkpoint_text}\n\n"
            "Evaluate checkpoint coverage and logical coherence, then return "
            "your JSON verdict."
        )


# ---------------------------------------------------------------------------
# SelfCorrectionGrader
# ---------------------------------------------------------------------------


class SelfCorrectionGrader(BaseGrader):
    """Grades the agent's ability to catch and correct its own errors.

    Score guide:
    - **1.0** if the agent caught all its errors, or if there were no errors
      to correct.
    - **0.5** if some errors were caught but others were missed.
    - **0.0** if clear errors were present in the reasoning but not corrected.
    """

    system_prompt: str = (
        "You are an expert self-correction grader for a medical QA agent. "
        "You will receive the agent's corrections, reasoning trace, and final "
        "answer.\n\n"
        "Instructions:\n"
        "1. Review the reasoning trace for any errors, mistakes, or "
        "inaccuracies.\n"
        "2. Check whether the agent's corrections address those errors.\n"
        "3. Examine the final answer for any uncorrected errors.\n"
        "4. Score guide:\n"
        "   - 1.0: All errors were caught and corrected, OR there were no "
        "errors to correct.\n"
        "   - 0.5: Some errors were caught but others were missed.\n"
        "   - 0.0: Clear errors were present but not corrected.\n\n"
        "Respond with a JSON object:\n"
        '{"score": <float 0-1>, "explanation": "<evaluation>"}'
    )

    def build_user_prompt(self, agent_trace: dict, test_case: dict) -> str:
        corrections = agent_trace.get("corrections", [])
        reasoning_trace = agent_trace.get("reasoning_trace", [])
        final_answer = agent_trace.get("final_answer", "(no answer provided)")

        corrections_text = ""
        for i, c in enumerate(corrections, 1):
            corrections_text += (
                f"  {i}. Original: {c.get('original', '')}\n"
                f"     Corrected: {c.get('corrected', '')}\n"
                f"     Reason: {c.get('reason', '')}\n\n"
            )

        if not corrections_text:
            corrections_text = "  (no corrections recorded)\n"

        trace_text = ""
        for i, step in enumerate(reasoning_trace, 1):
            trace_text += f"  {i}. {step}\n"

        if not trace_text:
            trace_text = "  (no reasoning trace recorded)\n"

        return (
            f"## Agent's Corrections\n{corrections_text}\n"
            f"## Reasoning Trace\n{trace_text}\n"
            f"## Final Answer\n{final_answer}\n\n"
            "Evaluate the agent's self-correction ability and return your "
            "JSON verdict."
        )


# ---------------------------------------------------------------------------
# Convenience: run all graders
# ---------------------------------------------------------------------------

# Mapping from dimension key to grader class
_DIMENSION_GRADERS: dict[str, BaseGrader] = {
    "answer_quality": AnswerGrader(),
    "tool_selection": ToolGrader(),
    "retrieval_quality": RetrievalGrader(),
    "reasoning_trace": ReasoningGrader(),
    "self_correction": SelfCorrectionGrader(),
}


def grade_all_dimensions(
    agent_trace: dict,
    test_case: dict,
    grader_model: SamplerBase,
) -> dict[str, dict]:
    """Run all five grader agents and return per-dimension results.

    Args:
        agent_trace: The agent's full execution trace dict.
        test_case: The test case with rubric/checkpoint data.
        grader_model: A ``SamplerBase`` instance for the grading LLM.

    Returns:
        Dict mapping dimension name to its grading result.  Keys:
        ``"answer_quality"``, ``"tool_selection"``, ``"retrieval_quality"``,
        ``"reasoning_trace"``, ``"self_correction"``.  Each value is a dict
        with at least ``"score"`` and ``"explanation"``.
    """
    results: dict[str, dict] = {}

    for dim_name, grader in _DIMENSION_GRADERS.items():
        results[dim_name] = grader.grade(agent_trace, test_case, grader_model)

    return results
