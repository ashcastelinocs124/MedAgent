"""
Database Schema Setup

Creates the Postgres schema for the healthcare search system.
Run once after creating your RDS instance.

Usage:
    DATABASE_URL="postgresql://user:pass@host:5432/healthsearch" python setup_db.py

Requires:
    pip install psycopg2-binary
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL environment variable not set.")
        print("Example: export DATABASE_URL='postgresql://postgres:yourpass@your-host.region.rds.amazonaws.com:5432/healthsearch'")
        sys.exit(1)
    return psycopg2.connect(url)


def create_schema(conn) -> None:
    with conn.cursor() as cur:

        # pgvector extension — available on AWS RDS Postgres 15+
        # This enables the vector column type used later for embeddings
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # ── MedMCQA full records ──────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS medmcqa_records (
                id               TEXT PRIMARY KEY,
                question         TEXT NOT NULL,
                option_a         TEXT,
                option_b         TEXT,
                option_c         TEXT,
                option_d         TEXT,
                correct_option   TEXT,
                explanation      TEXT,
                subject_name     TEXT,
                topic_name       TEXT,
                primary_category TEXT NOT NULL,
                secondary_category TEXT,
                quality_tier     TEXT NOT NULL,
                has_explanation  BOOLEAN NOT NULL DEFAULT FALSE,
                ingested_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_medmcqa_category
            ON medmcqa_records(primary_category);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_medmcqa_tier
            ON medmcqa_records(quality_tier);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_medmcqa_category_tier
            ON medmcqa_records(primary_category, quality_tier);
        """)

        # ── PubMedQA full records ─────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pubmedqa_records (
                pubid              BIGINT PRIMARY KEY,
                question           TEXT NOT NULL,
                long_answer        TEXT,
                context_passages   JSONB,
                context_labels     JSONB,
                mesh_terms         TEXT[],
                final_decision     TEXT,
                primary_category   TEXT NOT NULL,
                secondary_category TEXT,
                quality_tier       TEXT NOT NULL DEFAULT 'TIER_A',
                ingested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_pubmedqa_category
            ON pubmedqa_records(primary_category);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_pubmedqa_mesh
            ON pubmedqa_records USING GIN(mesh_terms);
        """)

        # ── MedQuAD full records ──────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS medquad_records (
                id                  SERIAL PRIMARY KEY,
                question_id         TEXT UNIQUE NOT NULL,
                question_type       TEXT,
                question            TEXT NOT NULL,
                answer              TEXT NOT NULL,
                source              TEXT,
                primary_category    TEXT,
                secondary_category  TEXT,
                quality_tier        TEXT DEFAULT 'TIER_A',
                created_at          TIMESTAMP DEFAULT NOW()
            );
        """)

        # ── Embeddings (populated later via embed.py) ─────────────────────────
        # source_table: 'medmcqa_records' or 'pubmedqa_records'
        # source_id: the id/pubid of the source record
        # chunk_text: the actual text that was embedded (for debugging)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id           BIGSERIAL PRIMARY KEY,
                source_table TEXT NOT NULL,
                source_id    TEXT NOT NULL,
                chunk_text   TEXT NOT NULL,
                embedding    vector(1536),
                model        TEXT NOT NULL DEFAULT 'text-embedding-3-small',
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(source_table, source_id)
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_source
            ON embeddings(source_table, source_id);
        """)

    conn.commit()
    print("Schema created successfully.")
    print("Tables: medmcqa_records, pubmedqa_records, medquad_records, embeddings")
        # ── Embeddings v2 (improved chunk format — no MCQ noise, includes MedQuAD) ──
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings_v2 (
                id           BIGSERIAL PRIMARY KEY,
                source_table TEXT NOT NULL,
                source_id    TEXT NOT NULL,
                chunk_text   TEXT NOT NULL,
                embedding    vector(1536),
                model        TEXT NOT NULL DEFAULT 'text-embedding-3-small',
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(source_table, source_id)
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_v2_source
            ON embeddings_v2(source_table, source_id);
        """)

        # ── HealthCareMagic records ───────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS healthcaremagic_records (
                id                  BIGINT PRIMARY KEY,
                input               TEXT NOT NULL,
                output              TEXT NOT NULL,
                primary_category    TEXT NOT NULL,
                secondary_category  TEXT,
                quality_tier        TEXT NOT NULL,
                has_response        BOOLEAN NOT NULL DEFAULT TRUE,
                ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_healthcaremagic_category
            ON healthcaremagic_records(primary_category);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_healthcaremagic_tier
            ON healthcaremagic_records(quality_tier);
        """)

    conn.commit()
    print("Schema created successfully.")
    print("Tables: medmcqa_records, pubmedqa_records, medquad_records, embeddings, embeddings_v2, healthcaremagic_records")

        # ── Embeddings v2 (improved chunk format — no MCQ noise, includes MedQuAD) ──
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings_v2 (
                id           BIGSERIAL PRIMARY KEY,
                source_table TEXT NOT NULL,
                source_id    TEXT NOT NULL,
                chunk_text   TEXT NOT NULL,
                embedding    vector(1536),
                model        TEXT NOT NULL DEFAULT 'text-embedding-3-small',
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(source_table, source_id)
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_v2_source
            ON embeddings_v2(source_table, source_id);
        """)

    conn.commit()
    print("Schema created successfully.")
    print("Tables: medmcqa_records, pubmedqa_records, medquad_records, embeddings, embeddings_v2")
    print("Extensions: vector (pgvector)")


def print_counts(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM medmcqa_records;")
        med_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pubmedqa_records;")
        pub_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM medquad_records;")
        mq_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM embeddings;")
        emb_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM embeddings_v2;")
        emb_v2_count = cur.fetchone()[0]

    print(f"\nCurrent row counts:")
    print(f"  medmcqa_records:  {med_count:,}")
    print(f"  pubmedqa_records: {pub_count:,}")
    print(f"  medquad_records:  {mq_count:,}")
    print(f"  embeddings:       {emb_count:,}")
        cur.execute("SELECT COUNT(*) FROM embeddings_v2;")
        emb_v2_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM healthcaremagic_records;")
        hcm_count = cur.fetchone()[0]

    print(f"\nCurrent row counts:")
    print(f"  medmcqa_records:          {med_count:,}")
    print(f"  pubmedqa_records:         {pub_count:,}")
    print(f"  medquad_records:          {mq_count:,}")
    print(f"  healthcaremagic_records:  {hcm_count:,}")
    print(f"  embeddings:               {emb_count:,}")
    print(f"  embeddings_v2:            {emb_v2_count:,}")

    print(f"  embeddings_v2:    {emb_v2_count:,}")


if __name__ == "__main__":
    conn = get_connection()
    try:
        create_schema(conn)
        print_counts(conn)
    finally:
        conn.close()
