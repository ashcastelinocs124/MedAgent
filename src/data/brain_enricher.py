"""
Brain Enricher

Provides two modes of brain enrichment:

1. Data-driven (free, no API):
   compute_category_links(stats) -> derives category links from co-occurrence

2. OpenAI API (requires OPENAI_API_KEY):
   enrich_category_with_claude(...)  -> generates rich knowledge sections per category
   enrich_general_rules_with_claude(...) -> regenerates general_rules.md from data patterns

Usage:
    from brain_enricher import compute_category_links, enrich_category_with_claude
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

# Imported at call-time to avoid hard dependency when not using --enrich
# from openai import OpenAI

# Keep in sync with categorize.py
CATEGORY_LABELS = {
    "heart_blood_vessels": "Heart & Blood Vessels",
    "brain_nervous_system": "Brain & Nervous System",
    "mental_health": "Mental Health",
    "digestive_liver": "Digestive System & Liver",
    "breathing_lungs": "Breathing & Lungs",
    "blood_immune": "Blood & Immune Disorders",
    "cancer": "Cancer",
    "infections": "Infections & Infectious Disease",
    "bones_joints_muscles": "Bones, Joints & Muscles",
    "kidney_urinary": "Kidney & Urinary Health",
    "womens_reproductive": "Women's & Reproductive Health",
    "childrens_health": "Children's Health",
    "eye_health": "Eye Health",
    "ear_nose_throat": "Ear, Nose & Throat",
    "skin_dermatology": "Skin & Dermatology",
    "medications_drug_safety": "Medications & Drug Safety",
    "hormones_metabolism_nutrition": "Hormones, Metabolism & Nutrition",
    "emergency_critical_care": "Emergency & Critical Care",
    "dental_oral": "Dental & Oral Health",
    "public_health_prevention": "Public Health & Prevention",
}


def compute_category_links(stats: dict) -> dict[str, dict]:
    """
    Derive category-to-category links from secondary_category co-occurrence data.

    Args:
        stats: Output of compute_stats() — must contain "secondary_by_primary" key.

    Returns:
        dict mapping primary_cat -> {"strong": [(cat, count), ...], "weak": [(cat, count), ...]}
        Strong = top 3 co-occurring secondary categories
        Weak   = next 3 (positions 4-6)
    """
    links: dict[str, dict] = {}
    secondary_by_primary: dict[str, Counter] = stats.get("secondary_by_primary", {})

    for cat, secondary_counts in secondary_by_primary.items():
        top = secondary_counts.most_common(8)
        links[cat] = {
            "strong": top[:3],
            "weak": top[3:6],
        }

    return links


def enrich_category_with_claude(
    cat: str,
    label: str,
    stats: dict,
    cat_results: list[dict],
    links: dict,
) -> dict:
    """
    Call OpenAI API (GPT-4o) to generate rich knowledge sections for a single category.

    Sends the top 30 TIER_A questions (with their exp field) plus co-occurrence
    link data as context. Returns a dict with keys:
        subcategories, source_priority, source_priority_rationale,
        terminology_map, query_patterns, rules, pitfalls, dominant_style

    Requires OPENAI_API_KEY in environment.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "openai package not installed. Run: pip install openai"
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Add it to your .env file."
        )

    client = OpenAI(api_key=api_key)

    total = stats["by_category"].get(cat, 0)
    tiers = stats["by_tier_category"].get(cat, {})

    # Top TIER_A questions with explanations for grounding
    tier_a_samples = [
        r for r in cat_results
        if r.get("quality_tier") == "TIER_A" and r.get("exp")
    ][:30]

    sample_questions = [
        {
            "question": r["question"][:200],
            "exp": (r.get("exp") or "")[:300],
            "subject": r.get("subject_name", ""),
        }
        for r in tier_a_samples
    ]

    # Format link context
    cat_links = links.get(cat, {})
    strong_labels = [CATEGORY_LABELS.get(c, c) for c, _ in cat_links.get("strong", [])]
    weak_labels = [CATEGORY_LABELS.get(c, c) for c, _ in cat_links.get("weak", [])]

    prompt = f"""You are building a knowledge base for an agentic consumer healthcare search system.
The system helps everyday consumers (not doctors) find and understand health information.

Category: {label}

Data stats for this category:
- Total records: {total:,}
- TIER_A (reference-cited, textbook quality): {tiers.get('TIER_A', 0):,} ({tiers.get('TIER_A', 0)/total*100:.0f}% of total)
- TIER_B (mechanism-based explanations): {tiers.get('TIER_B', 0):,}
- Strong cross-category co-occurrence: {', '.join(strong_labels) if strong_labels else 'none identified'}
- Weak cross-category co-occurrence: {', '.join(weak_labels) if weak_labels else 'none identified'}

Sample TIER_A questions and their expert explanations from this category:
{json.dumps(sample_questions[:10], indent=2)}

Return a JSON object with EXACTLY these keys. IMPORTANT: Do NOT use double quotes inside string values — use single quotes instead (e.g. use 'heart attack' not "heart attack" inside a string value):
{{
  "subcategories": "comma-separated list of 6-10 specific subcategories",
  "source_priority": ["source 1 (most trusted)", "source 2", "source 3", "source 4", "source 5 (least trusted)"],
  "source_priority_rationale": "1-2 sentences on why these sources are prioritized for this category",
  "terminology_map": [
    {{"consumer_term": "lay term", "medical_term": "medical term", "notes": "why this mapping matters"}},
    ...
  ],
  "query_patterns": [
    "consumer question phrasing -> how the system should handle it",
    ...
  ],
  "rules": [
    "Category-specific rule the retrieval or verification agent must follow",
    ...
  ],
  "pitfalls": [
    "Common mistake or confusion agents must avoid for this category",
    ...
  ],
  "dominant_style": "1-2 sentences describing the dominant explanation style in the TIER_A data above"
}}

Requirements:
- terminology_map: 6-8 entries based on what consumers actually search for
- query_patterns: 4-5 entries, NO double quotes inside the string values
- rules: 4-5 entries, specific and actionable
- pitfalls: 3-4 entries grounded in the sample data
- Return ONLY the JSON object, no extra text before or after"""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()

    # Extract JSON object
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        raw = text[json_start:json_end]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Attempt repair: replace unescaped double quotes inside string values
            # by converting the whole thing with a lenient approach
            import re
            # Remove literal newlines inside string values
            repaired = re.sub(r'(?<!\\)\n', ' ', raw)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                print(f"  WARNING: JSON parse error for {cat}: {e}")
                return {}

    print(f"  WARNING: No JSON found in GPT-4o response for {cat}")
    return {}


