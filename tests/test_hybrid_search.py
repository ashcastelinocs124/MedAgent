# tests/test_hybrid_search.py
import os
import psycopg2
import pytest
from openai import OpenAI
from src.search.hybrid import HybridSearcher
from src.agents.context import SearchResult

DATABASE_URL = os.environ["DATABASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


@pytest.fixture(scope="module")
def searcher():
    conn = psycopg2.connect(DATABASE_URL)
    client = OpenAI(api_key=OPENAI_API_KEY)
    s = HybridSearcher(conn, client)
    yield s
    conn.close()


def test_lexical_search_returns_results(searcher):
    results = searcher._lexical_search(
        terms=["diabetes", "metformin"],
        source_tables=["medmcqa_records"],
        top_n=5,
    )
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(r.source_table == "medmcqa_records" for r in results)


def test_lexical_search_populates_required_fields(searcher):
    results = searcher._lexical_search(
        terms=["heart", "blood pressure"],
        source_tables=["medmcqa_records"],
        top_n=3,
    )
    for r in results:
        assert r.record_id
        assert r.primary_category
        assert r.quality_tier in ("TIER_A", "TIER_B", "TIER_C", "TIER_D")
        assert r.chunk_text
        assert 0.0 <= r.relevance_score <= 1.0


def test_rrf_fusion_deduplicates_by_composite_key(searcher):
    # Build two overlapping ranked lists with same (source_table, record_id)
    r1 = SearchResult("42", "medmcqa_records", "heart_blood_vessels", "TIER_A", "text", 0.9, 0.0)
    r2 = SearchResult("42", "medmcqa_records", "heart_blood_vessels", "TIER_A", "text", 0.7, 0.0)
    fused = searcher._rrf_fusion(semantic=[r1], lexical=[r2], top_k=5)
    assert len(fused) == 1  # deduped
    assert fused[0].rrf_score > 0


def test_rrf_uses_integer_ranks_not_raw_scores(searcher):
    # Two results with very different raw scores should be ranked by position, not score
    high_score = SearchResult("1", "medmcqa_records", "cat", "TIER_A", "t", 0.99, 0.0)
    low_score = SearchResult("2", "medmcqa_records", "cat", "TIER_A", "t", 0.01, 0.0)
    # In semantic list: high_score rank=1, low_score rank=2 → in lexical they're reversed
    fused = searcher._rrf_fusion(semantic=[high_score, low_score], lexical=[low_score, high_score], top_k=2)
    # Both should get comparable RRF scores since rank positions are symmetric
    assert abs(fused[0].rrf_score - fused[1].rrf_score) < 0.01


def test_search_degrades_gracefully_with_no_embeddings(searcher):
    # Category with no embeddings should still return lexical results
    # Pass retrieval_plan=None to search all tables (default behavior)
    results = searcher.search(
        terms=["skin", "rash", "dermatology"],
        category="skin_dermatology",
        retrieval_plan=None,
        top_k=3,
    )
    # May return lexical-only results or empty — should not raise
    assert isinstance(results, list)
