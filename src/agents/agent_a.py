# src/agents/agent_a.py
"""Query Understanding Agent (Agent A).

Classifies an incoming consumer health query into a brain category slug using a
three-step cascade:

  1. Keyword match — terminology maps parsed from brain/categories/*.md
  2. Embedding similarity — cosine distance against per-category centroids
  3. LLM fallback — GPT-4o classifies from a list of known category slugs

Falls back to ``public_health_prevention`` on any unrecoverable error.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

import numpy as np

from src.agents.context import QueryContext

_DEFAULT_CATEGORY = "public_health_prevention"
_EMBED_MODEL = "text-embedding-3-small"
_EMBED_THRESHOLD = 0.65
_MIN_CENTROID_RECORDS = 50

# Minimum word length to register as a standalone keyword token.
_MIN_TOKEN_LEN = 4

# Stop-words that are too generic to be useful category signals.
_STOP_WORDS = {
    "with", "from", "this", "that", "have", "been", "will", "your",
    "they", "their", "what", "when", "where", "which", "about", "into",
    "more", "some", "also", "does", "very", "just", "than", "then",
    "such", "each", "most", "over", "like", "used", "been", "both",
    "only", "well", "even", "here", "much", "many", "same", "these",
}


class QueryUnderstandingAgent:
    """Agent A — Query Understanding.

    Args:
        db_conn: Active psycopg2 connection (or ``None`` for keyword-only mode).
        openai_client: Initialised ``openai.OpenAI`` client (or ``None``).
        anthropic_client: Deprecated, ignored. Kept for backward compatibility.
        brain_dir: Path to the ``brain/`` directory (default ``"brain"``).
    """

    def __init__(
        self,
        db_conn,
        openai_client: "OpenAI | None",
        anthropic_client: object | None = None,  # deprecated, ignored
        brain_dir: str = "brain",
        memory_store=None,
    ) -> None:
        self._db = db_conn
        self._openai = openai_client
        self._brain_dir = Path(brain_dir)
        self._memory_store = memory_store

        # consumer_phrase → category_slug  (full phrase, for substring match)
        self._phrase_map: dict[str, str] = {}

        # keyword_token → {category_slug: hit_count}  (individual tokens, for
        # token-presence match; aggregated to handle ties)
        self._token_map: dict[str, dict[str, int]] = {}

        # category_slug → list of medical terms (from brain terminology maps)
        # Used to seed query expansion with domain-specific clinical vocabulary.
        self._medical_terms: dict[str, list[str]] = {}

        # category_slug → mean embedding vector
        self._centroids: dict[str, np.ndarray] = {}

        # ordered list of all known category slugs
        self._categories: list[str] = []

        self._load_terminology_maps()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_term(self, consumer_term: str, category_slug: str) -> None:
        """Register a consumer term and its individual tokens for a category."""
        phrase = consumer_term.lower().strip()
        if not phrase:
            return

        # Full phrase — substring match (highest precision)
        self._phrase_map[phrase] = category_slug

        # Individual tokens — presence-based match (higher recall)
        for raw_token in re.split(r"[\s/\-,]+", phrase):
            token = raw_token.strip("()[].'\"")
            if len(token) >= _MIN_TOKEN_LEN and token not in _STOP_WORDS:
                bucket = self._token_map.setdefault(token, {})
                bucket[category_slug] = bucket.get(category_slug, 0) + 1

    def _load_terminology_maps(self) -> None:
        """Parse ``## Terminology Map`` sections from all brain category files.

        The section uses a markdown table::

            | Consumer Term | Medical Term | Notes |
            |--------------|-------------|-------|
            | heart attack  | myocardial infarction (MI) | ... |

        Both full phrases and individual significant tokens are indexed so that
        queries like "chest pain and heart palpitations" match ``heart_blood_vessels``
        even when the exact phrase "heart palpitations" is not in the table (because
        "heart" is a token found across multiple consumer terms in that category).
        """
        cat_dir = self._brain_dir / "categories"
        if not cat_dir.exists():
            return

        for md_file in sorted(cat_dir.glob("*.md")):
            slug = md_file.stem
            if slug not in self._categories:
                self._categories.append(slug)

            text = md_file.read_text(encoding="utf-8")
            in_section = False
            header_skipped = False  # skip `| Consumer Term | ... |` header row
            separator_skipped = False  # skip `|---|---|---|` separator row

            for line in text.splitlines():
                stripped = line.strip()

                # Detect section start
                if re.match(r"##\s+terminology\s+map", stripped, re.I):
                    in_section = True
                    header_skipped = False
                    separator_skipped = False
                    continue

                # Detect section end (next ## heading)
                if in_section and stripped.startswith("##"):
                    in_section = False
                    continue

                if not in_section:
                    continue

                # Skip blank lines and non-table lines
                if not stripped.startswith("|"):
                    continue

                # Skip the header row (first `|` row in section)
                if not header_skipped:
                    header_skipped = True
                    continue

                # Skip the separator row (`|---|---|---|`)
                if not separator_skipped:
                    separator_skipped = True
                    continue

                # Parse data row: | consumer term | medical term | notes |
                parts = [p.strip() for p in stripped.split("|")]
                # parts[0] is empty (before first |), parts[1] is consumer term,
                # parts[2] is medical term
                if len(parts) >= 3 and parts[1]:
                    consumer_term = parts[1]
                    self._register_term(consumer_term, slug)
                    # Also store medical term for query expansion seeding
                    medical_term = parts[2] if len(parts) > 2 else ""
                    if medical_term:
                        self._medical_terms.setdefault(slug, []).append(medical_term)

    def build_centroids(self) -> None:
        """Precompute category centroids from DB embeddings.

        Computes AVG(embedding) per category on the DB side — returns one vector
        per category instead of all 10k rows. Safe to call with None connections
        (becomes a no-op).
        """
        if self._db is None or self._openai is None:
            return
        cur = self._db.cursor()
        cur.execute("""
            SELECT t.primary_category,
                   AVG(e.embedding) AS centroid,
                   COUNT(*) AS record_count
            FROM embeddings e
            JOIN medmcqa_records t ON t.id::text = e.source_id
            WHERE e.source_table = 'medmcqa_records'
              AND t.primary_category IS NOT NULL
            GROUP BY t.primary_category
            HAVING COUNT(*) >= %s
        """, (_MIN_CENTROID_RECORDS,))
        for row in cur.fetchall():
            cat, centroid, _ = row
            if cat and centroid is not None:
                self._centroids[cat] = np.array(centroid)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(self, ctx: QueryContext) -> QueryContext:
        """Classify ``ctx.query`` and populate ``ctx.category`` + ``ctx.classification_method``.

        Classification cascade:
          1. Keyword match (full phrase then token-presence) — deterministic, free.
          2. Embedding cosine similarity against pre-built centroids — requires DB +
             OpenAI client; skipped gracefully when unavailable.
          3. LLM classification via GPT-4o — requires OpenAI client; skipped on error.
          4. Fallback to ``public_health_prevention``.

        Args:
            ctx: Mutable pipeline context carrying the raw query and user profile.

        Returns:
            The same ``ctx`` object with ``category``, ``classification_method``,
            and ``normalized_terms`` populated.
        """
        # Normalise query text
        normalized = ctx.query.lower()
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        words = [w for w in normalized.split() if w]

        # ----------------------------------------------------------------
        # Step 0: Collect keyword/token match scores
        # ----------------------------------------------------------------
        phrase_hits: dict[str, int] = {}   # category → full-phrase hit count
        token_hits: dict[str, int] = {}    # category → token hit count
        matched_terms: list[str] = []

        # Full-phrase substring matches (highest confidence)
        for phrase, cat in self._phrase_map.items():
            if phrase in normalized:
                phrase_hits[cat] = phrase_hits.get(cat, 0) + 1
                matched_terms.append(phrase)

        # Token-presence matches (fallback within keyword step)
        for token, cat_counts in self._token_map.items():
            if token in words:
                for cat, weight in cat_counts.items():
                    token_hits[cat] = token_hits.get(cat, 0) + weight

        ctx.normalized_terms = matched_terms if matched_terms else words[:5]

        # ----------------------------------------------------------------
        # Steps 1–3: Classification cascade (resolve category + method)
        # ----------------------------------------------------------------
        category: str | None = None
        method: str | None = None

        # Step 1: Keyword match — require a single clear winner
        # Prefer phrase hits; use token hits only when there are no phrase hits.
        if phrase_hits:
            winner = self._single_winner(phrase_hits)
            if winner:
                category, method = winner, "keyword"
        if category is None and token_hits:
            winner = self._single_winner(token_hits)
            if winner:
                category, method = winner, "keyword"

        # Step 2: Embedding similarity
        if category is None:
            try:
                cat, score = await self._embedding_classify(ctx.query)
                if cat and score >= _EMBED_THRESHOLD:
                    category, method = cat, "embedding"
            except Exception:
                pass

        # Resolve model for this query (set by caller via ctx.model)
        model = getattr(ctx, "model", None) or "gpt-5.4"

        # Step 3: LLM fallback
        if category is None:
            try:
                cat = await self._llm_classify(ctx.query, model)
                category, method = cat or _DEFAULT_CATEGORY, "llm"
            except Exception:
                category, method = _DEFAULT_CATEGORY, "fallback"

        ctx.category = category or _DEFAULT_CATEGORY
        ctx.classification_method = method or "fallback"

        # ----------------------------------------------------------------
        # Step 4: Query expansion — always runs regardless of classification path
        #   Expands to a HyDE clinical sentence seeded with brain medical terms,
        #   appended to normalized_terms so Agent C searches with richer vocabulary.
        # ----------------------------------------------------------------
        expanded = await self._expand_query(ctx.query, ctx.category, model)
        if expanded:
            existing = set(ctx.normalized_terms)
            ctx.normalized_terms = ctx.normalized_terms + [t for t in expanded if t not in existing]

        # ----------------------------------------------------------------
        # Step 5: Extract user memory — novel health facts not in profile
        # ----------------------------------------------------------------
        if self._memory_store is not None and ctx.user_profile:
            user_id = getattr(ctx.user_profile, "user_id", None)
            if user_id:
                new_facts = await self._extract_user_facts(ctx.query, ctx.user_profile, model)
                for fact in new_facts:
                    self._memory_store.add_fact(
                        user_id, fact["fact"], fact.get("category", "general")
                    )

        return ctx

    # ------------------------------------------------------------------
    # Private classification helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _single_winner(scores: dict[str, int]) -> str | None:
        """Return the unique top-scoring category, or ``None`` on a tie."""
        if not scores:
            return None
        max_score = max(scores.values())
        winners = [c for c, s in scores.items() if s == max_score]
        return winners[0] if len(winners) == 1 else None

    async def _embedding_classify(self, query: str) -> tuple[str | None, float]:
        """Classify ``query`` by cosine similarity to category centroids.

        Args:
            query: Raw query string.

        Returns:
            ``(category_slug, cosine_score)`` for the best-matching centroid, or
            ``(None, 0.0)`` when centroids are unavailable.
        """
        if not self._centroids or self._openai is None:
            return None, 0.0
        resp = await asyncio.to_thread(
            self._openai.embeddings.create, model=_EMBED_MODEL, input=query
        )
        q_vec = np.array(resp.data[0].embedding)
        best_cat, best_score = None, -1.0
        for cat, centroid in self._centroids.items():
            score = float(
                np.dot(q_vec, centroid)
                / (np.linalg.norm(q_vec) * np.linalg.norm(centroid) + 1e-9)
            )
            if score > best_score:
                best_score = score
                best_cat = cat
        return best_cat, best_score

    async def _expand_query(self, query: str, category: str, model: str = "gpt-5.4") -> list[str]:
        """Expand a consumer query into a clinical HyDE sentence using the selected model.

        Bridges the vocabulary gap between consumer language ("chest pain") and
        the clinical MCQ/QA language in the embedding corpus. Seeds the prompt with
        medical terms from the brain terminology map so the expansion stays grounded
        in the domain vocabulary we know is in the corpus.

        Args:
            query: Raw consumer query.
            category: Classified brain category slug.

        Returns:
            List containing one HyDE clinical sentence, or empty list on any error.
            Returned as a list so it integrates cleanly with normalized_terms.
        """
        if self._openai is None:
            return []
        try:
            seed_terms = self._medical_terms.get(category, [])[:10]
            seed_line = (
                f"\nUse these medical terms where relevant: {', '.join(seed_terms)}."
                if seed_terms else ""
            )
            prompt = (
                f"Rewrite this consumer health query as 1-2 sentences in the style "
                f"of a clinical case presentation. Use medical terminology.{seed_line} "
                f"Category: {category}. Query: {query}\n"
                "Respond with the clinical sentences only, nothing else."
            )
            resp = await asyncio.to_thread(
                self._openai.chat.completions.create,
                model=model,
                max_completion_tokens=120,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.choices[0].message.content.strip()
            return [text] if text else []
        except Exception:
            return []

    async def _extract_user_facts(self, query: str, profile, model: str = "gpt-5.4") -> list[dict[str, str]]:
        """Extract novel health-relevant personal context from query.

        Compares against the user's profile and only returns facts that
        are genuinely new (not already in conditions/medications).

        Args:
            query: Raw consumer query.
            profile: ``UserProfile`` instance with conditions and medications.

        Returns:
            List of ``{"fact": "...", "category": "..."}`` dicts, or empty
            list on any failure (silent fallback).
        """
        try:
            conditions = ", ".join(c.name for c in (profile.conditions or []))
            medications = ", ".join(m.name for m in (profile.medications or []))
            profile_summary = (
                f"Age: {profile.age}, Sex: {profile.sex.value if profile.sex else 'unknown'}, "
                f"Conditions: {conditions or 'none'}, "
                f"Medications: {medications or 'none'}"
            )
            prompt = (
                "Compare this health query against the user's profile. Extract any "
                "health-relevant personal context NOT already in the profile.\n\n"
                "Examples of what to extract: caregiver roles, family history, "
                "lifestyle factors (diet, exercise, smoking), new symptoms, "
                "treatment experiences, allergies not listed.\n\n"
                f"User profile: {profile_summary}\n"
                f"Query: {query}\n\n"
                'Return JSON: {"new_facts": [{"fact": "...", "category": "..."}]} '
                'or {"new_facts": []} if nothing new.\n'
                "Category should be a brain category slug. Respond with only the JSON."
            )
            if self._openai is None:
                return []
            resp = await asyncio.to_thread(
                self._openai.chat.completions.create,
                model=model,
                max_completion_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.choices[0].message.content.strip()

            import json as _json
            data = _json.loads(text.strip().removeprefix("```json").removesuffix("```"))
            return data.get("new_facts", [])
        except Exception:
            return []

    async def _llm_classify(self, query: str, model: str = "gpt-5.4") -> str:
        """Ask the selected OpenAI model to classify ``query`` into one of the known category slugs.

        Args:
            query: Raw query string.

        Returns:
            A category slug (guaranteed to be in ``self._categories``), or
            ``_DEFAULT_CATEGORY`` if GPT-4o returns an unrecognised slug.

        Raises:
            Exception: Propagates any API or network error so the caller can fall
                back gracefully.
        """
        cats = ", ".join(self._categories)
        prompt_content = (
            "Classify this health query into exactly one category slug.\n"
            f"Categories: {cats}\n"
            f"Query: {query}\n"
            "Respond with only the category slug, nothing else."
        )
        resp = await asyncio.to_thread(
            self._openai.chat.completions.create,
            model=model,
            max_completion_tokens=50,
            messages=[{"role": "user", "content": prompt_content}],
        )
        slug = resp.choices[0].message.content.strip().lower().replace(" ", "_").replace("-", "_")
        return slug if slug in self._categories else _DEFAULT_CATEGORY
