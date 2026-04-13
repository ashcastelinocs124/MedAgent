"""Track recurring failure patterns from HealthBench eval runs.

Stores pattern tags with occurrence counts, example references, and graduation
status. Patterns graduate to learnings.md when they hit the configured threshold.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


_DEFAULT_THRESHOLD = 5


class PatternTracker:
    """Tag-and-count tracker for recurring eval failure patterns.

    Args:
        storage_path: Path to the JSON file for persistence.
        threshold: Number of occurrences before a pattern is ready to graduate.
    """

    def __init__(
        self,
        storage_path: str | Path,
        threshold: int = _DEFAULT_THRESHOLD,
    ) -> None:
        self._path = Path(storage_path)
        self._threshold = threshold
        self._data: dict[str, dict[str, Any]] = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def add(self, tag: str, example_id: str, example_summary: str) -> None:
        """Record one occurrence of a failure pattern."""
        if tag not in self._data:
            self._data[tag] = {
                "count": 0,
                "examples": [],
                "graduated": False,
                "ready_to_graduate": False,
                "last_relevant": None,
                "graduated_at": None,
            }
        entry = self._data[tag]
        entry["count"] += 1
        entry["examples"].append({
            "example_id": example_id,
            "summary": example_summary,
            "timestamp": datetime.now().isoformat(),
        })
        entry["ready_to_graduate"] = entry["count"] >= self._threshold and not entry["graduated"]
        self.save()

    def get(self, tag: str) -> dict[str, Any] | None:
        """Get a pattern entry by tag name."""
        return self._data.get(tag)

    def mark_graduated(self, tag: str) -> None:
        """Mark a pattern as graduated (written to learnings.md)."""
        if tag in self._data:
            self._data[tag]["graduated"] = True
            self._data[tag]["ready_to_graduate"] = False
            self._data[tag]["graduated_at"] = datetime.now().isoformat()
            self.save()

    def get_ready_to_graduate(self) -> dict[str, dict[str, Any]]:
        """Return all patterns at threshold that haven't graduated yet."""
        return {
            tag: entry for tag, entry in self._data.items()
            if entry.get("ready_to_graduate", False)
        }

    def update_last_relevant(self, tag: str, run_id: str) -> None:
        """Record that this pattern was seen in a specific eval run."""
        if tag in self._data:
            self._data[tag]["last_relevant"] = run_id
            self.save()

    def get_stale(self, current_run_number: int, stale_threshold: int = 20) -> list[str]:
        """Return graduated patterns not seen in stale_threshold runs."""
        stale = []
        for tag, entry in self._data.items():
            if not entry.get("graduated"):
                continue
            last = entry.get("last_relevant")
            if last is None:
                stale.append(tag)
                continue
            try:
                last_num = int(last.split("_")[-1])
                if current_run_number - last_num >= stale_threshold:
                    stale.append(tag)
            except (ValueError, IndexError):
                pass
        return stale

    def all_tags(self) -> list[str]:
        """Return all tracked pattern tags."""
        return list(self._data.keys())

    def save(self) -> None:
        """Persist tracker to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, default=str),
            encoding="utf-8",
        )
