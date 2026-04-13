"""
Embedding Pipeline

Generates OpenAI embeddings for MedMCQA and PubMedQA records already in
Postgres and inserts them into the embeddings table. Uses LEFT JOIN to find
un-embedded records — safe to run concurrently and to resume after interruption.

Usage:
    # Small test run
    DATABASE_URL="..." OPENAI_API_KEY="sk-..." python embed.py --source medmcqa --limit 100

    # Full run (both sources)
    DATABASE_URL="..." OPENAI_API_KEY="sk-..." python embed.py --source both --limit 10000

    # Custom batch size / model
    DATABASE_URL="..." OPENAI_API_KEY="sk-..." python embed.py --source pubmedqa --batch-size 50

Requires:
    pip install psycopg2-binary openai pgvector python-dotenv
"""

import os
import sys
import time
import argparse
import psycopg2
import psycopg2.extras
import openai
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()


# ── DB Connection ──────────────────────────────────────────────────────────────

def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL environment variable not set.")
        print("Example: export DATABASE_URL='postgresql://postgres:yourpass@your-host.region.rds.amazonaws.com:5432/postgres'")
        sys.exit(1)
    return psycopg2.connect(url)


# ── OpenAI Client ──────────────────────────────────────────────────────────────

def get_openai_client() -> openai.OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)
    return openai.OpenAI(api_key=key)


# ── Chunk Text Builders ────────────────────────────────────────────────────────

def build_chunk_text_medmcqa(record: dict) -> str:
    """Build the text to embed for a MedMCQA record.

    MCQ options (A/B/C/D) are intentionally excluded — they add format noise
    that shifts embeddings away from the clinical meaning of the question.
    """
    parts = [f"Question: {record.get('question') or ''}"]

    if record.get("has_explanation") and record.get("explanation"):
        parts.append(f"Answer: {record.get('explanation') or ''}")

    parts.append(f"Category: {record.get('primary_category') or ''}")

    return "\n".join(parts)[:8000]


def build_chunk_text_pubmedqa(record: dict) -> str:
    """Build the text to embed for a PubMedQA record."""
    parts = [
        f"Question: {record.get('question') or ''}",
        f"Answer: {record.get('long_answer') or ''}",
        f"Category: {record.get('primary_category') or ''}",
    ]
    return "\n".join(parts)[:8000]


def build_chunk_text_medquad(record: dict) -> str:
    """Build the text to embed for a MedQuAD record.

    MedQuAD uses consumer-style questions and NIH-authored answers, making it
    the closest match to real user queries. Embed as clean Q&A.
    """
    parts = [
        f"Question: {record.get('question') or ''}",
        f"Answer: {record.get('answer') or ''}",
        f"Category: {record.get('primary_category') or ''}",
    ]
    return "\n".join(parts)[:8000]


def build_chunk_text_healthcaremagic(record: dict) -> str:
    """Build the text to embed for a HealthCareMagic record.

    Uses patient input as the question and doctor output as the answer.
    Consumer-language questions make this dataset especially valuable for
    matching real user queries at retrieval time.
    """
    parts = [
        f"Question: {record.get('input') or ''}",
        f"Answer: {record.get('output') or ''}",
        f"Category: {record.get('primary_category') or ''}",
    ]
    return "\n".join(parts)[:8000]


# ── DB Fetch Helpers ───────────────────────────────────────────────────────────

def fetch_unembedded_medmcqa(conn, limit: int, embeddings_table: str) -> list[dict]:
    """Fetch MedMCQA records that don't yet have a row in embeddings_table."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            f"""
            SELECT m.id, m.question, m.explanation, m.has_explanation,
                   m.subject_name, m.topic_name, m.primary_category
            FROM medmcqa_records m
            LEFT JOIN {embeddings_table} e
                ON e.source_table = 'medmcqa_records' AND e.source_id = m.id::TEXT
            WHERE e.id IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def fetch_unembedded_pubmedqa(conn, limit: int, embeddings_table: str) -> list[dict]:
    """Fetch PubMedQA records that don't yet have a row in embeddings_table."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            f"""
            SELECT p.pubid, p.question, p.long_answer,
                   p.primary_category, p.final_decision
            FROM pubmedqa_records p
            LEFT JOIN {embeddings_table} e
                ON e.source_table = 'pubmedqa_records' AND e.source_id = p.pubid::TEXT
            WHERE e.id IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_already_embedded_count(conn, source_table: str) -> int:
