# src/search/hybrid.py
from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2
    from openai import OpenAI

from src.agents.context import SearchResult

_TIER_WEIGHTS = {"TIER_A": 1.0, "TIER_B": 0.7, "TIER_C": 0.4, "TIER_D": 0.1}
_RRF_K = 60
_TOP_N = 20          # max results per individual search list
_FALLBACK_RANK = 21  # rank assigned when a document is absent from a list (N+1)
_EMBED_MODEL = "text-embedding-3-small"

# Source tables and their FTS + field config
_TABLE_CONFIG = {
    "medmcqa_records":  {"id_col": "id",    "fts_col": "fts_doc", "category_col": "primary_category"},
    "pubmedqa_records": {"id_col": "pubid", "fts_col": "fts_doc", "category_col": "primary_category"},
    "medquad_records":  {"id_col": "id",    "fts_col": "fts_doc", "category_col": "primary_category"},
}


class HybridSearcher:
    def __init__(
        self,
        conn,
        openai_client: "OpenAI",
        embeddings_table: str = "embeddings",
    ) -> None:
        self._conn = conn
        self._openai = openai_client
        self._embeddings_table = embeddings_table

    def _ensure_conn(self) -> None:
        """Reconnect if the DB connection has been lost, with retries."""
        import os, time
        try:
            if self._conn.closed:
                raise Exception("closed")
            cur = self._conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
        except Exception:
            import psycopg2
            db_url = os.environ.get("DATABASE_URL")
            for attempt in range(5):
                try:
                    self._conn = psycopg2.connect(
                        db_url,
                        keepalives=1,
                        keepalives_idle=10,
                        keepalives_interval=5,
                        keepalives_count=10,
                    )
                    return
                except Exception:
                    if attempt < 4:
                        time.sleep(3 * (attempt + 1))
            raise psycopg2.OperationalError("Failed to reconnect after 5 attempts")

    def _safe_rollback(self) -> None:
        """Rollback, reconnecting if the connection is dead."""
        try:
            self._conn.rollback()
        except Exception:
            self._ensure_conn()

    def search(
        self,
        terms: list[str],
        category: str,
        retrieval_plan=None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Run hybrid search and return top_k fused results.

        retrieval_plan: RetrievalPlan from Agent B. If None, all tables are searched.
        Graph weights from the retrieval plan are applied after RRF fusion:
          - effective_weights (float per category) → multiplicative boost (Fix 1)
          - must_load categories → additive flat boost (Fix 3)
        Overfetch by 3× before graph reranking so boosted results can bubble up.
        """
        self._ensure_conn()
        source_tables = self._resolve_source_tables(retrieval_plan)
        semantic = self._semantic_search(terms, source_tables, top_n=_TOP_N)
        lexical = self._lexical_search(terms, source_tables, top_n=_TOP_N)

        # Overfetch before graph reranking so lower-ranked but graph-relevant
        # results have a chance to surface into the final top_k.
        prefetch_k = min(top_k * 3, _TOP_N)
        fused = self._rrf_fusion(semantic, lexical, top_k=prefetch_k)

        # Fix 1: multiplicative boost from RetrievalPlan.effective_weights
        # Fix 3: additive flat boost for must_load categories
        effective_weights: dict[str, float] = (
            getattr(retrieval_plan, "effective_weights", {}) if retrieval_plan else {}
        )
        must_load: set[str] = set(
            getattr(retrieval_plan, "must_load", []) if retrieval_plan else []
        )

        if effective_weights or must_load:
            for result in fused:
                cat = result.primary_category
                graph_weight = effective_weights.get(cat, 0.0)
                must_boost = 0.10 if cat in must_load else 0.0
                result.rrf_score = result.rrf_score * (1.0 + graph_weight * 0.3) + must_boost
            fused.sort(key=lambda r: r.rrf_score, reverse=True)

        return fused[:top_k]

    def _resolve_source_tables(self, retrieval_plan) -> list[str]:
        """Determine which DB tables to search from the retrieval plan."""
        all_tables = list(_TABLE_CONFIG.keys())
        if retrieval_plan is None:
            return all_tables
        priority = getattr(retrieval_plan, "source_priority_tables", None)
        if priority:
            return [t for t in priority if t in _TABLE_CONFIG] or all_tables
        return all_tables

    def _embed_query(self, terms: list[str]) -> list[float]:
        text = " ".join(terms)
        resp = self._openai.embeddings.create(model=_EMBED_MODEL, input=text)
        return resp.data[0].embedding

    def _semantic_search(
        self, terms: list[str], source_tables: list[str], top_n: int
    ) -> list[SearchResult]:
        try:
            vec = self._embed_query(terms)
        except Exception:
            return []

        vec_str = "[" + ",".join(str(v) for v in vec) + "]"
        results: list[SearchResult] = []

        for table in source_tables:
            cfg = _TABLE_CONFIG[table]
            sql = f"""
                SELECT
                    e.source_id::text AS record_id,
                    e.source_table,
                    t.{cfg['category_col']} AS primary_category,
                    t.quality_tier,
                    e.chunk_text,
                    1 - (e.embedding <=> %s::vector) AS similarity
                FROM {self._embeddings_table} e
                JOIN {table} t ON t.{cfg['id_col']}::text = e.source_id
                WHERE e.source_table = %s
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
            """
            rows = None
            for _attempt in range(2):
                try:
                    cur = self._conn.cursor()
                    cur.execute(sql, (vec_str, table, vec_str, top_n))
                    rows = cur.fetchall()
                    break
                except Exception:
                    self._safe_rollback()
            if rows is None:
                continue
            for row in rows:
                results.append(SearchResult(
                    record_id=row[0],
                    source_table=row[1],
                    primary_category=row[2] or "public_health_prevention",
                    quality_tier=row[3] or "TIER_D",
                    chunk_text=row[4] or "",
                    relevance_score=float(max(0.0, min(1.0, row[5]))),
                    rrf_score=0.0,
                ))

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_n]

    def _lexical_search(
        self, terms: list[str], source_tables: list[str], top_n: int
    ) -> list[SearchResult]:
        query_str = " ".join(terms)
        if not query_str.strip():
            return []

        results: list[SearchResult] = []
        for table in source_tables:
            cfg = _TABLE_CONFIG[table]
            if table == "medmcqa_records":
                text_expr = "question || ' ' || COALESCE(explanation, '')"
            elif table == "pubmedqa_records":
                text_expr = "question || ' ' || COALESCE(long_answer, '')"
            else:
                text_expr = "question || ' ' || COALESCE(answer, '')"

            sql = f"""
                SELECT
                    {cfg['id_col']}::text AS record_id,
                    '{table}' AS source_table,
                    {cfg['category_col']} AS primary_category,
                    quality_tier,
                    {text_expr} AS chunk_text,
                    ts_rank({cfg['fts_col']}, plainto_tsquery('english', %s)) AS rank_score
                FROM {table}
                WHERE {cfg['fts_col']} @@ plainto_tsquery('english', %s)
                ORDER BY rank_score DESC
                LIMIT %s
            """
            rows = None
            for _attempt in range(2):
                try:
                    cur = self._conn.cursor()
                    cur.execute(sql, (query_str, query_str, top_n))
                    rows = cur.fetchall()
                    break
                except Exception:
                    self._safe_rollback()
            if rows is None:
                continue
            for row in rows:
                results.append(SearchResult(
                    record_id=row[0],
                    source_table=row[1],
                    primary_category=row[2] or "public_health_prevention",
                    quality_tier=row[3] or "TIER_D",
                    chunk_text=row[4] or "",
                    relevance_score=float(row[5]),
                    rrf_score=0.0,
                ))

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_n]

    def _rrf_fusion(
        self, semantic: list[SearchResult], lexical: list[SearchResult], top_k: int
    ) -> list[SearchResult]:
        """Fuse two ranked lists using RRF with 1-based integer ranks."""
        sem_ranks: dict[tuple[str, str], int] = {
            (r.source_table, r.record_id): i + 1 for i, r in enumerate(semantic)
        }
        lex_ranks: dict[tuple[str, str], int] = {
            (r.source_table, r.record_id): i + 1 for i, r in enumerate(lexical)
        }

        all_keys: set[tuple[str, str]] = set(sem_ranks) | set(lex_ranks)

        # Build result map: prefer semantic result if present (has embedding-based relevance_score)
        result_map: dict[tuple[str, str], SearchResult] = {}
        for r in lexical:
            result_map[(r.source_table, r.record_id)] = r
        for r in semantic:
            result_map[(r.source_table, r.record_id)] = r

        fused: list[SearchResult] = []
        for key in all_keys:
            r_sem = sem_ranks.get(key, _FALLBACK_RANK)
            r_lex = lex_ranks.get(key, _FALLBACK_RANK)
            rrf = 1.0 / (_RRF_K + r_sem) + 1.0 / (_RRF_K + r_lex)
            result = result_map[key]
            result.rrf_score = rrf
            fused.append(result)

        fused.sort(key=lambda r: r.rrf_score, reverse=True)
        return fused[:top_k]
