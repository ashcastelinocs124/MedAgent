"""LLM-assisted comorbidity inference for condition pairs not in static tables.

Called only when condition pairs are NOT in COMORBIDITY_PAIRS.
Results are cached per unique sorted condition set.
All LLM-inferred boosts are capped at 0.20.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

MAX_LLM_BOOST = 0.20


@dataclass
class InferredComorbidity:
    """A comorbidity relationship discovered via LLM inference."""

    condition_a: str
    condition_b: str
    related_categories: list[str]
    boost: float
    reasoning: str


class ComorbidityInference:
    """Discovers cross-condition relationships using the Anthropic API."""

    def __init__(self, client: Optional[object] = None, model: str = "claude-sonnet-4-5-20250929") -> None:
        self.client = client
        self.model = model
        self._cache: dict[frozenset[str], list[InferredComorbidity]] = {}

    def infer(
        self,
        condition_a: str,
        condition_b: str,
        available_categories: list[str],
    ) -> list[InferredComorbidity]:
        """Infer comorbidity relationships between two conditions.

        Args:
            condition_a: First condition name.
            condition_b: Second condition name.
            available_categories: List of category slugs that exist in the graph.

        Returns:
            List of InferredComorbidity objects with boost values capped at 0.20.
        """
        cache_key = frozenset({condition_a, condition_b})
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.client is None:
            self._cache[cache_key] = []
            return []

        results = self._call_llm(condition_a, condition_b, available_categories)
        self._cache[cache_key] = results
        return results

    def _call_llm(
        self,
        condition_a: str,
        condition_b: str,
        available_categories: list[str],
    ) -> list[InferredComorbidity]:
        """Call the Anthropic API to discover comorbidity relationships."""
        prompt = (
            f"Given a patient with both '{condition_a}' and '{condition_b}', "
            f"identify which of these health categories become MORE clinically "
            f"relevant due to the interaction of these two conditions:\n\n"
            f"Available categories: {', '.join(available_categories)}\n\n"
            f"For each relevant category, provide:\n"
            f"1. The category name (must be from the list above)\n"
            f"2. A clinical relevance score from 0.05 to 0.20\n"
            f"3. Brief clinical reasoning\n\n"
            f"Respond in JSON format:\n"
            f'[{{"category": "...", "score": 0.XX, "reasoning": "..."}}]\n\n'
            f"Only include categories where the COMBINATION of both conditions "
            f"creates additional risk beyond either condition alone. "
            f"Return an empty list [] if no significant interaction exists."
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            # Extract JSON from response (handle markdown code blocks)
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            items = json.loads(text)
            results = []
            for item in items:
                cat = item.get("category", "")
                if cat not in available_categories:
                    continue
                score = min(float(item.get("score", 0.10)), MAX_LLM_BOOST)
                results.append(InferredComorbidity(
                    condition_a=condition_a,
                    condition_b=condition_b,
                    related_categories=[cat],
                    boost=score,
                    reasoning=item.get("reasoning", ""),
                ))
            return results

        except Exception:
            return []