def enrich_general_rules_with_claude(
    stats: dict,
    results: list[dict],
) -> str:
    """
    Regenerate general_rules.md content from actual DB data patterns.

    Sends overall quality distribution, per-subject missing explanation rates,
    and tier breakdowns to GPT-4o, which generates updated cross-category rules
    grounded in the real data.

    Returns the full markdown content string for general_rules.md.
    Requires OPENAI_API_KEY in environment.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "openai package not installed. Run: pip install openai"
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Add it to your .env file.")

    client = OpenAI(api_key=api_key)

    total = stats["total"]
    tier_dist = {tier: stats["by_tier"].get(tier, 0) for tier in ["TIER_A", "TIER_B", "TIER_C", "TIER_D"]}

    # Compute per-subject explanation coverage
    subject_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "missing": 0})
    for r in results:
        if r.get("dataset") == "medmcqa":
            subj = r.get("subject_name") or "Unknown"
            subject_stats[subj]["total"] += 1
            if not r.get("has_explanation"):
                subject_stats[subj]["missing"] += 1

    worst_subjects = sorted(
        [
            (subj, d["missing"] / d["total"] * 100, d["total"])
            for subj, d in subject_stats.items()
            if d["total"] >= 100
        ],
        key=lambda x: -x[1],
    )[:8]

    prompt = f"""You are generating the general_rules.md file for an agentic consumer healthcare search system.

This file is loaded for EVERY query by agents A (query understanding) and D (verification).
It defines cross-category trust rules, confidence thresholds, and data quality guidance.

Actual database statistics:
- Total records: {total:,}
- TIER_A (reference-cited, textbook): {tier_dist['TIER_A']:,} ({tier_dist['TIER_A']/total*100:.1f}%)
- TIER_B (mechanism-based): {tier_dist['TIER_B']:,} ({tier_dist['TIER_B']/total*100:.1f}%)
- TIER_C (minimal, answer-only): {tier_dist['TIER_C']:,} ({tier_dist['TIER_C']/total*100:.1f}%)
- TIER_D (null explanation): {tier_dist['TIER_D']:,} ({tier_dist['TIER_D']/total*100:.1f}%)

MedMCQA subjects with highest missing explanation rates (subjects with ≥100 records):
{chr(10).join(f'- {s}: {pct:.0f}% missing ({total:,} records)' for s, pct, total in worst_subjects)}

Generate general_rules.md with these sections:
1. ## Source Quality Rules — how to use TIER_A/B/C/D and PubMedQA; textbook reference hierarchy
2. ## Verification Rules — what needs cross-checking, when to flag uncertainty, drug interaction rules
3. ## Source Trust Hierarchy — numbered ordered list (1=highest)
4. ## Confidence Thresholds — 95%/80%/50%/<50% behavior rules for agent responses
5. ## Data Quality Warnings — grounded in the ACTUAL stats above (not generic advice)

Format the output as markdown starting with:
<!-- STATUS: DRAFT -- awaiting human review -->

# General Rules -- Cross-Category Quality & Verification

Make the data quality warnings specific and numerical — reference the actual percentages above."""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content
