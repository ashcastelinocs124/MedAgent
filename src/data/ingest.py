
"""
Full-Record Ingestion Pipeline

Fetches complete records from MedMCQA, PubMedQA, and MedQuAD, assigns categories,
and writes to Postgres. Optionally rebuilds brain markdown files from
all records currently in the database.

Usage:
    # Test run — 500 MedMCQA + all PubMedQA labeled
    DATABASE_URL="..." python ingest.py --source medmcqa --limit 500

    # Your initial run — 10k MedMCQA
    DATABASE_URL="..." python ingest.py --source medmcqa --limit 10000

    # Groupmate continues from where you left off
    DATABASE_URL="..." python ingest.py --source medmcqa --limit 10000 --offset 10000

    # Ingest all PubMedQA labeled (1,000 records)
    DATABASE_URL="..." python ingest.py --source pubmedqa

    # Ingest MedQuAD from a local CSV file
    DATABASE_URL="..." python ingest.py --source medquad --medquad-path data/medquad.csv

    # Ingest both MedMCQA + rebuild brain markdown files from DB
    DATABASE_URL="..." python ingest.py --source both --limit 10000 --rebuild-brain

    # Rebuild brain (safe, free — only updates stats/links blocks)
    DATABASE_URL="..." python ingest.py --source medmcqa --limit 1 --rebuild-brain

    # Full enrichment with Claude API (slow, requires ANTHROPIC_API_KEY)
    DATABASE_URL="..." python ingest.py --source medmcqa --limit 1 --rebuild-brain --enrich

Requires:
    pip install psycopg2-binary
"""

import os
import sys
import csv
import json
import time
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv()
import psycopg2.extras
import requests
from pathlib import Path

# Import categorization logic and brain writers from categorize.py
sys.path.insert(0, str(Path(__file__).parent))
from categorize import (
    categorize_medmcqa,
    categorize_pubmedqa,
    categorize_medquad,
    categorize_healthcaremagic,
    detect_quality_tier,
    detect_healthcaremagic_tier,
    CATEGORY_LABELS,
    BRAIN_DIR,
    compute_stats,
    write_category_mapping,
    write_mesh_mapping,
    write_stats_md,
    write_directory_md,
    write_general_rules,
    write_category_files,
    write_review_files,
)
from brain_enricher import compute_category_links
from collections import Counter, defaultdict


# ── DB Connection ─────────────────────────────────────────────────────────────

def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL environment variable not set.")
        print("Example: export DATABASE_URL='postgresql://postgres:yourpass@your-host.region.rds.amazonaws.com:5432/postgres'")
        sys.exit(1)
    return psycopg2.connect(url)


# ── HuggingFace Fetching ──────────────────────────────────────────────────────

