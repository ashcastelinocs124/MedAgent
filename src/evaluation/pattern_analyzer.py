"""Analyze HealthBench eval failures, tag patterns, and graduate learnings.

Reads *_allresults.json from a HealthBench run, extracts failed rubric items,
uses GPT-4o to tag each failure with a pattern label, and graduates patterns
that recur >= threshold times into learnings.md.
"""
from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.evaluation.pattern_tracker import PatternTracker


class PatternAnalyzer:
    """Post-eval analyzer that tags failures and graduates recurring patterns.

    Args:
        results_path: Path to the HealthBench *_allresults.json file.
        tracker_path: Path to the pattern_tracker.json file.
        learnings_path: Path to learnings.md for graduated learnings.
        openai_client: OpenAI client for LLM tagging calls. If None, uses env default.
    """

    def __init__(
        self,
        results_path: str | Path,
        tracker_path: str | Path,
        learnings_path: str | Path = "learnings.md",
        openai_client: Any = None,
    ) -> None:
        self._results_path = Path(results_path)
        self._tracker = PatternTracker(storage_path=tracker_path)
        self._learnings_path = Path(learnings_path)
        self._openai = openai_client
        self._results: dict | None = None

    def _load_results(self) -> dict:
        if self._results is None:
            self._results = json.loads(
                self._results_path.read_text(encoding="utf-8")
            )
        return self._results

    def extract_failures(self) -> list[dict[str, Any]]:
        """Extract failed rubric items (criteria_met=False, points>0)."""
        results = self._load_results()
        examples = results.get("metadata", {}).get("example_level_metadata", [])
        failures = []
        for ex in examples:
            prompt_id = ex.get("prompt_id", "unknown")
            query = ""
            for msg in ex.get("prompt", []):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    query = content if isinstance(content, str) else str(content)
            response = ""
            for msg in ex.get("completion", []):
                if msg.get("role") == "assistant":
                    response = msg.get("content", "")
            for rubric in ex.get("rubric_items", []):
                if not rubric.get("criteria_met", True) and rubric.get("points", 0) > 0:
                    failures.append({
                        "prompt_id": prompt_id,
                        "query": query,
                        "response": response[:500],
                        "criterion": rubric["criterion"],
                        "points": rubric["points"],
                        "tags": rubric.get("tags", []),
                        "explanation": rubric.get("explanation", ""),
                    })
        return failures

    def _get_openai(self):
        if self._openai is None:
            from openai import OpenAI
            self._openai = OpenAI()
        return self._openai

    async def tag_failure(self, failure: dict[str, Any]) -> str:
        """Use GPT-4o to tag a failure with a short pattern label."""
        prompt = (
            "You are analyzing a healthcare search system's failures on a medical benchmark.\n\n"
            f"Query: {failure['query']}\n"
            f"Response (truncated): {failure['response']}\n"
            f"Failed criterion: {failure['criterion']}\n"
            f"Grader explanation: {failure['explanation']}\n\n"
            "Tag this failure with a short, reusable snake_case pattern label that captures "
            "the TYPE of mistake (not the specific query). Examples: 'missing_drug_interaction_warning', "
            "'oversimplified_for_clinical_query', 'uncited_statistical_claim', 'missing_side_effects'.\n\n"
            "Respond with only the pattern tag, nothing else."
        )
        client = self._get_openai()
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            max_tokens=30,
            messages=[{"role": "user", "content": prompt}],
        )
        tag = resp.choices[0].message.content.strip().lower().replace(" ", "_").replace("-", "_")
        return tag

    async def check_existing_tags(self, new_tag: str) -> str:
        """Check if new_tag is semantically similar to an existing tag. Merges if so."""
        existing = self._tracker.all_tags()
        if not existing or new_tag in existing:
            return new_tag

        prompt = (
            f"Existing pattern tags: {', '.join(existing)}\n"
            f"New tag: {new_tag}\n\n"
            "Is the new tag semantically the same as any existing tag? "
            "If yes, respond with the existing tag name. If no, respond with the new tag name.\n"
            "Respond with only the tag name, nothing else."
        )
        client = self._get_openai()
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            max_tokens=30,
            messages=[{"role": "user", "content": prompt}],
        )
        result = resp.choices[0].message.content.strip().lower().replace(" ", "_").replace("-", "_")
        return result if result in existing else new_tag

    async def graduate_ready_patterns(self) -> list[str]:
        """Graduate all patterns that have reached the threshold."""
        ready = self._tracker.get_ready_to_graduate()
        graduated = []

        for tag, entry in ready.items():
            examples_text = "\n".join(
                f"- {ex['summary']}" for ex in entry["examples"][:10]
            )
            prompt = (
                "You are improving a healthcare search system. This failure pattern "
                f"has occurred {entry['count']} times:\n\n"
                f"Pattern: {tag}\n"
                f"Examples:\n{examples_text}\n\n"
                "Write a generalized learning (2-3 sentences) explaining:\n"
                "1. What the system consistently gets wrong\n"
                "2. How to avoid this in future responses\n\n"
                "Be specific and actionable. Respond with only the learning text."
            )
            client = self._get_openai()
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            learning_text = resp.choices[0].message.content.strip()

            self._append_learning(tag, learning_text, entry["count"])
            self._tracker.mark_graduated(tag)
            graduated.append(tag)

        return graduated

    def _append_learning(self, tag: str, learning_text: str, count: int) -> None:
        """Append a graduated learning to learnings.md under ## Self-Learning."""
        content = ""
        if self._learnings_path.exists():
            content = self._learnings_path.read_text(encoding="utf-8")

        if "## Self-Learning" not in content:
            content += "\n\n## Self-Learning\n"

        today = date.today().isoformat()
        entry = (
            f"\n### {today} — {tag} (auto-graduated, {count} occurrences)\n"
            f"**Ref:** Evaluation > HealthBench pattern analysis\n"
            f"- **What:** {learning_text}\n"
            f"- **Why it matters:** Recurring failure pattern detected across {count} benchmark examples.\n"
            f"- **Fix/Pattern:** {learning_text}\n"
        )
        content += entry
        self._learnings_path.write_text(content, encoding="utf-8")

    async def analyze(self, run_id: str | None = None) -> dict[str, Any]:
        """Full analysis pipeline: extract -> tag -> dedup -> count -> graduate."""
        failures = self.extract_failures()
        new_tags = 0
        merged_tags = 0

        for failure in failures:
            try:
                raw_tag = await self.tag_failure(failure)
                final_tag = await self.check_existing_tags(raw_tag)

                if final_tag != raw_tag:
                    merged_tags += 1
                if self._tracker.get(final_tag) is None:
                    new_tags += 1

                summary = f"{failure['criterion']}: {failure['explanation'][:100]}"
                self._tracker.add(final_tag, failure["prompt_id"], summary)

                if run_id:
                    self._tracker.update_last_relevant(final_tag, run_id)
            except Exception as e:
                self._tracker.add(
                    "untagged",
                    failure["prompt_id"],
                    f"Tagging failed: {e}. Criterion: {failure['criterion'][:100]}",
                )

        graduated = await self.graduate_ready_patterns()

        return {
            "failures_analyzed": len(failures),
            "new_tags": new_tags,
            "merged_tags": merged_tags,
            "graduated": graduated,
        }
