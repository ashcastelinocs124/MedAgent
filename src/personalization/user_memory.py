"""Per-user short-term memory store with mention-based graduation.

Stores health-relevant facts extracted from user queries that aren't in their
formal profile. Facts graduate to permanent graph changes after 5 mentions.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


_MAX_FACTS = 20
_GRADUATION_THRESHOLD = 5


class UserMemoryStore:
    """Manages per-user short-term and long-term memory files.

    Args:
        base_dir: Base directory for user memory files (e.g., "users/").
    """

    def __init__(self, base_dir: str | Path = "users") -> None:
        self._base = Path(base_dir)

    def _user_dir(self, user_id: str) -> Path:
        return self._base / user_id

    def _stm_path(self, user_id: str) -> Path:
        return self._user_dir(user_id) / "short_term_memory.json"

    def _ltm_path(self, user_id: str) -> Path:
        return self._user_dir(user_id) / "long_term_memory.json"

    def _load_stm(self, user_id: str) -> list[dict[str, Any]]:
        path = self._stm_path(user_id)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return []

    def _save_stm(self, user_id: str, facts: list[dict[str, Any]]) -> None:
        path = self._stm_path(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")

    def _load_ltm(self, user_id: str) -> list[dict[str, Any]]:
        path = self._ltm_path(user_id)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return []

    def _save_ltm(self, user_id: str, entries: list[dict[str, Any]]) -> None:
        path = self._ltm_path(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2, default=str), encoding="utf-8")

    def _find_fact(self, facts: list[dict], fact_text: str) -> int | None:
        lower = fact_text.lower()
        for i, f in enumerate(facts):
            if f["fact"].lower() == lower:
                return i
        return None

    def add_fact(self, user_id: str, fact: str, category: str) -> None:
        """Add a fact or increment its mention count. Graduates at 5 mentions.

        Args:
            user_id: Unique user identifier.
            fact: The health-relevant fact text.
            category: Brain category slug (e.g., "cancer_oncology").
        """
        facts = self._load_stm(user_id)
        idx = self._find_fact(facts, fact)

        if idx is not None:
            facts[idx]["mentions"] += 1
            facts[idx]["last_seen"] = date.today().isoformat()
            if facts[idx]["mentions"] >= _GRADUATION_THRESHOLD:
                self._graduate(user_id, facts.pop(idx))
        else:
            if len(facts) >= _MAX_FACTS:
                facts.sort(key=lambda f: (f["mentions"], f.get("first_seen", "")))
                facts.pop(0)
            facts.append({
                "fact": fact,
                "category": category,
                "mentions": 1,
                "first_seen": date.today().isoformat(),
                "last_seen": date.today().isoformat(),
            })

        self._save_stm(user_id, facts)

    def update_fact(self, user_id: str, old_fact: str, new_fact: str, category: str) -> None:
        """Replace a fact (e.g., contradictory update), resetting mentions to 1.

        Args:
            user_id: Unique user identifier.
            old_fact: The existing fact text to replace.
            new_fact: The replacement fact text.
            category: Brain category slug.
        """
        facts = self._load_stm(user_id)
        idx = self._find_fact(facts, old_fact)
        if idx is not None:
            facts[idx] = {
                "fact": new_fact,
                "category": category,
                "mentions": 1,
                "first_seen": date.today().isoformat(),
                "last_seen": date.today().isoformat(),
            }
        else:
            facts.append({
                "fact": new_fact,
                "category": category,
                "mentions": 1,
                "first_seen": date.today().isoformat(),
                "last_seen": date.today().isoformat(),
            })
        self._save_stm(user_id, facts)

    def get_facts(self, user_id: str) -> list[dict[str, Any]]:
        """Return all short-term memory facts for a user.

        Args:
            user_id: Unique user identifier.

        Returns:
            List of fact dicts with keys: fact, category, mentions, first_seen, last_seen.
        """
        return self._load_stm(user_id)

    def get_graduated(self, user_id: str) -> list[dict[str, Any]]:
        """Return all graduated (long-term) facts for a user.

        Args:
            user_id: Unique user identifier.

        Returns:
            List of graduated fact dicts (includes graduated_at timestamp).
        """
        return self._load_ltm(user_id)

    def _graduate(self, user_id: str, fact_entry: dict[str, Any]) -> None:
        """Move a fact from short-term to long-term memory.

        Args:
            user_id: Unique user identifier.
            fact_entry: The fact dict to graduate.
        """
        ltm = self._load_ltm(user_id)
        fact_entry["graduated_at"] = date.today().isoformat()
        ltm.append(fact_entry)
        self._save_ltm(user_id, ltm)

    def get_novel_facts(
        self, user_id: str, profile_conditions: list[str], profile_medications: list[str]
    ) -> list[dict[str, Any]]:
        """Return facts that are NOT already in the user's profile.

        A fact is considered "in profile" if any profile condition or medication
        is a substring of the fact (or vice versa), case-insensitive.

        Args:
            user_id: Unique user identifier.
            profile_conditions: List of condition strings from the user profile.
            profile_medications: List of medication strings from the user profile.

        Returns:
            List of fact dicts not matching any profile entry.
        """
        facts = self._load_stm(user_id)
        profile_lower = {c.lower() for c in profile_conditions} | {m.lower() for m in profile_medications}
        novel = []
        for f in facts:
            fact_lower = f["fact"].lower()
            is_in_profile = any(p in fact_lower or fact_lower in p for p in profile_lower)
            if not is_in_profile:
                novel.append(f)
        return novel
