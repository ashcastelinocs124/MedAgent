"""LLM-augmented profile intake — GPT-4o weight review and clarification.

Uses GPT-4o to review a user's health profile against the pipeline's baseline
category weights, propose adjustments, and optionally ask 1-2 clarifying
questions.  All proposed changes are clamped by guardrail constants before
being applied.

Silent fallback: if any GPT-4o call fails (timeout, API error, unparseable
JSON), the system returns {} and the caller falls back to the pipeline's
baseline weights.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from src.personalization.models import UserProfile

logger = logging.getLogger(__name__)

# ── Guardrail Constants ────────────────────────────────────────────────────

_MAX_BOOST: float = 0.30       # LLM can increase a weight by at most +0.30
_MAX_REDUCTION: float = 0.20   # LLM can decrease a weight by at most -0.20
_WEIGHT_FLOOR: float = 0.05    # No category gets zeroed out
_WEIGHT_CEILING: float = 0.95  # No category gets maxed

# ── System Prompts ─────────────────────────────────────────────────────────

REVIEW_SYSTEM_PROMPT: str = """\
You are a clinical reasoning assistant that reviews a patient's health profile \
and the personalization pipeline's baseline category weights. Your job is to \
identify categories where the pipeline's weights are materially wrong given the \
patient's clinical picture, and either adjust them or ask a brief clarifying \
question.

Rules:
1. Only adjust categories where the delta from baseline would be > 0.10. Do not \
adjust for the sake of it.
2. Ask at most 1-2 clarifying questions, and ONLY when a missing piece of \
information would swing a weight by 0.15 or more.
3. When to ask:
   - A comorbidity interaction is likely but unconfirmed (e.g. diabetes -> \
kidney status unknown).
   - The profile has a gap that contradicts medical norms (e.g. hypertension \
but no cardiac medications).
   - Age + condition implies a screening need the pipeline missed.
4. When NOT to ask:
   - The pipeline weights already look reasonable for the profile.
   - The potential delta is < 0.10.
   - Health literacy is LOW and the question would require medical knowledge \
to answer.
   - The answer is already implied by something in the profile.
5. Respect the patient's health literacy level when phrasing questions. Use \
plain, simple language for LOW literacy.
6. For each question, include a "why" field with your clinical reasoning (this \
is NOT shown to the patient — it is passed to the follow-up call).
7. Include "preliminary_adjustments" for categories you are already confident \
about, even if you also have questions about other categories.

Respond with ONLY a JSON object (no markdown fences, no commentary) in one of \
these formats:

No questions needed:
{
  "needs_clarification": false,
  "adjustments": {
    "<category_id>": {"weight": <float>, "reason": "<brief clinical reason>"}
  }
}

Questions needed:
{
  "needs_clarification": true,
  "questions": [
    {
      "question": "<plain-language question for the patient>",
      "target_categories": ["<category_id>"],
      "options": ["Yes", "No", "Not sure"],
      "why": "<your clinical reasoning for asking — not shown to patient>"
    }
  ],
  "preliminary_adjustments": {
    "<category_id>": {"weight": <float>, "reason": "<brief clinical reason>"}
  }
}
"""

CLARIFY_SYSTEM_PROMPT: str = """\
You are a clinical reasoning assistant completing a follow-up review. You \
previously reviewed this patient's profile, asked clarifying questions, and \
made preliminary weight adjustments. Now the patient has answered your \
questions.

Your prior reasoning is provided below. Trust it and build on it — do not \
re-derive the clinical logic from scratch.

Rules:
1. If the patient confirmed a suspected comorbidity, apply the weight boost \
you were considering.
2. If the patient denied, leave the weight closer to baseline or give a \
smaller screening-level bump (0.05-0.10 at most).
3. If the patient answered "Not sure", treat it as a mild positive — apply a \
moderate bump (0.10-0.15) since the risk is unconfirmed but not ruled out.
4. Do not re-adjust preliminary categories unless the patient's answer changes \
that reasoning too.
5. No more questions — this is the final round.
6. Respond with ONLY a JSON object (no markdown fences, no commentary):

