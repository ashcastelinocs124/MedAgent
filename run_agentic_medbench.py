"""Run the Agentic MedBench 3x4 evaluation matrix.

Evaluates the agentic medical QA system across three experimental conditions
(baseline, brain_steered, fully_steered) and four user profiles (default,
low_literacy_patient, high_literacy_nurse, elderly_comorbid).

Usage:
    python run_agentic_medbench.py                                # full 3x4 matrix, 20 examples
    python run_agentic_medbench.py --examples 10                  # quick test
    python run_agentic_medbench.py --condition baseline            # single condition, all profiles
    python run_agentic_medbench.py --profile default               # single profile, all conditions
    python run_agentic_medbench.py --generate-cases 50             # generate test cases first
    python run_agentic_medbench.py --test-cases path/to/cases.jsonl
"""

import argparse
import json
import logging
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from simple_evals import common
from simple_evals.agentic_medbench.agent_sampler import AgenticSampler, AgentCondition
from simple_evals.agentic_medbench.eval import AgenticMedBenchEval
from simple_evals.agentic_medbench.pipeline_sampler import PipelineSampler
from simple_evals.healthbench_eval import HealthBenchEval, INPUT_PATH as HEALTHBENCH_INPUT_PATH
from simple_evals.agentic_medbench.profiles import PROFILE_PRESETS
from simple_evals.agentic_medbench.types import DIMENSION_WEIGHTS
from simple_evals.sampler.chat_completion_sampler import (
    OPENAI_SYSTEM_MESSAGE_API,
    ChatCompletionSampler,
)
from src.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_CONDITIONS = ["baseline", "brain_steered", "fully_steered"]
ALL_PROFILES = list(PROFILE_PRESETS.keys())

# ---------------------------------------------------------------------------
# Test case generation
# ---------------------------------------------------------------------------


