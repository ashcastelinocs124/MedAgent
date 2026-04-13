"""Parse brain category markdown files into a NetworkX DiGraph.

The base graph is read-only and shared across all users.
It contains ~20 category nodes, ~175 subcategory nodes, and ~700+ edges
parsed from the brain/categories/*.md files.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import networkx as nx

BRAIN_DIR = Path(__file__).parent.parent.parent / "brain"
CAT_DIR = BRAIN_DIR / "categories"

# Ceiling weights — a link at max co-occurrence count reaches these values
STRONG_LINK_MAX = 0.85
WEAK_LINK_MAX = 0.35
RELATED_LINK_WEIGHT = 0.60
PARENT_CHILD_WEIGHT = 1.0  # category <-> subcategory

# Minimum weight floor regardless of count (so even 1 cross-hit isn't zero)
_LINK_MIN_WEIGHT = 0.10

# Reference count treated as "maximum" for log normalization.
# Links with this many co-occurrences reach the ceiling weight.
_LOG_REF_COUNT = 100


def _count_to_weight(count: int, max_weight: float) -> float:
    """Scale a co-occurrence count to an edge weight using log normalization.

    1 cross-hit  → near _LINK_MIN_WEIGHT (~0.10)
    _LOG_REF_COUNT cross-hits → max_weight (ceiling)
    Monotonically increasing; never exceeds max_weight.
    """
    if count <= 0:
        return _LINK_MIN_WEIGHT
    t = math.log10(count + 1) / math.log10(_LOG_REF_COUNT + 1)
    return _LINK_MIN_WEIGHT + t * (max_weight - _LINK_MIN_WEIGHT)


@dataclass
class NodeData:
    """Metadata stored on each graph node."""

    node_type: str  # "category" or "subcategory"
    category_id: str  # slug of parent category (same as node id for categories)
    display_name: str
    subcategories: list[str] = field(default_factory=list)  # only for category nodes


@dataclass
class EdgeData:
    """Metadata stored on each graph edge."""

    edge_type: str  # "strong", "weak", "related", "parent_child"
    base_weight: float
    reason: str = ""


def slugify(name: str) -> str:
    """Convert a display name to a node-ID slug.

    Examples:
        "Heart & Blood Vessels" -> "heart_blood_vessels"
        "Hypertension & Blood Pressure" -> "hypertension_blood_pressure"
        "Diabetes (Type 1, Type 2, Gestational)" -> "diabetes_type_1_type_2_gestational"
        "Nephrotic / Nephritic Syndrome" -> "nephrotic_nephritic_syndrome"
    """
    s = name.lower()
    s = s.replace("&", "and")
    s = s.replace("/", " ")
    s = re.sub(r"[(),]", " ", s)
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    # Remove 'and_' that came from '&' replacement
    s = s.replace("_and_", "_")
    # Clean up double underscores
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _filename_to_slug(filename: str) -> str:
    """Convert a markdown filename to a category slug.

    Example: "heart_blood_vessels.md" -> "heart_blood_vessels"
    """
    return filename.replace(".md", "")


def _extract_link_target(line: str) -> Optional[tuple[str, str]]:
    """Extract (target_slug, reason) from a markdown link line.

    Handles lines like:
        - [Heart & Blood Vessels](heart_blood_vessels.md) -- reason text
        - [Heart & Blood Vessels](heart_blood_vessels.md) (reason text)
    """
    match = re.search(r"\[([^\]]+)\]\(([^)]+\.md)\)", line)
    if not match:
        return None
    filename = match.group(2)
    target_slug = _filename_to_slug(filename)

    # Extract reason after " -- " or after the link in parentheses
    reason = ""
    rest = line[match.end():]
    dash_match = re.search(r"\s*--\s*(.+)", rest)
    paren_match = re.search(r"\s*\(([^)]+)\)", rest)
    if dash_match:
        reason = dash_match.group(1).strip()
    elif paren_match:
        reason = paren_match.group(1).strip()

    return target_slug, reason


def parse_category_file(filepath: Path) -> dict:
    """Parse a single brain category markdown file.

    Returns a dict with:
        - name: str (display name from # heading)
        - slug: str (category slug from filename)
        - subcategories: list[dict] with name, slug, related links
        - strong_links: list[(target_slug, reason)]
        - weak_links: list[(target_slug, reason)]
    """
    text = filepath.read_text(encoding="utf-8")
    slug = filepath.stem
    lines = text.split("\n")

    result = {
        "name": "",
        "slug": slug,
        "subcategories": [],
        "strong_links": [],   # list of (target_slug, reason, cross_hit_count)
        "weak_links": [],     # list of (target_slug, reason, cross_hit_count)
    }

    # Extract category name from first # heading
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            result["name"] = line[2:].strip()
            break

    # Parse sections
    current_section = ""
    current_link_type = ""
    current_subcategory = None
    in_subcategory_details = False

    for line in lines:
        stripped = line.strip()

        # Track ## sections
        if stripped.startswith("## "):
            section_name = stripped[3:].strip()
            current_section = section_name
            if section_name == "Subcategory Details":
                in_subcategory_details = True
            else:
                in_subcategory_details = False
            current_subcategory = None
            continue

        # Parse Links section
        if current_section == "Links":
            if "**Strong links:**" in stripped:
                current_link_type = "strong"
                continue
            elif "**Weak links:**" in stripped:
                current_link_type = "weak"
                continue

            if stripped.startswith("- ") or stripped.startswith("  - "):
                link_data = _extract_link_target(stripped)
                if link_data:
                    target_slug, reason = link_data
                    # Parse cross-hit count from reason, e.g. "51 cross-hits"
                    count_match = re.search(r"(\d+)\s+cross-hits?", reason)
                    cross_hits = int(count_match.group(1)) if count_match else 1
                    entry = (target_slug, reason, cross_hits)
                    if current_link_type == "strong":
                        result["strong_links"].append(entry)
                    elif current_link_type == "weak":
                        result["weak_links"].append(entry)

        # Parse Subcategory Details section
        if in_subcategory_details:
            if stripped.startswith("### "):
                subcat_name = stripped[4:].strip()
                current_subcategory = {
                    "name": subcat_name,
                    "slug": slugify(subcat_name),
                    "related": [],
                }
                result["subcategories"].append(current_subcategory)
                continue

            if current_subcategory and stripped.startswith("- **Related:**"):
                # Extract all markdown links from the Related line
                related_text = stripped[len("- **Related:**"):]
                for match in re.finditer(
                    r"\[([^\]]+)\]\(([^)]+\.md)\)\s*\(([^)]+)\)", related_text
                ):
                    target_slug = _filename_to_slug(match.group(2))
                    reason = match.group(3).strip()
                    current_subcategory["related"].append((target_slug, reason))

    return result


def build_base_graph(cat_dir: Optional[Path] = None) -> nx.DiGraph:
    """Build the base knowledge graph from all brain category files.

    Returns a NetworkX DiGraph with:
        - Category nodes: "cat:<slug>"
        - Subcategory nodes: "sub:<category_slug>:<subcategory_slug>"
        - Edges with base_weight and edge_type metadata
    """
    if cat_dir is None:
        cat_dir = CAT_DIR

    G = nx.DiGraph()
    md_files = sorted(cat_dir.glob("*.md"))

    parsed_categories = {}
    for f in md_files:
        parsed = parse_category_file(f)
        parsed_categories[parsed["slug"]] = parsed

    # First pass: add all category and subcategory nodes
    for slug, data in parsed_categories.items():
        cat_node = f"cat:{slug}"
        subcat_slugs = [s["slug"] for s in data["subcategories"]]

        G.add_node(
            cat_node,
            data=NodeData(
                node_type="category",
                category_id=slug,
                display_name=data["name"],
                subcategories=subcat_slugs,
            ),
        )

        for subcat in data["subcategories"]:
            sub_node = f"sub:{slug}:{subcat['slug']}"
            G.add_node(
                sub_node,
                data=NodeData(
                    node_type="subcategory",
                    category_id=slug,
                    display_name=subcat["name"],
                ),
            )

            # Bidirectional parent-child edges
            G.add_edge(
                cat_node,
                sub_node,
                data=EdgeData(
                    edge_type="parent_child",
                    base_weight=PARENT_CHILD_WEIGHT,
                    reason="parent category",
                ),
            )
            G.add_edge(
                sub_node,
                cat_node,
                data=EdgeData(
                    edge_type="parent_child",
                    base_weight=PARENT_CHILD_WEIGHT,
                    reason="parent category",
                ),
            )

    # Second pass: add category-level strong/weak links
    for slug, data in parsed_categories.items():
        cat_node = f"cat:{slug}"

        for target_slug, reason, cross_hits in data["strong_links"]:
            target_node = f"cat:{target_slug}"
            if target_node in G:
                G.add_edge(
                    cat_node,
                    target_node,
                    data=EdgeData(
                        edge_type="strong",
                        base_weight=_count_to_weight(cross_hits, STRONG_LINK_MAX),
                        reason=reason,
                    ),
                )

        for target_slug, reason, cross_hits in data["weak_links"]:
            target_node = f"cat:{target_slug}"
            if target_node in G:
                G.add_edge(
                    cat_node,
                    target_node,
                    data=EdgeData(
                        edge_type="weak",
                        base_weight=_count_to_weight(cross_hits, WEAK_LINK_MAX),
                        reason=reason,
                    ),
                )

    # Third pass: add subcategory Related links (cross-category)
    for slug, data in parsed_categories.items():
        for subcat in data["subcategories"]:
            sub_node = f"sub:{slug}:{subcat['slug']}"

            for target_cat_slug, reason in subcat["related"]:
                target_cat_node = f"cat:{target_cat_slug}"
                if target_cat_node in G:
                    # Subcategory -> target category
                    G.add_edge(
                        sub_node,
                        target_cat_node,
                        data=EdgeData(
                            edge_type="related",
                            base_weight=RELATED_LINK_WEIGHT,
                            reason=reason,
                        ),
                    )

    return G


def get_category_nodes(G: nx.DiGraph) -> list[str]:
    """Return all category node IDs."""
    return [n for n in G.nodes if n.startswith("cat:")]


def get_subcategory_nodes(G: nx.DiGraph) -> list[str]:
    """Return all subcategory node IDs."""
    return [n for n in G.nodes if n.startswith("sub:")]


def get_subcategories_for_category(G: nx.DiGraph, category_id: str) -> list[str]:
    """Return subcategory node IDs belonging to a category."""
    prefix = f"sub:{category_id}:"
    return [n for n in G.nodes if n.startswith(prefix)]
