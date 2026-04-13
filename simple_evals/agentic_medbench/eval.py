"""Agentic MedBench evaluation runner.

Orchestrates the full evaluation pipeline: load test cases, run the agent
sampler, grade across five dimensions, compute a unified score, and
aggregate results.  Follows the same structural pattern as
``simple_evals.healthbench_eval.HealthBenchEval``.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from .. import common
from ..types import Eval, EvalResult, MessageList, SamplerBase, SingleEvalResult
from .graders import grade_all_dimensions
from .types import DIMENSION_WEIGHTS, AgentTrace, compute_unified_score

# ---------------------------------------------------------------------------
# Data directory — default location for the test-case JSONL file
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"
_DEFAULT_TEST_CASES_PATH = str(_DATA_DIR / "agentic_medbench.jsonl")

# ---------------------------------------------------------------------------
# HTML template for per-example rendering
# ---------------------------------------------------------------------------

_EXAMPLE_HTML_TEMPLATE = """
<div style="border:1px solid #ccc; padding:16px; margin-bottom:24px; border-radius:8px;">
  <h3>Scenario</h3>
  {% for message in prompt_messages %}
  {{ message_to_html(message) | safe }}
  {% endfor %}

  <h3>Agent Response</h3>
  {{ message_to_html(next_message) | safe }}

  <h3>Unified Score: {{ "%.3f"|format(unified_score) }}</h3>

  <h4>Per-Dimension Scores</h4>
  <table style="border-collapse:collapse; width:100%;">
    <tr><th style="text-align:left; padding:4px; border-bottom:1px solid #ddd;">Dimension</th>
        <th style="text-align:left; padding:4px; border-bottom:1px solid #ddd;">Weight</th>
        <th style="text-align:left; padding:4px; border-bottom:1px solid #ddd;">Score</th></tr>
    {% for dim_name, dim_result in dimensions.items() %}
    <tr>
      <td style="padding:4px;">{{ dim_name }}</td>
      <td style="padding:4px;">{{ dim_weights[dim_name] }}</td>
      <td style="padding:4px;">{{ "%.3f"|format(dim_result.score) }}</td>
    </tr>
    {% endfor %}
  </table>

  {% if tool_calls %}
  <h4>Tool Calls</h4>
  <ol>
    {% for tc in tool_calls %}
    <li><b>{{ tc.tool_name }}</b> — {{ tc.arguments }} &rarr; {{ tc.result }}</li>
    {% endfor %}
  </ol>
  {% endif %}

  {% if reasoning_trace %}
  <h4>Reasoning Trace</h4>
  <ol>
    {% for step in reasoning_trace %}
    <li>{{ step }}</li>
    {% endfor %}
  </ol>
  {% endif %}

  <h4>Grader Details</h4>
  {% for dim_name, dim_result in dimensions.items() %}
  <details>
    <summary><b>{{ dim_name }}</b> ({{ "%.3f"|format(dim_result.score) }})</summary>
    <pre style="white-space:pre-wrap;">{{ dim_result.explanation }}</pre>
  </details>
  {% endfor %}
