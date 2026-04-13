"""Run HealthBench comparing vanilla GPT-4o vs brain-augmented GPT-4o vs pipeline.

Usage:
    python run_healthbench.py                        # default: 50 examples (vanilla + brain)
    python run_healthbench.py --examples 20          # quick test
    python run_healthbench.py --examples 100         # larger run
    python run_healthbench.py --vanilla-only          # only run vanilla
    python run_healthbench.py --brain-only            # only run brain-augmented
    python run_healthbench.py --pipeline              # only run DB-backed pipeline (single-turn)
    python run_healthbench.py --pipeline --examples 3 # quick pipeline smoke test
"""

import argparse
import json
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from simple_evals.healthbench_eval import HealthBenchEval
from simple_evals.sampler.chat_completion_sampler import (
    OPENAI_SYSTEM_MESSAGE_API,
    ChatCompletionSampler,
)
from simple_evals.sampler.brain_sampler import BrainAugmentedSampler
from simple_evals import common


ENGLISH_STOPWORDS = {
    "the", "and", "is", "are", "to", "of", "in", "for", "with", "you",
    "your", "what", "how", "can", "should", "have", "this", "that",
}


def _extract_last_user_text(prompt_messages: list[dict]) -> str:
    """Extract the last user message as plain text from a prompt."""
    for msg in reversed(prompt_messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
                return " ".join(parts)
    return ""


def _looks_english(text: str) -> bool:
    """Heuristic English detector without external dependencies."""
    if not text.strip():
        return False

    # If too many letters are non-ASCII, treat as non-English.
    letters = [ch for ch in text if ch.isalpha()]
    if letters:
        ascii_ratio = sum(ord(ch) < 128 for ch in letters) / len(letters)
        if ascii_ratio < 0.85:
            return False

    # Require at least one common English stopword.
    words = re.findall(r"[A-Za-z']+", text.lower())
    if not words:
        return False
    return any(word in ENGLISH_STOPWORDS for word in words)


def _write_eval_artifacts(file_stem: str, result) -> None:
    """Persist report, metrics, and full per-example metadata for inspection."""
    report_path = Path(f"/tmp/{file_stem}.html")
    report_path.write_text(common.make_report(result), encoding="utf-8")
    print(f"\nHTML report: {report_path}")

    metrics_path = Path(f"/tmp/{file_stem}.json")
    metrics_path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    print(f"Metrics JSON: {metrics_path}")

    full_result = {
        "score": result.score,
        "metrics": result.metrics,
        "htmls": result.htmls,
        "convos": result.convos,
        "metadata": result.metadata,
    }
    full_path = Path(f"/tmp/{file_stem}_allresults.json")
    full_path.write_text(json.dumps(full_result, indent=2, default=str), encoding="utf-8")
    print(f"Full results (with rubric metadata): {full_path}")


def run_eval(name: str, sampler, grader, num_examples: int, n_threads: int) -> dict:
    """Run HealthBench with a given sampler and return metrics."""
    print(f"\n{'='*60}")
    print(f"  Running HealthBench: {name}")
    print(f"  Examples: {num_examples}, Threads: {n_threads}")
    print(f"{'='*60}\n")

    eval_obj = HealthBenchEval(
        grader_model=grader,
        num_examples=num_examples,
        n_threads=n_threads,
    )

    result = eval_obj(sampler)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_name = name.lower().replace(" ", "_").replace("-", "_")

    _write_eval_artifacts(file_stem=f"healthbench_{safe_name}_{timestamp}", result=result)

    return {
        "name": name,
        "score": result.score,
        "metrics": result.metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Run HealthBench evaluation")
    parser.add_argument(
        "--examples",
        type=int,
        default=50,
        help="Number of examples to evaluate (default: 50)",
    )
    parser.add_argument(
        "--n-threads",
        type=int,
        default=10,
        help="Number of parallel threads (default: 10)",
    )
    parser.add_argument(
        "--vanilla-only",
        action="store_true",
        help="Only run vanilla GPT-4o (no brain augmentation)",
    )
    parser.add_argument(
        "--brain-only",
        action="store_true",
        help="Only run brain-augmented GPT-4o",
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Run the four-agent DB-backed pipeline on single-turn examples only",
    )
    parser.add_argument(
        "--analyze-failures",
        action="store_true",
        help="Run pattern analyzer on pipeline results to tag and track failure patterns",
    )
    args = parser.parse_args()

    # Grader model (used to score responses against rubrics)
    print("Initializing grader model (GPT-4o for rubric grading)...")
    grader = ChatCompletionSampler(
        model="gpt-4o",
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )

    results = []

    if args.pipeline:
        # ── Pipeline mode: DB-backed four-agent pipeline on single-turn only ──
        import psycopg2
        from openai import OpenAI
        from src.pipeline import Pipeline
        from simple_evals.sampler.pipeline_sampler import PipelineHealthBenchSampler

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("ERROR: DATABASE_URL environment variable not set.")
            sys.exit(1)

        print("\nConnecting to database...")
        db_conn = psycopg2.connect(
            db_url,
            keepalives=1,
            keepalives_idle=10,
            keepalives_interval=5,
            keepalives_count=10,
            connect_timeout=30,
        )
        openai_client = OpenAI()

        print("Building pipeline (build_centroids=False, use_gpt4o=True)...")
        pipeline = Pipeline(
            db_conn=db_conn,
            openai_client=openai_client,
            anthropic_client=None,
            build_centroids=False,
            use_gpt4o=True,
        )
        sampler = PipelineHealthBenchSampler(pipeline=pipeline)

        # Load all examples via HealthBenchEval (parses rubrics), then filter
        eval_obj = HealthBenchEval(
            grader_model=grader,
            num_examples=None,
            n_threads=1,
        )

        all_count = len(eval_obj.examples)
        single_turn = [
            ex for ex in eval_obj.examples
            if not any(m["role"] == "assistant" for m in ex["prompt"])
        ]
        english_only = [
            ex for ex in single_turn
            if _looks_english(_extract_last_user_text(ex["prompt"]))
        ]
        print(f"  Total examples: {all_count}")
        print(f"  After single-turn filter: {len(single_turn)}")
        print(f"  After English-only filter: {len(english_only)}")

        if args.examples is not None and args.examples < len(english_only):
            rng = random.Random(0)
            english_only = rng.sample(english_only, args.examples)

        eval_obj.examples = english_only

        print(f"\n{'='*60}")
        print(f"  Running HealthBench: Pipeline (DB-backed)")
        print(f"  Examples: {len(english_only)}, Threads: 1")
        print(f"{'='*60}\n")

        result = eval_obj(sampler)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        _write_eval_artifacts(file_stem=f"healthbench_pipeline_{timestamp}", result=result)

        # Run pattern analyzer if requested
        if args.analyze_failures:
            import asyncio as _asyncio
            from src.evaluation.pattern_analyzer import PatternAnalyzer

            tracker_path = Path("src/evaluation/pattern_tracker.json")
            analyzer = PatternAnalyzer(
                results_path=Path(f"/tmp/healthbench_pipeline_{timestamp}_allresults.json"),
                tracker_path=tracker_path,
                learnings_path=Path("learnings.md"),
                openai_client=openai_client,
            )
            print("\nAnalyzing failure patterns...")
            summary = _asyncio.run(analyzer.analyze(run_id=f"eval_run_{timestamp}"))
            print(f"  Failures analyzed: {summary['failures_analyzed']}")
            print(f"  New pattern tags: {summary['new_tags']}")
            print(f"  Merged with existing: {summary['merged_tags']}")
            print(f"  Patterns graduated: {len(summary['graduated'])}")
            if summary['graduated']:
                print(f"  Graduated patterns: {', '.join(summary['graduated'])}")

        results.append({
            "name": "Pipeline (DB-backed)",
            "score": result.score,
            "metrics": result.metrics,
        })

        db_conn.close()

    else:
        # ── Default mode: vanilla GPT-4o and/or brain-augmented ───────────
        if not args.brain_only:
            print("\nInitializing vanilla GPT-4o sampler...")
            vanilla_sampler = ChatCompletionSampler(
                model="gpt-4o",
                system_message=OPENAI_SYSTEM_MESSAGE_API,
                max_tokens=4096,
            )
            vanilla_result = run_eval(
                "Vanilla GPT-4o",
                vanilla_sampler,
                grader,
                args.examples,
                args.n_threads,
            )
            results.append(vanilla_result)

        if not args.vanilla_only:
            print("\nInitializing brain-augmented GPT-4o sampler...")
            brain_sampler = BrainAugmentedSampler(
                model="gpt-4o",
                max_tokens=4096,
            )
            brain_result = run_eval(
                "Brain-Augmented GPT-4o",
                brain_sampler,
                grader,
                args.examples,
                args.n_threads,
            )
            results.append(brain_result)

    # ── Print comparison ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  RESULTS COMPARISON")
    print(f"{'='*60}\n")

    for r in results:
        score = r["score"]
        overall = r["metrics"].get("overall_score", score)
        print(f"  {r['name']}:")
        print(f"    Overall Score: {overall:.4f}" if overall else f"    Overall Score: {score}")

        for key, val in sorted(r["metrics"].items()):
            if ":" not in key and key != "overall_score" and isinstance(val, float):
                print(f"    {key}: {val:.4f}")
        print()

    if len(results) == 2 and not args.pipeline:
        v_score = results[0]["metrics"].get("overall_score", results[0]["score"])
        b_score = results[1]["metrics"].get("overall_score", results[1]["score"])
        diff = b_score - v_score
        print(f"  Difference (Brain - Vanilla): {diff:+.4f}")
        if diff > 0:
            print(f"  Brain augmentation improved score by {diff*100:.1f} percentage points")
        elif diff < 0:
            print(f"  Brain augmentation decreased score by {abs(diff)*100:.1f} percentage points")
        else:
            print("  No difference")

    # Save combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    combined_path = Path(f"/tmp/healthbench_comparison_{timestamp}.json")
    combined_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nCombined results: {combined_path}")


if __name__ == "__main__":
    main()
