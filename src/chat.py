"""Simple CLI chat agent that uses the brain knowledge graph.

Onboards the user, builds a personalized subgraph, and answers health
questions by loading relevant brain category files as context for GPT-4o.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from openai import OpenAI

from src.personalization.adaptive import AdaptiveLearner
from src.personalization.base_graph import build_base_graph, get_category_nodes
from src.personalization.models import (
    Condition,
    HealthLiteracy,
    Medication,
    Sex,
    UserProfile,
)
from src.personalization.query_merge import QueryGraphMerger
from src.personalization.user_graph import UserSubgraphBuilder

BRAIN_DIR = Path(__file__).parent.parent / "brain"
CAT_DIR = BRAIN_DIR / "categories"
REGISTRY_PATH = Path(__file__).parent / "personalization" / "condition_registry.json"

MODEL = "gpt-4o"


# ── Condition registry ──────────────────────────────────────────────────────


def load_condition_registry() -> dict:
    """Load the condition registry mapping consumer terms to graph nodes."""
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def match_condition(name: str, registry: dict) -> Condition | None:
    """Match a user-entered condition name against the registry."""
    key = name.strip().lower()
    if key in registry:
        entry = registry[key]
        return Condition(
            name=name.strip(),
            category_id=entry["category"],
            subcategory_id=entry["subcategory"],
        )
    # Try partial matching
    for reg_name, entry in registry.items():
        if key in reg_name or reg_name in key:
            return Condition(
                name=name.strip(),
                category_id=entry["category"],
                subcategory_id=entry["subcategory"],
            )
    return None


# ── Onboarding ──────────────────────────────────────────────────────────────


def onboard_user(registry: dict) -> UserProfile:
    """Interactively collect user profile information."""
    print("\n=== Health Profile Setup ===\n")

    # Age
    while True:
        age_input = input("Age: ").strip()
        if age_input.isdigit() and 0 < int(age_input) < 150:
            age = int(age_input)
            break
        print("Please enter a valid age.")

    # Sex
    sex_map = {"male": Sex.MALE, "female": Sex.FEMALE, "other": Sex.OTHER}
    while True:
        sex_input = input("Sex (male/female/other): ").strip().lower()
        if sex_input in sex_map:
            sex = sex_map[sex_input]
            break
        print("Please enter male, female, or other.")

    # Conditions
    conditions = []
    cond_input = input("Health conditions (comma-separated, or 'none'): ").strip()
    if cond_input.lower() != "none" and cond_input:
        for name in cond_input.split(","):
            name = name.strip()
            if not name:
                continue
            matched = match_condition(name, registry)
            if matched:
                conditions.append(matched)
                print(f"  Matched: {name} -> {matched.category_id}/{matched.subcategory_id}")
            else:
                print(f"  Could not match: {name} (skipping)")

    # Medications
    medications = []
    med_input = input("Medications (comma-separated, or 'none'): ").strip()
    if med_input.lower() != "none" and med_input:
        for name in med_input.split(","):
            name = name.strip()
            if not name:
                continue
            # Link medication to the first condition's category if available
            cat_id = conditions[0].category_id if conditions else "medications_drug_safety"
            medications.append(Medication(name=name, category_id=cat_id))
            print(f"  Added: {name} (linked to {cat_id})")

    # Health literacy
    lit_map = {
        "basic": HealthLiteracy.LOW,
        "intermediate": HealthLiteracy.MEDIUM,
        "advanced": HealthLiteracy.HIGH,
    }
    while True:
        lit_input = input("Health literacy (basic/intermediate/advanced): ").strip().lower()
        if lit_input in lit_map:
            literacy = lit_map[lit_input]
            break
        print("Please enter basic, intermediate, or advanced.")

    profile = UserProfile(
        age=age,
        sex=sex,
        conditions=conditions,
        medications=medications,
        health_literacy=literacy,
    )
    print(f"\nProfile created: {age}yo {sex.value}, "
          f"{len(conditions)} condition(s), {len(medications)} medication(s), "
          f"literacy={literacy.value}")
    return profile


# ── Query classification ────────────────────────────────────────────────────


def get_category_display_names(base_graph) -> dict[str, str]:
    """Build a mapping of category slug -> display name from the graph."""
    names = {}
    for node_id in get_category_nodes(base_graph):
        slug = node_id.replace("cat:", "")
        display_name = base_graph.nodes[node_id]["data"].display_name
        names[slug] = display_name
    return names


def classify_query(client: OpenAI, question: str, category_names: dict[str, str]) -> str:
    """Classify a user question into one of the brain categories using GPT-4o."""
    categories_list = "\n".join(
        f"- {slug}: {display}" for slug, display in sorted(category_names.items())
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a medical query classifier. Given a health question, "
                    "respond with ONLY the category slug that best matches. "
                    "No explanation, just the slug."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Classify this health question into one of these categories:\n\n"
                    f"{categories_list}\n\n"
                    f"Question: {question}\n\n"
                    f"Reply with only the category slug."
                ),
            },
        ],
        temperature=0,
        max_tokens=50,
    )
    slug = response.choices[0].message.content.strip().lower()
    # Clean up in case the model returns extra formatting
    slug = slug.strip("`\"' ")
    if slug in category_names:
        return slug
    # Fallback: try to find a partial match
    for cat_slug in category_names:
        if cat_slug in slug or slug in cat_slug:
            return cat_slug
    # Default to first category if classification fails
    return list(category_names.keys())[0]


# ── Brain context loading ───────────────────────────────────────────────────


def load_brain_context(plan) -> str:
    """Load general rules + relevant category files based on the retrieval plan."""
    parts = []

    # Always load general rules
    general_path = BRAIN_DIR / "general_rules.md"
    if general_path.exists():
        parts.append(f"=== GENERAL RULES ===\n{general_path.read_text(encoding='utf-8')}")

    # Load primary category
    primary_path = CAT_DIR / f"{plan.primary_category}.md"
    if primary_path.exists():
        parts.append(
            f"=== PRIMARY: {plan.primary_category} ===\n"
            f"{primary_path.read_text(encoding='utf-8')}"
        )

    # Load must_load categories
    for cat_id in plan.must_load:
        cat_path = CAT_DIR / f"{cat_id}.md"
        if cat_path.exists():
            parts.append(
                f"=== RELATED: {cat_id} ===\n"
                f"{cat_path.read_text(encoding='utf-8')}"
            )

    return "\n\n".join(parts)


def build_system_prompt(brain_context: str, profile: UserProfile, plan) -> str:
    """Build the full system prompt with brain context and user profile."""
    literacy_instructions = {
        HealthLiteracy.LOW: (
            "Use plain, simple language (grade 5-6 reading level). "
            "No medical jargon. Short sentences. Explain any medical terms."
        ),
        HealthLiteracy.MEDIUM: (
            "Use accessible language (grade 8-10 reading level). "
            "You may use some medical terms but define them."
        ),
        HealthLiteracy.HIGH: (
            "You may use full medical terminology. "
            "The user has a clinical or advanced background."
        ),
    }

    conditions_str = ", ".join(c.name for c in profile.conditions) or "none reported"
    medications_str = ", ".join(m.name for m in profile.medications) or "none reported"

    return (
        "You are a health information assistant. You provide accurate, personalized "
        "health information based on the medical knowledge provided below. "
        "You are NOT a doctor and do not diagnose conditions.\n\n"
        "IMPORTANT RULES:\n"
        "- Only use information from the knowledge base provided below\n"
        "- Never fabricate medical facts\n"
        "- If you're unsure, say so and recommend consulting a healthcare provider\n"
        "- For emergencies, always advise calling 911\n"
        "- Frame suggestions as information, never as diagnosis\n\n"
        f"USER PROFILE:\n"
        f"- Age: {profile.age}\n"
        f"- Sex: {profile.sex.value}\n"
        f"- Conditions: {conditions_str}\n"
        f"- Medications: {medications_str}\n"
        f"- Health Literacy: {profile.health_literacy.value}\n\n"
        f"LANGUAGE STYLE: {literacy_instructions[profile.health_literacy]}\n\n"
        f"RETRIEVAL CONTEXT (categories loaded for this query):\n"
        f"{chr(10).join('- ' + e for e in plan.explanation)}\n\n"
        f"--- MEDICAL KNOWLEDGE BASE ---\n\n"
        f"{brain_context}"
    )


# ── Chat loop ───────────────────────────────────────────────────────────────


def chat_loop(
    client: OpenAI,
    profile: UserProfile,
    base_graph,
    user_subgraph,
    merger: QueryGraphMerger,
    learner: AdaptiveLearner,
) -> None:
    """Main chat loop with multi-turn conversation history."""
    category_names = get_category_display_names(base_graph)
    messages: list[dict] = []

    print("\n=== HealthSearch Chat ===")
    print("Ask any health question. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # 1. Classify the query
        category = classify_query(client, question, category_names)
        print(f"  [Category: {category_names.get(category, category)}]")

        # 2. Plan retrieval with personalized weights
        plan = merger.plan_retrieval(category, user_subgraph)

        # 3. Load relevant brain files
        brain_context = load_brain_context(plan)

        # 4. Build system prompt
        system_prompt = build_system_prompt(brain_context, profile, plan)

        # 5. Add user message to history
        messages.append({"role": "user", "content": question})

        # 6. Call GPT-4o with streaming
        print("\nAgent: ", end="", flush=True)
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.3,
            stream=True,
        )

        assistant_response = []
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                assistant_response.append(delta.content)

        full_response = "".join(assistant_response)
        print("\n")

        # 7. Add assistant response to history
        messages.append({"role": "assistant", "content": full_response})

        # 8. Record query for adaptive learning
        touched = [f"cat:{category}"]
        touched.extend(f"cat:{c}" for c in plan.must_load)
        learner.record_query(user_subgraph, touched)


# ── Entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the chat agent."""
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("  export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    client = OpenAI()

    print("Loading knowledge graph...")
    base_graph = build_base_graph()
    print(f"  {base_graph.number_of_nodes()} nodes, {base_graph.number_of_edges()} edges")

    # Load condition registry
    registry = load_condition_registry()
    print(f"  {len(registry)} conditions in registry")

    # Onboard user
    profile = onboard_user(registry)

    # Build personalized subgraph
    print("\nBuilding personalized graph...")
    builder = UserSubgraphBuilder(base_graph)
    user_subgraph = builder.build(profile)
    print(f"  {len(user_subgraph.edge_boosts)} personalized edge boosts")
    print(f"  {len(user_subgraph.anchored_categories)} anchored categories")

    # Initialize query merger and adaptive learner
    merger = QueryGraphMerger(base_graph)
    learner = AdaptiveLearner(builder)

    # Enter chat loop
    chat_loop(client, profile, base_graph, user_subgraph, merger, learner)


if __name__ == "__main__":
    main()