def fetch_unembedded_medquad(conn, limit: int, embeddings_table: str) -> list[dict]:
    """Fetch MedQuAD records that don't yet have a row in embeddings_table."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            f"""
            SELECT q.id, q.question, q.answer, q.primary_category
            FROM medquad_records q
            LEFT JOIN {embeddings_table} e
                ON e.source_table = 'medquad_records' AND e.source_id = q.id::TEXT
            WHERE e.id IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def fetch_unembedded_healthcaremagic(conn, limit: int, embeddings_table: str) -> list[dict]:
    """Fetch HealthCareMagic records that don't yet have a row in embeddings_table."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            f"""
            SELECT h.id, h.input, h.output, h.primary_category
            FROM healthcaremagic_records h
            LEFT JOIN {embeddings_table} e
                ON e.source_table = 'healthcaremagic_records' AND e.source_id = h.id::TEXT
            WHERE e.id IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_already_embedded_count(conn, source_table: str, embeddings_table: str) -> int:

    """Return how many embeddings already exist for a given source table."""
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM {embeddings_table} WHERE source_table = %s",
            (source_table,),
        )
        return cur.fetchone()[0]


# ── OpenAI Embedding with Retry ────────────────────────────────────────────────

def _openai_embed_with_retry(
    client: openai.OpenAI,
    texts: list[str],
    model: str,
    max_retries: int = 5,
) -> list[list[float]]:
    """
    Call the OpenAI embeddings API with exponential backoff on rate-limit/server errors.

    Retry schedule (seconds): 10, 20, 40, 80, 160
    Raises immediately on auth/invalid-request errors (no point retrying).
    """
    delay = 10
    for attempt in range(1, max_retries + 1):
        try:
            response = client.embeddings.create(input=texts, model=model)
            return [item.embedding for item in response.data]

        except openai.RateLimitError as e:
            # Honour Retry-After header when present
            retry_after = getattr(getattr(e, "response", None), "headers", {}).get("Retry-After")
            wait = int(retry_after) if retry_after and str(retry_after).isdigit() else delay
            print(f"    429 rate limited (attempt {attempt}/{max_retries}) — waiting {wait}s before retry")
            if attempt == max_retries:
                raise
            time.sleep(wait)
            delay = min(delay * 2, 160)

        except openai.APIStatusError as e:
            if e.status_code < 500:
                # 4xx that isn't 429 — not worth retrying
                raise
            print(f"    OpenAI server error {e.status_code} (attempt {attempt}/{max_retries}) — retrying in {delay}s")
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 160)

        except openai.APIConnectionError as e:
            print(f"    Connection error (attempt {attempt}/{max_retries}): {e} — retrying in {delay}s")
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 160)

        except openai.OpenAIError:
            # Auth errors, invalid requests, etc. — re-raise immediately
            raise

    raise RuntimeError(f"OpenAI embedding request failed after {max_retries} retries")


# ── DB Insert ──────────────────────────────────────────────────────────────────

def insert_embeddings_batch(cur, rows: list[tuple], embeddings_table: str) -> int:
    """
    Insert a batch of embedding rows into embeddings_table. Skips duplicates silently.

    Each tuple: (source_table, source_id, chunk_text, embedding, model)
    """
    psycopg2.extras.execute_values(
        cur,
        f"""
        INSERT INTO {embeddings_table} (source_table, source_id, chunk_text, embedding, model)
        VALUES %s
        ON CONFLICT (source_table, source_id) DO NOTHING
        """,
        rows,
    )
    return cur.rowcount


# ── Core Embedding Loop ────────────────────────────────────────────────────────