{
  "adjustments": {
    "<category_id>": {"weight": <float>, "reason": "<brief clinical reason>"}
  }
}
"""


# ── Pure-Python Helpers ────────────────────────────────────────────────────

def _clamp_adjustments(
    adjustments: dict[str, dict[str, Any]],
    baseline_weights: dict[str, float],
) -> dict[str, float]:
    """Apply guardrails to LLM-proposed weight adjustments.

    For each category in *adjustments*:
      1. Compute delta = proposed_weight - baseline (baseline defaults to 0.0
         for unknown categories).
      2. Clamp delta to [-_MAX_REDUCTION, +_MAX_BOOST].
      3. Clamp the resulting weight to [_WEIGHT_FLOOR, _WEIGHT_CEILING].

    Returns a dict of category_id -> clamped weight (float).
    """
    if not adjustments:
        return {}

    clamped: dict[str, float] = {}
    for cat_id, adj in adjustments.items():
        proposed = adj.get("weight", 0.0)
        base = baseline_weights.get(cat_id, 0.0)
        delta = proposed - base
        clamped_delta = max(-_MAX_REDUCTION, min(delta, _MAX_BOOST))
        final = max(_WEIGHT_FLOOR, min(base + clamped_delta, _WEIGHT_CEILING))
        # Round to avoid floating-point noise
        clamped[cat_id] = round(final, 4)
    return clamped


def _parse_response(text: str) -> dict:
    """Extract a JSON object from LLM response text.

    Handles three common patterns:
      1. Clean JSON string
      2. JSON wrapped in ```json ... ``` markdown fences
      3. JSON preceded by leading commentary text

    Returns an empty dict if no valid JSON can be parsed.
    """
    if not text or not text.strip():
        return {}

    # Strategy 1: Try parsing the whole string as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find the first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def _format_profile(profile: UserProfile) -> str:
    """Format a UserProfile as human-readable text for the LLM prompt."""
    lines = [
        f"Age: {profile.age or 'unknown'}",
        f"Sex: {profile.sex.value if profile.sex else 'unknown'}",
        f"Health literacy: {profile.health_literacy.value if profile.health_literacy else 'unknown'}",
    ]

    if profile.conditions:
        cond_strs = [
            f"  - {c.name} ({c.category_id})"
            for c in profile.conditions
        ]
        lines.append("Conditions:\n" + "\n".join(cond_strs))
    else:
        lines.append("Conditions: none reported")

    if profile.medications:
        med_strs = [
            f"  - {m.name} ({m.category_id})"
            for m in profile.medications
        ]
        lines.append("Medications:\n" + "\n".join(med_strs))
    else:
        lines.append("Medications: none reported")

    return "\n".join(lines)


def _format_weights(weights: dict[str, float]) -> str:
    """Format category weights as text, sorted descending by weight."""
    sorted_items = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    return "\n".join(
        f"{cat_id}: {weight:.2f}" for cat_id, weight in sorted_items
    )


# ── Async GPT-4o Functions ────────────────────────────────────────────────

async def review_profile(
    openai_client: Any,
    profile: UserProfile,
    effective_weights: dict[str, float],
) -> dict:
    """Call GPT-4o to review the profile against pipeline weights.

    Returns the parsed LLM response with clamped adjustments added under
    ``_clamped_adjustments`` (if needs_clarification is False) or
    ``_clamped_preliminary`` (if True).

    Returns {} on any failure (API error, timeout, unparseable JSON).
    """
    try:
        user_msg = (
            "## User Profile\n"
            f"{_format_profile(profile)}\n\n"
            "## Pipeline Weights\n"
            f"{_format_weights(effective_weights)}"
        )

        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o",
            temperature=0.2,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )

        text = response.choices[0].message.content
        result = _parse_response(text)
        if not result:
            logger.warning("review_profile: unparseable LLM response")
            return {}

        # Apply guardrails to whichever adjustments are present
        if result.get("needs_clarification"):
            prelim = result.get("preliminary_adjustments", {})
            result["_clamped_preliminary"] = _clamp_adjustments(
                prelim, effective_weights,
            )
        else:
            adjs = result.get("adjustments", {})
            result["_clamped_adjustments"] = _clamp_adjustments(
                adjs, effective_weights,
            )

        return result

    except Exception:
        logger.exception("review_profile: GPT-4o call failed, falling back")
        return {}


async def apply_answers(
    openai_client: Any,
    profile: UserProfile,
    effective_weights: dict[str, float],
    review_result: dict,
    user_answers: list[str],
) -> dict[str, float]:
    """Call GPT-4o with the user's answers to clarifying questions.

    Builds the prompt with the full prior reasoning chain (question ``why``
    fields and preliminary adjustment reasons) so the LLM can resolve its
    clinical hypotheses with the user's answers rather than reasoning from
    scratch.

    Returns a dict of category_id -> clamped weight (float).
    Returns {} on any failure.
    """
    try:
        # Build the "Your Prior Review" section
        prior_lines: list[str] = []

        # Preliminary adjustments
        prelim = review_result.get("preliminary_adjustments", {})
        if prelim:
            prior_lines.append("### Preliminary adjustments (already applied)")
            for cat_id, adj in prelim.items():
                reason = adj.get("reason", "")
                weight = adj.get("weight", "")
                prior_lines.append(f"  {cat_id}: {weight} -- {reason}")
        else:
            prior_lines.append("### Preliminary adjustments (already applied)")
            prior_lines.append("  None")

        # Questions and answers
        questions = review_result.get("questions", [])
        prior_lines.append("\n### Questions asked and your reasoning")
        for i, q in enumerate(questions):
            answer = user_answers[i] if i < len(user_answers) else "No answer"
            prior_lines.append(f"Q: {q.get('question', '')}")
            targets = ", ".join(q.get("target_categories", []))
            prior_lines.append(f"Target categories: {targets}")
            prior_lines.append(
                f"Your reasoning for asking: {q.get('why', 'N/A')}"
            )
            prior_lines.append(f"User's answer: {answer}")

        user_msg = (
            "## User Profile\n"
            f"{_format_profile(profile)}\n\n"
            "## Pipeline Weights\n"
            f"{_format_weights(effective_weights)}\n\n"
            "## Your Prior Review\n"
            + "\n".join(prior_lines)
        )

        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o",
            temperature=0.2,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": CLARIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )

        text = response.choices[0].message.content
        result = _parse_response(text)
        if not result:
            logger.warning("apply_answers: unparseable LLM response")
            return {}

        adjs = result.get("adjustments", {})
        return _clamp_adjustments(adjs, effective_weights)

    except Exception:
        logger.exception("apply_answers: GPT-4o call failed, falling back")
        return {}