def _hf_headers() -> dict:
    """Return Authorization header if HF_TOKEN is set in environment."""
    token = os.environ.get("HF_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _hf_get(url: str, params: dict, max_retries: int = 5) -> dict:
    """
    GET from HuggingFace datasets API with exponential backoff on 429/5xx.

    Retry schedule (seconds): 10, 20, 40, 80, 160
    Raises on non-retryable errors or when retries are exhausted.
    """
    delay = 10  # initial wait in seconds
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=_hf_headers(), timeout=30)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                raise
            print(f"    Network error (attempt {attempt}/{max_retries}): {e} — retrying in {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 160)
            continue

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 429:
            # Honour Retry-After header if present, otherwise use backoff
            retry_after = resp.headers.get("Retry-After")
            wait = int(retry_after) if retry_after and retry_after.isdigit() else delay
            print(f"    429 rate limited (attempt {attempt}/{max_retries}) — waiting {wait}s before retry")
            time.sleep(wait)
            delay = min(delay * 2, 160)
            continue

        if resp.status_code >= 500:
            print(f"    HF server error {resp.status_code} (attempt {attempt}/{max_retries}) — retrying in {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 160)
            continue

        # 4xx that isn't 429 — not worth retrying
        resp.raise_for_status()

    raise RuntimeError(f"HuggingFace request failed after {max_retries} retries: {url} params={params}")


def fetch_medmcqa_batch(offset: int, length: int = 100) -> list[dict]:
    """Fetch a batch of MedMCQA rows from HuggingFace."""
    data = _hf_get(
        "https://datasets-server.huggingface.co/rows",
        params={
            "dataset": "openlifescienceai/medmcqa",
            "config": "default",
            "split": "train",
            "offset": offset,
            "length": length,
        },
    )
    return [r["row"] for r in data.get("rows", [])]


def fetch_pubmedqa_batch(offset: int, length: int = 100) -> list[dict]:
    """Fetch a batch of PubMedQA labeled rows from HuggingFace."""
    data = _hf_get(
        "https://datasets-server.huggingface.co/rows",
        params={
            "dataset": "qiaojin/PubMedQA",
            "config": "pqa_labeled",
            "split": "train",
            "offset": offset,
            "length": length,
        },
    )
    return [r["row"] for r in data.get("rows", [])]


# ── DB Inserts ────────────────────────────────────────────────────────────────

def insert_medmcqa_batch(cur, records: list[dict]) -> int:
    """Insert a batch of MedMCQA records. Returns number of new rows inserted."""
    if not records:
        return 0

    rows = []
    for r in records:
        primary, secondary = categorize_medmcqa(r)
        tier = detect_quality_tier(r.get("exp"))
        has_exp = bool(
            r.get("exp") and
            r["exp"].strip() and
            r["exp"].strip().lower() != "null"
        )

        # Map cop (correct option index) to letter
        cop_raw = r.get("cop")
        correct = {1: "a", 2: "b", 3: "c", 4: "d"}.get(cop_raw, str(cop_raw) if cop_raw else None)

        rows.append((
            str(r.get("id", "")),
            r.get("question", ""),
            r.get("opa"),
            r.get("opb"),
            r.get("opc"),
            r.get("opd"),
            correct,
            r.get("exp"),
            r.get("subject_name"),
            r.get("topic_name"),
            primary,
            secondary,
            tier,
            has_exp,
        ))

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO medmcqa_records
            (id, question, option_a, option_b, option_c, option_d,
             correct_option, explanation, subject_name, topic_name,
             primary_category, secondary_category, quality_tier, has_explanation)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    return cur.rowcount


def insert_pubmedqa_batch(cur, records: list[dict]) -> int:
    """Insert a batch of PubMedQA records. Returns number of new rows inserted."""
    if not records:
        return 0

    rows = []
    for r in records:
        primary, secondary = categorize_pubmedqa(r)
        context = r.get("context", {})

        rows.append((
            r.get("pubid"),
            r.get("question", ""),
            r.get("long_answer"),
            json.dumps(context.get("contexts", [])),
            json.dumps(context.get("labels", [])),
            context.get("meshes", []),
            r.get("final_decision"),
            primary,
            secondary,
            "TIER_A",
        ))

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO pubmedqa_records
            (pubid, question, long_answer, context_passages, context_labels,
             mesh_terms, final_decision, primary_category, secondary_category,
             quality_tier)
        VALUES %s
        ON CONFLICT (pubid) DO NOTHING
        """,
        rows,
    )
    return cur.rowcount


# ── Ingestion Runners ─────────────────────────────────────────────────────────

def ingest_medmcqa(conn, limit: int, start_offset: int, batch_size: int = 100) -> int:
    """
    Ingest MedMCQA records sequentially starting from start_offset.
    Returns total new rows inserted.
    """
    total_inserted = 0
    total_fetched = 0
    offset = start_offset

    print(f"\nIngesting MedMCQA: up to {limit:,} records starting at offset {start_offset:,}")

    while total_fetched < limit:
        this_batch = min(batch_size, limit - total_fetched)

        try:
            rows = fetch_medmcqa_batch(offset, this_batch)
        except Exception as e:
            # Retries inside _hf_get already exhausted — log and stop the run
            print(f"  offset={offset} FAILED after all retries: {e}")
            print(f"  Stopping. Resume with --offset {offset} to pick up here.")
            break

        if not rows:
            print(f"  No more rows at offset={offset}, stopping.")
            break

        with conn.cursor() as cur:
            inserted = insert_medmcqa_batch(cur, rows)
        conn.commit()

        total_inserted += inserted
        total_fetched += len(rows)
        offset += len(rows)

        print(f"  offset={offset - len(rows):>7,} | fetched {len(rows):>3} | "
              f"new {inserted:>3} | total ingested {total_inserted:,}")

        time.sleep(2.0)

    print(f"MedMCQA done: {total_inserted:,} new records inserted ({total_fetched:,} fetched)")
    return total_inserted


def ingest_pubmedqa(conn, batch_size: int = 100) -> int:
    """
    Ingest all PubMedQA labeled records (1,000 total).
    Returns total new rows inserted.
    """
    total_inserted = 0
    total_fetched = 0
    offset = 0
    max_records = 1000  # pqa_labeled has exactly 1,000 rows

    print(f"\nIngesting PubMedQA labeled: all {max_records:,} records")

    while total_fetched < max_records:
        try:
            rows = fetch_pubmedqa_batch(offset, batch_size)
        except Exception as e:
            print(f"  offset={offset} FAILED after all retries: {e}")
            print(f"  Stopping. Resume with --offset {offset} to pick up here.")
            break

        if not rows:
            print(f"  No more rows at offset={offset}, stopping.")
            break

        with conn.cursor() as cur:
            inserted = insert_pubmedqa_batch(cur, rows)
        conn.commit()

        total_inserted += inserted
        total_fetched += len(rows)
        offset += len(rows)

        print(f"  offset={offset - len(rows):>5,} | fetched {len(rows):>3} | "
              f"new {inserted:>3} | total ingested {total_inserted:,}")

        time.sleep(2.0)

    print(f"PubMedQA done: {total_inserted:,} new records inserted ({total_fetched:,} fetched)")
    return total_inserted


# ── MedQuAD (CSV) ────────────────────────────────────────────────────────────

def insert_medquad_batch(cur, records: list[dict], source_name: str = "") -> int:
    """Insert a batch of MedQuAD records. Returns number of new rows inserted."""
    if not records:
        return 0

    rows = []
    for r in records:
        # Skip records with no answer (MedlinePlus copyright-stripped rows)
        answer = (r.get("answer") or "").strip()
        if not answer:
            continue
        primary, secondary = categorize_medquad(r, source_name=source_name)
        rows.append((
            f"{source_name}::{r.get('question_id', '')}",
            r.get("question_type") or "",
            r.get("question", ""),
            answer,
            source_name,
            primary,
            secondary,
            "TIER_A",
        ))

    if not rows:
        return 0

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO medquad_records
            (question_id, question_type, question, answer, source,
             primary_category, secondary_category, quality_tier)
        VALUES %s
        ON CONFLICT (question_id) DO NOTHING
        """,
        rows,
    )
    return cur.rowcount


def ingest_medquad(conn, csv_path: str, batch_size: int = 500) -> int:
    """
    Ingest MedQuAD records from a folder of CSV files or a single CSV file.

    Pass the _data_as_csvs folder path:
      python ingest.py --source medquad --medquad-path data/MedQuAD-CSVs-master/_data_as_csvs

    Files 10/11/12 (ADAM, MPlusDrugs, MPlusHerbsSupplements) have answers stripped
    due to MedlinePlus copyright — those rows are skipped automatically.

    Returns total new rows inserted.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"ERROR: MedQuAD path not found at '{csv_path}'")
        print("Expected: data/MedQuAD-CSVs-master/_data_as_csvs")
        return 0

    # Support both a folder of CSVs and a single CSV file
    if path.is_dir():
        csv_files = sorted(path.glob("*.csv"))
        if not csv_files:
            print(f"ERROR: No CSV files found in '{csv_path}'")
            return 0
    else:
        csv_files = [path]

    total_inserted = 0
    total_read = 0
    total_skipped = 0

    print(f"\nIngesting MedQuAD from {len(csv_files)} CSV file(s) in: {csv_path}")

    for csv_file in csv_files:
        file_inserted = 0
        file_read = 0
        batch = []
        # Derive a clean source name from the filename e.g. "CancerGov", "GARD", "NIDDK"
        source_name = csv_file.stem  # e.g. "1_CancerGov_QA"

        try:
            with open(csv_file, newline="", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    batch.append(row)
                    file_read += 1

                    if len(batch) >= batch_size:
                        with conn.cursor() as cur:
                            inserted = insert_medquad_batch(cur, batch, source_name=source_name)
                        conn.commit()
                        file_inserted += inserted
                        batch = []

            # Final partial batch
            if batch:
                with conn.cursor() as cur:
                    inserted = insert_medquad_batch(cur, batch, source_name=source_name)
                conn.commit()
                file_inserted += inserted

        except Exception as e:
            print(f"  WARNING: Failed to read {csv_file.name}: {e}")
            continue

        skipped = file_read - file_inserted
        total_inserted += file_inserted
        total_read += file_read
        total_skipped += skipped
        print(f"  {csv_file.name:<40} read {file_read:>5,} | inserted {file_inserted:>5,} | skipped {skipped:>5,}")

    print(f"MedQuAD done: {total_inserted:,} new records inserted "
          f"({total_read:,} read, {total_skipped:,} skipped — no answer or duplicate)")
    return total_inserted


# ── HealthCareMagic (HuggingFace) ────────────────────────────────────────────

def fetch_healthcaremagic_batch(offset: int, length: int = 100) -> list[dict]:
    """Fetch a batch of HealthCareMagic rows from HuggingFace."""
    data = _hf_get(
        "https://datasets-server.huggingface.co/rows",
        params={
            "dataset": "lavita/ChatDoctor-HealthCareMagic-100k",
            "config": "default",
            "split": "train",
            "offset": offset,
            "length": length,
        },
    )
    return [
        {"row_idx": r["row_idx"], **r["row"]}
        for r in data.get("rows", [])
    ]


def insert_healthcaremagic_batch(cur, records: list[dict]) -> int:
    """Insert a batch of HealthCareMagic records. Returns number of new rows inserted."""
    if not records:
        return 0

    rows = []
    for r in records:
        patient_input = (r.get("input") or "").strip()
        doctor_output = (r.get("output") or "").strip()

        # Skip records with no meaningful content
        if not patient_input or not doctor_output:
            continue

        primary, secondary = categorize_healthcaremagic(r)
        tier = detect_healthcaremagic_tier(doctor_output)

        rows.append((
            r["row_idx"],
            patient_input,
            doctor_output,
            primary,
            secondary,
            tier,
            bool(doctor_output),
        ))

    if not rows:
        return 0

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO healthcaremagic_records
            (id, input, output, primary_category, secondary_category,
             quality_tier, has_response)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    return cur.rowcount


def recategorize_healthcaremagic(conn, batch_size: int = 1000) -> int:
    """
    Re-run categorization on all existing healthcaremagic_records in-place.
    Updates primary_category and secondary_category without re-fetching from HuggingFace.
    Returns number of rows updated.
    """
    print("\nRe-categorizing healthcaremagic_records in-place...")

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM healthcaremagic_records")
        total = cur.fetchone()[0]

    print(f"  Total rows to recategorize: {total:,}")

    updated = 0
    offset = 0

    while offset < total:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT id, input, output FROM healthcaremagic_records ORDER BY id LIMIT %s OFFSET %s",
                (batch_size, offset),
            )
            rows = cur.fetchall()

        if not rows:
            break

        updates = []
        for row in rows:
            primary, secondary = categorize_healthcaremagic({
                "input": row["input"],
                "output": row["output"],
            })
            updates.append((primary, secondary, row["id"]))

        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(
                cur,
                "UPDATE healthcaremagic_records SET primary_category = %s, secondary_category = %s WHERE id = %s",
                updates,
            )
        conn.commit()

        updated += len(rows)
        offset += len(rows)
        print(f"  recategorized {updated:,}/{total:,}")

    print(f"Recategorization done: {updated:,} rows updated.")
    return updated


def ingest_healthcaremagic(conn, limit: int, start_offset: int, batch_size: int = 100) -> int:
    """
    Ingest HealthCareMagic records from HuggingFace sequentially starting from start_offset.
    Total dataset size is 112,165 records.
    Returns total new rows inserted.
    """
    total_inserted = 0
    total_fetched = 0
    offset = start_offset

    print(f"\nIngesting HealthCareMagic: up to {limit:,} records starting at offset {start_offset:,}")

    while total_fetched < limit:
        this_batch = min(batch_size, limit - total_fetched)

        try:
            rows = fetch_healthcaremagic_batch(offset, this_batch)
        except Exception as e:
            print(f"  offset={offset} FAILED after all retries: {e}")
            print(f"  Stopping. Resume with --offset {offset} to pick up here.")
            break

        if not rows:
            print(f"  No more rows at offset={offset}, stopping.")
            break

        with conn.cursor() as cur:
            inserted = insert_healthcaremagic_batch(cur, rows)
        conn.commit()

        total_inserted += inserted
        total_fetched += len(rows)
        offset += len(rows)

        print(f"  offset={offset - len(rows):>7,} | fetched {len(rows):>3} | "
              f"new {inserted:>3} | total ingested {total_inserted:,}")

        time.sleep(2.0)

    print(f"HealthCareMagic done: {total_inserted:,} new records inserted ({total_fetched:,} fetched)")
    return total_inserted


# ── Brain Rebuild from DB ─────────────────────────────────────────────────────

def _discover_medical_tables(conn) -> list[dict]:
    """
    Dynamically discover tables that have both primary_category and question columns.
    Returns a list of dicts with table name and key column metadata.

    This ensures new datasets (e.g., consumer_health_records) are automatically
    included in brain rebuilds without code changes.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.columns
            WHERE column_name = 'primary_category'
              AND table_schema = 'public'
              AND table_name IN (
                  SELECT table_name
                  FROM information_schema.columns
                  WHERE column_name IN ('question', 'input')
                    AND table_schema = 'public'
              )
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]

        result = []
        for table in tables:
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
            """, (table,))
            columns = {row[0] for row in cur.fetchall()}

            # Determine the best id column
            if "id" in columns:
                id_col = "id"
            elif "pubid" in columns:
                id_col = "pubid"
            elif "question_id" in columns:
                id_col = "question_id"
            else:
                id_col = None

            # Determine the question/input column
            if "question" in columns:
                question_col = "question"
            elif "input" in columns:
                question_col = "input"
            else:
                question_col = None

            # Determine the best explanation column
            if "exp" in columns:
                exp_col = "exp"
            elif "long_answer" in columns:
                exp_col = "long_answer"
            elif "answer" in columns:
                exp_col = "answer"
            elif "output" in columns:
                exp_col = "output"
            else:
                exp_col = None

            # Subject/source column
            if "subject_name" in columns:
                subject_col = "subject_name"
            elif "source" in columns:
                subject_col = "source"
            else:
                subject_col = None

            # Topic column
            if "topic_name" in columns:
                topic_col = "topic_name"
            elif "question_type" in columns:
                topic_col = "question_type"
            else:
                topic_col = None

            # Infer dataset label from table name
            if "medmcqa" in table:
                dataset = "medmcqa"
            elif "pubmedqa" in table:
                dataset = "pubmedqa"
            elif "medquad" in table:
                dataset = "medquad"
            else:
                dataset = table

            result.append({
                "table": table,
                "dataset": dataset,
                "id_col": id_col,
                "question_col": question_col,
                "exp_col": exp_col,
                "subject_col": subject_col,
                "topic_col": topic_col,
                "has_has_explanation": "has_explanation" in columns,
                "has_quality_tier": "quality_tier" in columns,
                "has_secondary_category": "secondary_category" in columns,
                "has_mesh_terms": "mesh_terms" in columns,
            })

    return result


def _read_table_records(
    conn,
    table_info: dict,
    fetch_exp: bool = False,
) -> tuple[list[dict], dict]:
    """
    Read all records from a medical table using its discovered schema.
    Returns (results, mesh_category_map).
    mesh_category_map is only populated for tables with mesh_terms column.
    """
    table = table_info["table"]
    dataset = table_info["dataset"]
    id_col = table_info["id_col"]
    exp_col = table_info.get("exp_col")
    subject_col = table_info.get("subject_col")
    topic_col = table_info.get("topic_col")

    # Build SELECT list — alias question_col as "question" so record-building code is unchanged
    question_col = table_info.get("question_col", "question")
    question_select = f"{question_col} AS question" if question_col != "question" else "question"
    select_parts = [question_select, "primary_category"]
    if id_col:
        select_parts.insert(0, id_col)
    if table_info["has_secondary_category"]:
        select_parts.append("secondary_category")
    if table_info["has_quality_tier"]:
        select_parts.append("quality_tier")
    if table_info["has_has_explanation"]:
        select_parts.append("has_explanation")
    if subject_col:
        select_parts.append(subject_col)
    if topic_col:
        select_parts.append(topic_col)
    if table_info["has_mesh_terms"]:
        select_parts.append("mesh_terms")
    if fetch_exp and exp_col and exp_col not in select_parts:
        select_parts.append(exp_col)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(f"SELECT {', '.join(select_parts)} FROM {table}")
        rows = cur.fetchall()

    results = []
    mesh_category_map: dict[str, Counter] = defaultdict(Counter)

    for row in rows:
        row_dict = dict(row)
        primary_cat = row_dict.get("primary_category")

        # Build mesh map if applicable
        if table_info["has_mesh_terms"]:
            for mesh in (row_dict.get("mesh_terms") or []):
                mesh_category_map[mesh][primary_cat] += 1

        record: dict = {
            "id": str(row_dict.get(id_col, "")) if id_col else "",
            "dataset": dataset,
            "subject_name": row_dict.get(subject_col, "") or "" if subject_col else "",
            "topic_name": row_dict.get(topic_col, "") or "" if topic_col else "",
            "question": (row_dict.get("question") or "")[:200],
            "primary_category": primary_cat,
            "secondary_category": row_dict.get("secondary_category") or "",
            "quality_tier": row_dict.get("quality_tier") or "TIER_D",
            "has_explanation": (
                bool(row_dict.get("has_explanation", False))
                if table_info["has_has_explanation"]
                else bool(exp_col)  # tables without has_explanation col but with an answer col always have content
            ),
        }
        if fetch_exp and exp_col:
            record["exp"] = row_dict.get(exp_col, "") or ""

        results.append(record)

    return results, mesh_category_map


def rebuild_brain_from_db(conn, enrich: bool = False) -> None:
    """
    Read all records from the DB and rebuild brain markdown files.

    Mode 1 (default, --rebuild-brain):
      Replaces only the AUTO-GENERATED block in each category file.
      Stats, quality tiers, contributing subjects, sample questions, and
      co-occurrence links are updated. Human/AI knowledge sections untouched.

    Mode 2 (--rebuild-brain --enrich):
      Everything in Mode 1, PLUS calls Claude API to regenerate all knowledge
      sections (Source Priority, Terminology Map, Query Patterns, Rules,
      Pitfalls, Dominant Style) and also regenerates general_rules.md.
    """
    print("\nRebuilding brain from database...")

    # Discover all eligible tables dynamically
    table_infos = _discover_medical_tables(conn)
    if not table_infos:
        print("  ERROR: No tables with primary_category + question columns found.")
        return

    print(f"  Discovered {len(table_infos)} medical table(s): {[t['table'] for t in table_infos]}")

    results: list[dict] = []
    combined_mesh_map: dict[str, Counter] = defaultdict(Counter)

    for tinfo in table_infos:
        table_results, mesh_map = _read_table_records(conn, tinfo, fetch_exp=enrich)
        results.extend(table_results)
        for term, cat_counts in mesh_map.items():
            combined_mesh_map[term].update(cat_counts)
        print(f"  Loaded {len(table_results):,} records from {tinfo['table']}")

    print(f"  Total for brain rebuild: {len(results):,} records")

    # Resolve MeSH → category
    resolved_mesh_map = {
        term: counts.most_common(1)[0][0]
        for term, counts in combined_mesh_map.items()
    }

    # Compute stats (includes secondary_by_primary for link derivation)
    stats = compute_stats(results)

    # Derive data-driven category links (free, no API)
    links = compute_category_links(stats)

    # Optional: Claude API enrichment
    enrichment: dict | None = None
    if enrich:
        print("\nEnriching brain with Claude API...")
        from brain_enricher import (
            enrich_category_with_claude,
            enrich_general_rules_with_claude,
            CATEGORY_LABELS as _BE_LABELS,
        )
        from categorize import CATEGORIES

        enrichment = {}
        by_category: dict[str, list[dict]] = defaultdict(list)
        for r in results:
            by_category[r["primary_category"]].append(r)

        for cat in CATEGORIES:
            label = CATEGORY_LABELS.get(cat, cat)
            print(f"  Enriching {label}...", end="", flush=True)
            try:
                enrichment[cat] = enrich_category_with_claude(
                    cat=cat,
                    label=label,
                    stats=stats,
                    cat_results=by_category.get(cat, []),
                    links=links,
                )
                print(" done")
            except Exception as e:
                print(f" FAILED: {e}")

        # Regenerate general_rules.md
        print("  Regenerating general_rules.md...", end="", flush=True)
        try:
            rules_content = enrich_general_rules_with_claude(stats, results)
            rules_path = BRAIN_DIR / "general_rules.md"
            rules_path.write_text(rules_content, encoding="utf-8")
            print(" done")
        except Exception as e:
            print(f" FAILED: {e}")
            write_general_rules(BRAIN_DIR / "general_rules.md")
    else:
        # Only write general_rules.md if it doesn't already exist
        rules_path = BRAIN_DIR / "general_rules.md"
        if not rules_path.exists():
            write_general_rules(rules_path)

    # Strip exp field used only for enrichment — not part of the standard record schema
    for r in results:
        r.pop("exp", None)

    # Write all brain files
    import os
    os.makedirs(BRAIN_DIR / "categories", exist_ok=True)
    os.makedirs(BRAIN_DIR / "review", exist_ok=True)

    write_category_mapping(results, BRAIN_DIR / "category_mapping.csv")
    if resolved_mesh_map:
        write_mesh_mapping(resolved_mesh_map, BRAIN_DIR / "mesh_to_category.csv")

    write_stats_md(stats, BRAIN_DIR / "stats.md")
    write_directory_md(stats, BRAIN_DIR / "directory.md")
    write_category_files(stats, results, BRAIN_DIR / "categories", links=links, enrichment=enrichment)
    write_review_files(results, BRAIN_DIR / "review")

    mode_label = "with Claude enrichment" if enrich else "stats/links only (knowledge sections preserved)"
    print(f"Brain markdown files rebuilt from database ({mode_label}).")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest medical QA data into Postgres")
    parser.add_argument(
        "--source",
        choices=["medmcqa", "pubmedqa", "medquad", "healthcaremagic", "both"],
        default="medmcqa",
        help="Which dataset to ingest (default: medmcqa). 'both' covers medmcqa + pubmedqa.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10_000,
        help="Max MedMCQA records to ingest in this run (default: 10000)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="MedMCQA start offset — use this so groupmates don't duplicate work (default: 0)",
    )
    parser.add_argument(
        "--medquad-path",
        type=str,
        default="data/MedQuAD-CSVs-master/_data_as_csvs",
        help="Path to MedQuAD CSV folder or single CSV file (default: data/MedQuAD-CSVs-master/_data_as_csvs)",
    )
    parser.add_argument(
        "--rebuild-brain",
        action="store_true",
        help="After ingestion, rebuild brain markdown files from all DB records",
    )
    parser.add_argument(
        "--recategorize-healthcaremagic",
        action="store_true",
        help="Re-run categorization on all existing healthcaremagic_records in-place (no HuggingFace fetch).",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help=(
            "With --rebuild-brain: call Claude API to regenerate rich knowledge sections "
            "(Source Priority, Terminology Map, Query Patterns, Rules, Pitfalls). "
            "Requires ANTHROPIC_API_KEY in .env. Slow — run after major ingestion milestones."
        ),
    )
    args = parser.parse_args()

    conn = get_connection()

    try:
        if args.source in ("medmcqa", "both"):
            ingest_medmcqa(conn, limit=args.limit, start_offset=args.offset)

        if args.source in ("pubmedqa", "both"):
            ingest_pubmedqa(conn)

        if args.source == "medquad":
            ingest_medquad(conn, csv_path=args.medquad_path)

        if args.source == "healthcaremagic":
            ingest_healthcaremagic(conn, limit=args.limit, start_offset=args.offset)

        if args.recategorize_healthcaremagic:
            recategorize_healthcaremagic(conn)

        if args.rebuild_brain:
            rebuild_brain_from_db(conn, enrich=args.enrich)

        # Final counts
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM medmcqa_records;")
            med = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM pubmedqa_records;")
            pub = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM medquad_records;")
            mq = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM healthcaremagic_records;")
            hcm = cur.fetchone()[0]

        print(f"\nDatabase totals: medmcqa={med:,}  pubmedqa={pub:,}  medquad={mq:,}  healthcaremagic={hcm:,}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()