</div>
"""

# ---------------------------------------------------------------------------
# Aggregation helper (clipped mean + bootstrap std, matches HealthBench)
# ---------------------------------------------------------------------------


def _compute_clipped_stats(values: list, stat: str) -> float:
    """Compute a single statistic from a list of values.

    For ``"mean"`` the result is clipped to [0, 1].  For
    ``"bootstrap_std"`` 1000 bootstrap re-samplings are used.

    Args:
        values: List of numeric values.
        stat: One of ``"mean"``, ``"n_samples"``, ``"bootstrap_std"``.

    Returns:
        The computed statistic.
    """
    if stat == "mean":
        return float(np.clip(np.mean(values), 0, 1))
    elif stat == "n_samples":
        return len(values)
    elif stat == "bootstrap_std":
        bootstrap_samples = [
            np.random.choice(values, len(values)) for _ in range(1000)
        ]
        bootstrap_means = [
            _compute_clipped_stats(list(s), "mean") for s in bootstrap_samples
        ]
        return float(np.std(bootstrap_means))
    else:
        raise ValueError(f"Unknown stat: {stat}")


def _aggregate_results(
    single_eval_results: list[SingleEvalResult],
) -> EvalResult:
    """Aggregate multiple SingleEvalResults into a single EvalResult.

    For each metric the function computes:
    - **mean** (clipped to [0, 1])
    - **n_samples**
    - **bootstrap_std** (1000 re-samplings)

    This mirrors ``healthbench_eval._aggregate_get_clipped_mean``.

    Args:
        single_eval_results: List of per-example evaluation results.

    Returns:
        An ``EvalResult`` with aggregated metrics, HTML reports, and
        conversation logs.
    """
    name2values: dict[str, list[float]] = defaultdict(list)
    htmls: list[str] = []
    convos: list[MessageList] = []
    metadata: list[Any] = []

    for ser in single_eval_results:
        for name, value in ser.metrics.items():
            name2values[name].append(value)
        if ser.score is not None:
            name2values["score"].append(ser.score)
        htmls.append(ser.html)
        convos.append(ser.convo)
        metadata.append(ser.example_level_metadata)

    final_metrics: dict[str, float] = {}
    for name, values in name2values.items():
        for stat in ("mean", "n_samples", "bootstrap_std"):
            key = name if stat == "mean" else f"{name}:{stat}"
            final_metrics[key] = _compute_clipped_stats(values, stat)

    return EvalResult(
        score=final_metrics.pop("score", None),
        metrics=final_metrics,
        htmls=htmls,
        convos=convos,
        metadata={"example_level_metadata": metadata},
    )


# ---------------------------------------------------------------------------
# Helper: extract or build an AgentTrace from a sampler response
# ---------------------------------------------------------------------------


def _extract_agent_trace(
    response_text: str,
    response_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build an agent-trace dict from a sampler response.

    If *response_metadata* contains an ``"agent_trace"`` key (as
    produced by :class:`AgenticMedBenchSampler`), that dict is returned
    directly.  Otherwise a minimal trace is constructed from the plain
    response text.

    Args:
        response_text: The agent's textual response.
        response_metadata: Metadata dict from the sampler.

    Returns:
        A dict suitable for passing to the grader agents.
    """
    if "agent_trace" in response_metadata:
        trace = response_metadata["agent_trace"]
        # If it's an AgentTrace dataclass, convert to dict
        if isinstance(trace, AgentTrace):
            return trace.to_dict()
        return trace

    # Fallback: wrap the plain text into a minimal trace
    return {
        "final_answer": response_text,
        "tool_calls": [],
        "reasoning_trace": [],
        "corrections": [],
        "retrieval_results": [],
    }


# ---------------------------------------------------------------------------
# Main evaluation class
# ---------------------------------------------------------------------------