def embed_source(
    conn,
    client: openai.OpenAI,
    source_table: str,
    records: list[dict],
    model: str,
    batch_size: int,
    embeddings_table: str,
) -> tuple[int, int, int]:
    """
    Embed all records for one source table in batches.

    Returns (total_embedded, 0, total_failed).
    Failed batches are logged; the run continues so a re-run picks them up.
    """
    if source_table == "medmcqa_records":
        build_chunk = build_chunk_text_medmcqa
        get_source_id = lambda r: str(r["id"])
    elif source_table == "pubmedqa_records":
        build_chunk = build_chunk_text_pubmedqa
        get_source_id = lambda r: str(r["pubid"])

    else:  # medquad_records
        build_chunk = build_chunk_text_medquad
        get_source_id = lambda r: str(r["id"])

    total = len(records)
    total_embedded = 0
    total_failed = 0
    batch_num = 0

    for start in range(0, total, batch_size):
        batch = records[start : start + batch_size]
        batch_num += 1

        chunk_texts = [build_chunk(r) for r in batch]

        try:
            embeddings = _openai_embed_with_retry(client, chunk_texts, model)
        except Exception as e:
            print(f"  batch {batch_num} FAILED (offset {start}): {e}")
            total_failed += len(batch)
            print(
                f"  batch {batch_num} | processed {start + len(batch)}/{total} | "
                f"embedded {total_embedded} | failed {total_failed}"
            )
            time.sleep(0.5)
            continue

        rows = [
            (source_table, get_source_id(r), chunk_texts[i], embeddings[i], model)
            for i, r in enumerate(batch)
        ]

        with conn.cursor() as cur:
            inserted = insert_embeddings_batch(cur, rows, embeddings_table)
        conn.commit()

        total_embedded += inserted

        print(
            f"  batch {batch_num} | processed {start + len(batch):>6,}/{total:,} | "
            f"embedded {total_embedded:,} | failed {total_failed}"
        )

        time.sleep(0.5)

    return total_embedded, 0, total_failed


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate OpenAI embeddings and insert into Postgres")
    parser.add_argument(
        "--source",
        choices=["medmcqa", "pubmedqa", "both"],
        default="both",
        help="Which source to embed (default: both)",
        choices=["medmcqa", "pubmedqa", "medquad", "healthcaremagic", "all"],
        default="all",
        help="Which source to embed (default: all)",

        choices=["medmcqa", "pubmedqa", "medquad", "all"],
        default="all",
        help="Which source to embed (default: all)",

    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200_000,
        help="Max un-embedded records to process per source in this run (default: 200000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Records per OpenAI API call (default: 100)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="text-embedding-3-small",
        help="OpenAI embedding model (default: text-embedding-3-small)",
    )
    parser.add_argument(
        "--table",
        type=str,
        default="embeddings_v2",
        help="Target embeddings table (default: embeddings_v2). Use 'embeddings' for the original table.",
    )
    args = parser.parse_args()

    conn = get_connection()
    register_vector(conn)
    client = get_openai_client()

    sources = []
    if args.source in ("medmcqa", "both"):
        sources.append("medmcqa_records")
    if args.source in ("pubmedqa", "both"):
        sources.append("pubmedqa_records")
    source_map = {
        "medmcqa": ["medmcqa_records"],
        "pubmedqa": ["pubmedqa_records"],
        "medquad": ["medquad_records"],
        "healthcaremagic": ["healthcaremagic_records"],
        "all": ["medmcqa_records", "pubmedqa_records", "medquad_records", "healthcaremagic_records"],
    }
    sources = source_map[args.source]
    embeddings_table = args.table

    print(f"\nTarget embeddings table: {embeddings_table}")



    summary: dict[str, dict] = {}

    try:
        for source_table in sources:
            already_done = get_already_embedded_count(conn, source_table, embeddings_table)
            print(f"\n{source_table}: {already_done:,} already embedded in {embeddings_table}")

            if source_table == "medmcqa_records":
                records = fetch_unembedded_medmcqa(conn, args.limit)

                records = fetch_unembedded_medmcqa(conn, args.limit, embeddings_table)
            elif source_table == "pubmedqa_records":
                records = fetch_unembedded_pubmedqa(conn, args.limit, embeddings_table)
            else:
                records = fetch_unembedded_medquad(conn, args.limit, embeddings_table)

            print(f"{source_table}: {len(records):,} un-embedded records to process (limit={args.limit:,})")

            if not records:
                summary[source_table] = {"embedded": 0, "skipped": already_done, "failed": 0}
                continue

            embedded, _, failed = embed_source(
                conn, client, source_table, records, args.model, args.batch_size, embeddings_table
            )
            summary[source_table] = {
                "embedded": embedded,
                "skipped": already_done,
                "failed": failed,
            }

        # Summary
        print("\n── Run Summary ───────────────────────────────────────────")
        for table, stats in summary.items():
            print(
                f"  {table}: embedded={stats['embedded']:,}  "
                f"already_done={stats['skipped']:,}  failed={stats['failed']:,}"
            )

        # DB totals
        print(f"\n── {embeddings_table} Totals ────────────────────────────")
        for table in sources:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) FROM {embeddings_table} WHERE source_table = %s",
                    (table,),
                )
                total = cur.fetchone()[0]
            print(f"  {table}: {total:,} embeddings in {embeddings_table}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
