"""Build condition_registry.json from brain category markdown files.

Parses all 20 brain category files to extract:
1. Subcategory names from ### headings (canonical names)
2. Consumer terms from Terminology Map tables (common aliases)

Output: condition_registry.json mapping condition name variants to
(category_id, subcategory_slug) pairs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.personalization.base_graph import CAT_DIR, parse_category_file, slugify


def _extract_terminology_map(filepath: Path) -> list[tuple[str, str]]:
    """Extract consumer terms from the Terminology Map table.

    Returns list of (consumer_term, medical_term) tuples.
    """
    text = filepath.read_text(encoding="utf-8")
    terms = []
    in_terminology = False

    for line in text.split("\n"):
        stripped = line.strip()

        if stripped.startswith("## "):
            if "Terminology Map" in stripped:
                in_terminology = True
            else:
                in_terminology = False
            continue

        if in_terminology and "|" in stripped:
            # Skip header and separator rows
            if "Consumer Term" in stripped or re.match(r"^\|[-\s|]+\|$", stripped):
                continue
            parts = [p.strip() for p in stripped.split("|")]
            # parts[0] is empty (before first |), parts[1] is consumer, parts[2] is medical
            if len(parts) >= 3 and parts[1] and parts[2]:
                consumer = parts[1].strip()
                medical = parts[2].strip()
                terms.append((consumer, medical))

    return terms


def _find_best_subcategory_match(
    term: str,
    subcategories: list[dict],
    category_slug: str,
) -> str | None:
    """Try to match a consumer/medical term to a subcategory slug.

    Uses keyword overlap between the term and subcategory names,
    with stop-word filtering for better precision.
    """
    stop_words = {
        "and", "or", "the", "a", "an", "in", "of", "for", "to", "with",
        "is", "are", "was", "not", "vs", "type",
    }
    term_lower = term.lower()
    term_words = set(re.findall(r"[a-z]+", term_lower)) - stop_words

    best_match = None
    best_score = 0.0

    for sub in subcategories:
        sub_name_lower = sub["name"].lower()
        sub_words = set(re.findall(r"[a-z]+", sub_name_lower)) - stop_words

        # Direct substring match (both directions)
        if term_lower in sub_name_lower or sub_name_lower in term_lower:
            return sub["slug"]

        # Jaccard-like score: overlap / min(len) for better precision
        overlap = len(term_words & sub_words)
        if overlap > 0:
            score = overlap / min(len(term_words), len(sub_words))
            if score > best_score:
                best_score = score
                best_match = sub["slug"]

    return best_match if best_score > 0.3 else None


def build_registry(cat_dir: Path | None = None) -> dict[str, dict]:
    """Build the full condition registry.

    Returns a dict mapping lowercased condition names to:
        {"category": category_slug, "subcategory": subcategory_slug}
    """
    if cat_dir is None:
        cat_dir = CAT_DIR

    registry: dict[str, dict] = {}

    for md_file in sorted(cat_dir.glob("*.md")):
        parsed = parse_category_file(md_file)
        cat_slug = parsed["slug"]

        # Register each subcategory by its canonical name and variants
        for sub in parsed["subcategories"]:
            entry = {"category": cat_slug, "subcategory": sub["slug"]}
            name = sub["name"]

            # Canonical name (lowercased)
            registry[name.lower()] = entry

            # Remove parenthetical content: "Diabetes (Type 1, Type 2, Gestational)" -> "Diabetes"
            simple_name = re.sub(r"\s*\([^)]*\)", "", name).strip()
            if simple_name.lower() != name.lower():
                registry[simple_name.lower()] = entry

            # Remove "& X" suffix: "Hypertension & Blood Pressure" -> "Hypertension"
            amp_match = re.match(r"^(.+?)\s*&\s*.+$", name)
            if amp_match:
                registry[amp_match.group(1).strip().lower()] = entry

            # Expand parenthetical items as individual entries:
            # "Diabetes (Type 1, Type 2, Gestational)" -> "type 1 diabetes", "type 2 diabetes", etc.
            paren_match = re.search(r"\(([^)]+)\)", name)
            if paren_match:
                base = simple_name.lower()
                items = [i.strip().lower() for i in paren_match.group(1).split(",")]
                for item in items:
                    registry[f"{item} {base}"] = entry
                    registry[f"{base} {item}"] = entry

            # Split "/" variants: "Nephrotic / Nephritic Syndrome" -> "nephrotic syndrome", "nephritic syndrome"
            if "/" in name:
                parts = name.split("/")
                if len(parts) == 2:
                    # Find the shared suffix
                    left = parts[0].strip()
                    right = parts[1].strip()
                    # If right part has multiple words, it likely includes a shared suffix
                    right_words = right.split()
                    if len(right_words) >= 2:
                        suffix = " ".join(right_words[1:])
                        registry[f"{left.lower()} {suffix.lower()}"] = entry
                        registry[right.lower()] = entry

        # Register terminology map entries
        terms = _extract_terminology_map(md_file)
        for consumer_term, medical_term in terms:
            # Try medical term first (more specific), then consumer term
            match_slug = _find_best_subcategory_match(
                medical_term, parsed["subcategories"], cat_slug
            )
            if not match_slug:
                match_slug = _find_best_subcategory_match(
                    consumer_term, parsed["subcategories"], cat_slug
                )

            if match_slug:
                entry = {"category": cat_slug, "subcategory": match_slug}
                registry[consumer_term.lower()] = entry
                registry[medical_term.lower()] = entry

    return registry


def main() -> None:
    """Build and write condition_registry.json."""
    registry = build_registry()

    output_path = Path(__file__).parent / "condition_registry.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=True)

    print(f"Wrote {len(registry)} entries to {output_path}")

    # Stats
    categories = set(v["category"] for v in registry.values())
    subcategories = set(v["subcategory"] for v in registry.values())
    print(f"Categories covered: {len(categories)}")
    print(f"Unique subcategories covered: {len(subcategories)}")


if __name__ == "__main__":
    main()