class AgenticMedBenchEval(Eval):
    """Agentic MedBench evaluation runner.

    Loads test cases, runs a sampler (agent) on each case, grades
    across five dimensions via LLM grader agents, computes a
    unified score, and aggregates all results.

    Args:
        grader_model: A :class:`SamplerBase` used by the grader agents.
        test_cases: Pre-loaded list of test-case dicts.  Mutually
            exclusive with *test_cases_path*.
        test_cases_path: Path to a JSONL file containing test cases.
            Defaults to ``data/agentic_medbench.jsonl`` in the package.
        num_examples: If set, randomly sample this many test cases
            (seed=0).
        n_threads: Number of threads for parallel evaluation via
            :func:`common.map_with_progress`.
    """

    def __init__(
        self,
        grader_model: SamplerBase,
        test_cases: list[dict] | None = None,
        test_cases_path: str | None = None,
        num_examples: int | None = None,
        n_threads: int = 10,
    ) -> None:
        self.grader_model = grader_model
        self.n_threads = n_threads

        # --- Load test cases ------------------------------------------------
        if test_cases is not None:
            examples = list(test_cases)
        else:
            path = test_cases_path or _DEFAULT_TEST_CASES_PATH
            with open(path, "r", encoding="utf-8") as fh:
                examples = [json.loads(line) for line in fh]

        # --- Optional sampling ----------------------------------------------
        if num_examples is not None and num_examples < len(examples):
            rng = random.Random(0)
            examples = rng.sample(examples, num_examples)

        self.examples = examples

    # ------------------------------------------------------------------ #
    # __call__: the main evaluation loop
    # ------------------------------------------------------------------ #

    def __call__(self, sampler: SamplerBase) -> EvalResult:
        """Run the full evaluation.

        For each test case:
        1. Call *sampler* to get the agent's response.
        2. Extract or construct an ``AgentTrace``.
        3. Grade across all five dimensions.
        4. Compute a unified score (clipped to [0, 1]).
        5. Build metrics and per-example HTML.

        Args:
            sampler: The agent sampler under evaluation.

        Returns:
            An aggregated :class:`EvalResult`.
        """

        def fn(row: dict) -> SingleEvalResult:
            conversation = row["conversation"]

            # 1. Run the sampler (agent)
            sampler_response = sampler(conversation)
            response_text = sampler_response.response_text
            response_metadata = sampler_response.response_metadata
            actual_queried = sampler_response.actual_queried_message_list

            # 2. Extract agent trace
            agent_trace = _extract_agent_trace(response_text, response_metadata)

            # 3. Grade all dimensions
            dim_results = grade_all_dimensions(
                agent_trace, row, self.grader_model
            )

            # 4. Compute unified score
            dim_scores = {
                dim: res["score"] for dim, res in dim_results.items()
            }
            unified_score = compute_unified_score(dim_scores)
            unified_score = float(np.clip(unified_score, 0.0, 1.0))

            # 5. Build metrics
            metrics: dict[str, float] = {
                "overall_score": unified_score,
            }
            # Per-dimension scores
            for dim_name, dim_res in dim_results.items():
                metrics[dim_name] = dim_res["score"]

            # Per-tag scores
            tags = row.get("tags", [])
            for tag in tags:
                metrics[f"tag:{tag}"] = unified_score

            # Per-difficulty scores
            difficulty = row.get("difficulty", "unknown")
            metrics[f"difficulty:{difficulty}"] = unified_score

            # 6. Build HTML
            # Create lightweight namespace objects for template rendering
            class _DimView:
                """Lightweight view for template rendering."""
                def __init__(self, score: float, explanation: str):
                    self.score = score
                    self.explanation = explanation

            dim_views = {
                dn: _DimView(dr["score"], dr.get("explanation", ""))
                for dn, dr in dim_results.items()
            }

            html = common.jinja_env.from_string(_EXAMPLE_HTML_TEMPLATE).render(
                prompt_messages=actual_queried,
                next_message={"role": "assistant", "content": response_text},
                unified_score=unified_score,
                dimensions=dim_views,
                dim_weights=DIMENSION_WEIGHTS,
                tool_calls=agent_trace.get("tool_calls", []),
                reasoning_trace=agent_trace.get("reasoning_trace", []),
            )

            convo = list(actual_queried) + [
                {"role": "assistant", "content": response_text}
            ]

            return SingleEvalResult(
                score=unified_score,
                metrics=metrics,
                html=html,
                convo=convo,
                example_level_metadata={
                    "unified_score": unified_score,
                    "dimension_results": {
                        dn: {"score": dr["score"], "explanation": dr.get("explanation", "")}
                        for dn, dr in dim_results.items()
                    },
                    "agent_trace": agent_trace,
                    "conversation": row["conversation"],
                    "response": response_text,
                },
            )

        # Run evaluation in parallel
        results = common.map_with_progress(
            fn,
            self.examples,
            num_threads=self.n_threads,
            pbar=True,
        )

        return _aggregate_results(results)