def generate_test_cases(n: int, output_path: Path) -> list[dict]:
    """Generate N test cases from HealthBench and save to JSONL.

    Loads HealthBench examples, samples N of them (seed 42), augments each
    with agentic metadata, and writes the results to *output_path*.

    Args:
        n: Number of test cases to generate.
        output_path: Path where the JSONL file will be written.

    Returns:
        List of augmented test-case dicts.
    """
    from simple_evals.agentic_medbench.generate_cases import augment_healthbench_example
    from simple_evals.healthbench_eval import RubricItem

    healthbench_path = Path("simple_evals/data/healthbench.jsonl")
    if not healthbench_path.exists():
        print(f"ERROR: HealthBench data not found at {healthbench_path}")
        sys.exit(1)

    print(f"Loading HealthBench examples from {healthbench_path}...")
    with open(healthbench_path, "r", encoding="utf-8") as fh:
        raw_examples = [json.loads(line) for line in fh]

    print(f"Loaded {len(raw_examples)} HealthBench examples.")

    # Sample N examples with fixed seed
    rng = random.Random(42)
    if n < len(raw_examples):
        sampled = rng.sample(raw_examples, n)
    else:
        sampled = raw_examples
        print(f"Warning: requested {n} examples but only {len(raw_examples)} available.")

    # Parse rubrics into RubricItem objects
    for example in sampled:
        if "rubrics" in example:
            example["rubrics"] = [
                RubricItem.from_dict(r) if isinstance(r, dict) else r
                for r in example["rubrics"]
            ]

    # Create augmenter model
    print("Initializing augmenter model (GPT-4o)...")
    augmenter = ChatCompletionSampler(
        model="gpt-4o",
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )

    # Augment each example
    print(f"Augmenting {len(sampled)} examples with agentic metadata...")
    test_cases = []
    for i, example in enumerate(sampled):
        print(f"  Augmenting {i + 1}/{len(sampled)}...", end="\r")
        case = augment_healthbench_example(example, augmenter)
        test_cases.append(case)

    print(f"\nGenerated {len(test_cases)} test cases.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSONL
    with open(output_path, "w", encoding="utf-8") as fh:
        for case in test_cases:
            fh.write(json.dumps(case, default=str) + "\n")

    print(f"Saved test cases to {output_path}")
    return test_cases


# ---------------------------------------------------------------------------
# Pipeline sampler builder
# ---------------------------------------------------------------------------


def _build_pipeline_sampler(profile: str) -> PipelineSampler:
    """Instantiate a Pipeline from env vars and wrap it as a PipelineSampler.

    Requires DATABASE_URL and OPENAI_API_KEY in the environment (or .env file).

    Args:
        profile: Profile preset name (e.g. 'default', 'low_literacy_patient').

    Returns:
        A ready-to-use PipelineSampler.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set.")
        sys.exit(1)

    print(f"  Connecting to database...")
    db_conn = psycopg2.connect(db_url)

    openai_client = OpenAI()

    print(f"  Building pipeline (build_centroids=False for eval speed)...")
    pipeline = Pipeline(
        db_conn=db_conn,
        openai_client=openai_client,
        anthropic_client=None,
        build_centroids=False,  # Skips centroid precompute for speed; Agent A falls
                                # directly from keyword match to LLM classification
                                # (no embedding-similarity tier), which shifts
                                # classification_method distribution in eval traces.
        use_gpt4o=True,
    )

    return PipelineSampler(pipeline=pipeline, profile_name=profile)


# ---------------------------------------------------------------------------
# Single run helper
# ---------------------------------------------------------------------------


def run_single_eval(
    condition: str,
    profile: str,
    grader: ChatCompletionSampler,
    test_cases_path: str,
    num_examples: int,
    n_threads: int,
) -> dict:
    """Run a single condition x profile evaluation and return results.

    Args:
        condition: One of 'baseline', 'brain_steered', 'fully_steered'.
        profile: Profile preset name from PROFILE_PRESETS.
        grader: The grader model for rubric scoring.
        test_cases_path: Path to JSONL test cases.
        num_examples: Number of examples to evaluate.
        n_threads: Thread count for parallel evaluation.

    Returns:
        Dict with 'condition', 'profile', 'score', 'metrics', and
        per-dimension scores.
    """
    label = f"{condition} / {profile}"
    print(f"\n{'=' * 60}")
    print(f"  Running: {label}")
    print(f"  Examples: {num_examples}, Threads: {n_threads}")
    print(f"{'=' * 60}\n")

    # Create the agentic sampler
    agent_condition = AgentCondition(condition)
    sampler = AgenticSampler(
        model="gpt-4o",
        condition=agent_condition,
        profile_name=profile,
    )

    # Create the eval
    eval_obj = AgenticMedBenchEval(
        grader_model=grader,
        test_cases_path=test_cases_path,
        num_examples=num_examples,
        n_threads=n_threads,
    )

    # Run
    result = eval_obj(sampler)

    # Save per-run artefacts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = f"{condition}_{profile}"

    report_path = Path(f"/tmp/agentic_medbench_{safe_label}_{timestamp}.html")
    report_path.write_text(common.make_report(result), encoding="utf-8")
    print(f"  HTML report: {report_path}")

    metrics_path = Path(f"/tmp/agentic_medbench_{safe_label}_{timestamp}.json")
    metrics_path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {metrics_path}")

    return {
        "condition": condition,
        "profile": profile,
        "score": result.score,
        "metrics": result.metrics,
    }


def run_pipeline_eval(
    profile: str,
    grader: ChatCompletionSampler,
    test_cases_path: str,
    num_examples: int,
) -> dict:
    """Run a single pipeline x profile evaluation.

    Uses n_threads=1 — psycopg2 connections are not thread-safe.

    Args:
        profile: Profile preset name.
        grader: The grader model for rubric scoring.
        test_cases_path: Path to JSONL test cases.
        num_examples: Number of examples to evaluate.

    Returns:
        Dict with 'condition', 'profile', 'score', 'metrics'.
    """
    label = f"pipeline / {profile}"
    print(f"\n{'=' * 60}")
    print(f"  Running: {label}")
    print(f"  Examples: {num_examples}, Threads: 1 (psycopg2 not thread-safe)")
    print(f"{'=' * 60}\n")

    sampler = _build_pipeline_sampler(profile)

    eval_obj = AgenticMedBenchEval(
        grader_model=grader,
        test_cases_path=test_cases_path,
        num_examples=num_examples,
        n_threads=1,
    )

    result = eval_obj(sampler)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = f"pipeline_{profile}"

    report_path = Path(f"/tmp/agentic_medbench_{safe_label}_{timestamp}.html")
    report_path.write_text(common.make_report(result), encoding="utf-8")
    print(f"  HTML report: {report_path}")

    metrics_path = Path(f"/tmp/agentic_medbench_{safe_label}_{timestamp}.json")
    metrics_path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {metrics_path}")

    return {
        "condition": "pipeline",
        "profile": profile,
        "score": result.score,
        "metrics": result.metrics,
    }


def run_healthbench_eval(
    profile: str,
    grader: ChatCompletionSampler,
    num_examples: int,
) -> dict:
    """Run the original HealthBench eval using PipelineSampler as the underlying model.

    Uses the pipeline's final answer text graded against HealthBench rubrics —
    no tool-calling or reasoning trace, mirroring how OpenAI's benchmark works.
    Uses n_threads=1 (psycopg2 not thread-safe).

    Args:
        profile: Profile preset name.
        grader: The grader model for rubric scoring.
        num_examples: Number of HealthBench examples to evaluate.

    Returns:
        Dict with 'condition', 'profile', 'score', 'metrics'.
    """
    label = f"healthbench / {profile}"
    print(f"\n{'=' * 60}")
    print(f"  Running: {label}")
    print(f"  Examples: {num_examples}, Threads: 1 (psycopg2 not thread-safe)")
    print(f"{'=' * 60}\n")

    sampler = _build_pipeline_sampler(profile)

    eval_obj = HealthBenchEval(
        grader_model=grader,
        num_examples=num_examples,
        n_threads=1,
    )

    result = eval_obj(sampler)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = f"healthbench_{profile}"

    report_path = Path(f"/tmp/agentic_medbench_{safe_label}_{timestamp}.html")
    report_path.write_text(common.make_report(result), encoding="utf-8")
    print(f"  HTML report: {report_path}")

    metrics_path = Path(f"/tmp/agentic_medbench_{safe_label}_{timestamp}.json")
    metrics_path.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {metrics_path}")

    return {
        "condition": "healthbench",
        "profile": profile,
        "score": result.score,
        "metrics": result.metrics,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def print_results_matrix(results: list[dict], conditions: list[str], profiles: list[str]) -> None:
    """Print a formatted comparison matrix of overall scores.

    Args:
        results: List of result dicts from run_single_eval.
        conditions: Ordered list of condition names.
        profiles: Ordered list of profile names.
    """
    # Build lookup: (condition, profile) -> score
    score_lookup: dict[tuple[str, str], float] = {}
    for r in results:
        overall = r["metrics"].get("overall_score", r["score"])
        score_lookup[(r["condition"], r["profile"])] = overall

    # Column widths
    profile_col_width = max(len(p) for p in profiles) + 2
    cond_col_width = max(len(c) for c in conditions) + 2
    cond_col_width = max(cond_col_width, 16)

    print(f"\n{'=' * 70}")
    print("  RESULTS COMPARISON MATRIX")
    print(f"{'=' * 70}\n")

    # Header row
    header = f"{'Profile':<{profile_col_width}}"
    for c in conditions:
        header += f"{c:>{cond_col_width}}"
    print(header)
    print("-" * len(header))

    # Data rows
    for p in profiles:
        row = f"{p:<{profile_col_width}}"
        for c in conditions:
            score = score_lookup.get((c, p))
            if score is not None:
                row += f"{score:>{cond_col_width}.4f}"
            else:
                row += f"{'N/A':>{cond_col_width}}"
        print(row)

    print()


def print_dimension_breakdown(results: list[dict], conditions: list[str], profiles: list[str]) -> None:
    """Print per-dimension score breakdown for each condition x profile.

    Args:
        results: List of result dicts from run_single_eval.
        conditions: Ordered list of condition names.
        profiles: Ordered list of profile names.
    """
    dimensions = list(DIMENSION_WEIGHTS.keys())

    print(f"\n{'=' * 70}")
    print("  PER-DIMENSION BREAKDOWN")
    print(f"{'=' * 70}\n")

    # Build lookup
    metrics_lookup: dict[tuple[str, str], dict] = {}
    for r in results:
        metrics_lookup[(r["condition"], r["profile"])] = r["metrics"]

    for dim in dimensions:
        weight = DIMENSION_WEIGHTS[dim]
        print(f"  {dim} (weight: {weight})")

        profile_col_width = max(len(p) for p in profiles) + 2
        cond_col_width = max(len(c) for c in conditions) + 2
        cond_col_width = max(cond_col_width, 16)

        header = f"    {'Profile':<{profile_col_width}}"
        for c in conditions:
            header += f"{c:>{cond_col_width}}"
        print(header)
        print(f"    {'-' * (len(header) - 4)}")

        for p in profiles:
            row = f"    {p:<{profile_col_width}}"
            for c in conditions:
                metrics = metrics_lookup.get((c, p), {})
                score = metrics.get(dim)
                if score is not None:
                    row += f"{score:>{cond_col_width}.4f}"
                else:
                    row += f"{'N/A':>{cond_col_width}}"
            print(row)

        print()


def print_lift_analysis(results: list[dict], profiles: list[str]) -> None:
    """Print graph lift analysis comparing conditions.

    Shows three lift metrics:
    - Brain-only lift: brain_steered - baseline
    - Full graph lift: fully_steered - baseline
    - Personalization lift: fully_steered - brain_steered

    Args:
        results: List of result dicts from run_single_eval.
        profiles: Ordered list of profile names.
    """
    # Build lookup
    score_lookup: dict[tuple[str, str], float] = {}
    for r in results:
        overall = r["metrics"].get("overall_score", r["score"])
        if overall is not None:
            score_lookup[(r["condition"], r["profile"])] = overall

    # Check that we have all three conditions for at least some profiles
    has_baseline = any((("baseline", p) in score_lookup) for p in profiles)
    has_brain = any((("brain_steered", p) in score_lookup) for p in profiles)
    has_full = any((("fully_steered", p) in score_lookup) for p in profiles)

    if not (has_baseline and has_brain and has_full):
        print("\n  (Lift analysis requires all three conditions; skipping.)\n")
        return

    print(f"\n{'=' * 70}")
    print("  GRAPH LIFT ANALYSIS")
    print(f"{'=' * 70}\n")

    profile_col_width = max(len(p) for p in profiles) + 2
    lift_col_width = 20

    header = (
        f"{'Profile':<{profile_col_width}}"
        f"{'Brain-only':>{lift_col_width}}"
        f"{'Full graph':>{lift_col_width}}"
        f"{'Personalization':>{lift_col_width}}"
    )
    print(header)
    print("-" * len(header))

    for p in profiles:
        baseline_score = score_lookup.get(("baseline", p))
        brain_score = score_lookup.get(("brain_steered", p))
        full_score = score_lookup.get(("fully_steered", p))

        row = f"{p:<{profile_col_width}}"

        # Brain-only lift: brain_steered - baseline
        if brain_score is not None and baseline_score is not None:
            brain_lift = brain_score - baseline_score
            row += f"{brain_lift:>+{lift_col_width}.4f}"
        else:
            row += f"{'N/A':>{lift_col_width}}"

        # Full graph lift: fully_steered - baseline
        if full_score is not None and baseline_score is not None:
            full_lift = full_score - baseline_score
            row += f"{full_lift:>+{lift_col_width}.4f}"
        else:
            row += f"{'N/A':>{lift_col_width}}"

        # Personalization lift: fully_steered - brain_steered
        if full_score is not None and brain_score is not None:
            personal_lift = full_score - brain_score
            row += f"{personal_lift:>+{lift_col_width}.4f}"
        else:
            row += f"{'N/A':>{lift_col_width}}"

        print(row)

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Agentic MedBench 3x4 evaluation matrix.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_agentic_medbench.py --examples 10\n"
            "  python run_agentic_medbench.py --condition baseline --profile default\n"
            "  python run_agentic_medbench.py --generate-cases 50 --examples 20\n"
        ),
    )

    parser.add_argument(
        "--examples",
        type=int,
        default=20,
        help="Number of test examples to evaluate per run (default: 20)",
    )
    parser.add_argument(
        "--n-threads",
        type=int,
        default=10,
        help="Number of parallel threads (default: 10)",
    )
    parser.add_argument(
        "--condition",
        type=str,
        choices=ALL_CONDITIONS,
        default=None,
        help="Run a single condition (default: all three)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=ALL_PROFILES,
        default=None,
        help="Run a single profile (default: all four)",
    )
    parser.add_argument(
        "--test-cases",
        type=str,
        default=None,
        help="Path to JSONL file with test cases",
    )
    parser.add_argument(
        "--generate-cases",
        type=int,
        default=0,
        help="Generate N test cases from HealthBench before running (default: 0)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["openai", "pipeline", "healthbench"],
        default="openai",
        help=(
            "Evaluation mode. 'openai' runs AgenticSampler (GPT-4o + live APIs). "
            "'pipeline' runs PipelineSampler on the agentic eval (5 dimensions). "
            "'healthbench' runs PipelineSampler on the original HealthBench rubric eval "
            "(answer quality only, mirrors the OpenAI benchmark). Default: openai"
        ),
    )

    args = parser.parse_args()

    # Resolve which conditions and profiles to run
    conditions = [args.condition] if args.condition else ALL_CONDITIONS
    profiles = [args.profile] if args.profile else ALL_PROFILES

    # Resolve test cases path
    default_cases_path = "simple_evals/agentic_medbench/data/agentic_medbench.jsonl"

    # Generate test cases if requested
    if args.generate_cases > 0:
        output_path = Path(default_cases_path)
        generate_test_cases(args.generate_cases, output_path)
        test_cases_path = str(output_path)
    elif args.test_cases:
        test_cases_path = args.test_cases
    else:
        test_cases_path = default_cases_path

    # healthbench mode uses the HealthBench dataset directly — skip test-cases check
    if args.mode != "healthbench":
        if not Path(test_cases_path).exists():
            print(f"ERROR: Test cases file not found: {test_cases_path}")
            print("  Use --generate-cases N to generate test cases from HealthBench,")
            print("  or use --test-cases to specify an existing JSONL file.")
            sys.exit(1)

    print(f"\nMedBench Evaluation")
    print(f"  Mode:       {args.mode}")
    if args.mode == "openai":
        print(f"  Conditions: {conditions}")
    print(f"  Profiles:   {profiles}")
    print(f"  Examples:   {args.examples}")
    if args.mode == "openai":
        print(f"  Threads:    {args.n_threads}")
    else:
        print(f"  Threads:    1 (psycopg2 not thread-safe)")
    if args.mode != "healthbench":
        print(f"  Test cases: {test_cases_path}")
    else:
        print(f"  Dataset:    HealthBench ({HEALTHBENCH_INPUT_PATH})")

    # Initialize grader model (used by all modes)
    print("\nInitializing grader model (GPT-4o)...")
    grader = ChatCompletionSampler(
        model="gpt-4o",
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )

    all_results: list[dict] = []

    if args.mode == "healthbench":
        for profile in profiles:
            result = run_healthbench_eval(
                profile=profile,
                grader=grader,
                num_examples=args.examples,
            )
            all_results.append(result)
    elif args.mode == "pipeline":
        for profile in profiles:
            result = run_pipeline_eval(
                profile=profile,
                grader=grader,
                test_cases_path=test_cases_path,
                num_examples=args.examples,
            )
            all_results.append(result)
    else:
        for condition in conditions:
            for profile in profiles:
                result = run_single_eval(
                    condition=condition,
                    profile=profile,
                    grader=grader,
                    test_cases_path=test_cases_path,
                    num_examples=args.examples,
                    n_threads=args.n_threads,
                )
                all_results.append(result)

    # Output results
    eval_conditions = (
        conditions if args.mode == "openai"
        else ["pipeline"] if args.mode == "pipeline"
        else ["healthbench"]
    )
    print_results_matrix(all_results, eval_conditions, profiles)
    print_dimension_breakdown(all_results, eval_conditions, profiles)
    if args.mode == "openai":
        print_lift_analysis(all_results, profiles)

    # Save combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_path = Path(f"/tmp/agentic_medbench_matrix_{timestamp}.json")
    combined_path.write_text(json.dumps(all_results, indent=2, default=str), encoding="utf-8")
    print(f"Combined results saved to: {combined_path}")


if __name__ == "__main__":
    main()
