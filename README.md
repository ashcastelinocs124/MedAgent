# MedAgent: Agentic Healthcare Search System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)

> A multi-agent framework for consumer health query processing that combines hybrid search (semantic, lexical, and knowledge-graph retrieval) with personalization based on user health literacy, conditions, and demographics.

**Authors:** [Ash Castelino](https://github.com/ashcastelinocs124), [Keshav Trikha](https://github.com/ktrikha2), [Blazej Madrzyk](https://github.com/madrzyk2)

---

## Problem

Healthcare information is fragmented, jargon-heavy, and not personalized. Consumers get the same results regardless of whether they're a nurse, a patient with diabetes, or a caregiver for an elderly parent. **88% of U.S. adults have less-than-proficient health literacy.**

## Solution

An agentic system that:
1. **Understands** the user's query intent and health context
2. **Routes** to multiple retrieval strategies (hybrid search) guided by a structured knowledge base ("the brain")
3. **Synthesizes** results personalized to the user's literacy level and background
4. **Cites** authoritative sources, flags uncertainty, and applies confidence-based disclaimers

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Agent A — Query Understanding                   │
│  Keyword match → Embedding cosine → LLM fallback │
│  Outputs: category, normalized terms             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Agent B — Retrieval Planning                    │
│  UserSubgraph → QueryGraphMerger → Brain context │
│  Outputs: retrieval plan, source priorities      │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Agent C — Evidence Synthesis                    │
│  HybridSearcher (semantic + lexical + RRF)       │
│  → Claude personalized synthesis                 │
│  Outputs: answer text, citations                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Agent D — Verification                          │
│  Confidence scoring, tiered disclaimers,         │
│  uncertainty flags, citation deduplication       │
│  Outputs: final answer, confidence, disclaimer   │
└─────────────────────────────────────────────────┘
```

### Four Agents

| Agent | Role | Key Technique |
|-------|------|---------------|
| **A** — Query Understanding | Classifies queries into 20 health categories, normalizes medical terminology | Keyword → centroid embedding (cosine 0.65) → LLM fallback cascade |
| **B** — Retrieval Planning | Builds personalized retrieval plan from user profile and brain knowledge graph | UserSubgraph + QueryGraphMerger with adaptive weight boosting |
| **C** — Evidence Synthesis | Runs hybrid search, synthesizes personalized answer | pgvector semantic + Postgres FTS fused via Reciprocal Rank Fusion (k=60) |
| **D** — Verification | Scores confidence, applies disclaimers, flags uncertainty | Weighted confidence = Σ(tier_weight × relevance)/5 + source_bonus |

### Hybrid Search

- **Semantic**: OpenAI `text-embedding-3-small` (1536-dim) via pgvector cosine similarity
- **Lexical**: Postgres full-text search (`tsvector`/`ts_rank`) with GIN indexes
- **Fusion**: Reciprocal Rank Fusion (RRF, k=60) — parameter-free, robust to score-scale differences
- **Graph reranking**: Retrieval plan weights boost results from relevant brain categories

### The Brain — Knowledge Base

Graph-linked flat files — markdown category files with explicit link metadata connecting related categories. This structure seeds the context graph used for retrieval planning.

```
brain/
├── general_rules.md       ← Cross-category rules (loaded for every query)
├── directory.md            ← Master index with category links
├── categories/             ← 20 health category files
│   ├── heart_cardiovascular.md
│   ├── mental_health.md
│   ├── cancer_oncology.md
│   └── ... (17 more)
└── review/                 ← Flagged items for human review
```

**20 Consumer-Facing Categories**: Heart & Cardiovascular, Mental Health, Cancer & Oncology, Women's Health, Children's Health, Infections & Immunity, Bones/Joints/Movement, Eyes/Ears/Nose/Throat, Skin & Dermatology, Medications & Drug Safety, Diagnostic Testing & Imaging, Nutrition & Metabolism, Preventive & Public Health, Emergency & Trauma, Nervous System & Brain, and 5 more.

### Personalization

- **User profile**: age, sex, conditions, medications, health literacy level
- **Health literacy adaptation**: reading level adjusted from 6th-grade (LOW) to clinical terminology (HIGH)
- **Condition-aware filtering**: surfaces relevant info for user's known conditions
- **LLM-augmented onboarding**: GPT-4o reviews profile weights and can ask clarifying questions
- **Self-learning**: per-user memory tracks recurring health topics, graduates frequent patterns to permanent weight boosts

### Confidence Scoring

| Confidence | Behavior |
|-----------|----------|
| ≥ 95% | Direct answer |
| ≥ 80% | Answer + suggest provider review |
| ≥ 50% | Answer + strong disclaimer |
| < 50% | No recommendation, refer to provider |

---

## Project Structure

```
├── src/
│   ├── agents/              ← Four pipeline agents (A, B, C, D)
│   ├── search/hybrid.py     ← HybridSearcher (semantic + lexical + RRF)
│   ├── personalization/     ← User profiling, graph building, adaptive learning
│   ├── evaluation/          ← Post-eval failure pattern analysis
│   ├── data/                ← Ingestion, embedding, categorization pipelines
│   ├── pipeline.py          ← Pipeline orchestrator (A → B → C → D)
│   └── app.py               ← FastAPI demo web UI
├── brain/                   ← Knowledge base (20 category markdown files)
├── simple_evals/            ← HealthBench evaluation framework
├── tests/                   ← 20+ test files (pytest)
├── run_healthbench.py       ← HealthBench evaluation runner
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL with [pgvector](https://github.com/pgvector/pgvector) extension
- OpenAI API key (for embeddings and synthesis)
- Anthropic API key (optional, for Claude-based classification)

### Installation

```bash
git clone https://github.com/ashcastelinocs124/MedAgent.git
cd MedAgent
pip install -r requirements.txt
pip install pgvector
```

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:PASSWORD@your-host:5432/postgres?sslmode=require
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...   # optional
HF_TOKEN=hf_...                # optional, for HuggingFace datasets
```

### Database Setup

```bash
# Verify connection and table structure
python src/data/setup_db.py

# Ingest MedMCQA data
python src/data/ingest.py --source medmcqa --limit 10000

# Ingest PubMedQA data
python src/data/ingest.py --source pubmedqa

# Generate embeddings
python src/data/embed.py --source medmcqa --limit 10000

# Rebuild brain knowledge base (free, fast)
python src/data/ingest.py --source medmcqa --limit 1 --rebuild-brain
```

### Running the Demo

```bash
uvicorn src.app:app --reload
```

Open http://localhost:8000

**Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/onboarding` | GET | 4-screen profile intake wizard |
| `/` | GET | Search page with agent step visualization |
| `/query` | POST | JSON API: `{query, session_id?}` → `{answer_text, confidence, disclaimer, citations}` |
| `/profile/review` | POST | LLM-augmented profile weight review |

---

## Evaluation

### HealthBench (Primary Benchmark)

[HealthBench](https://github.com/openai/simple-evals): 5,000 physician-authored rubrics graded by GPT-4o.

```bash
# Quick smoke test
python run_healthbench.py --pipeline --examples 3

# Standard evaluation
python run_healthbench.py --pipeline --examples 50

# With automatic failure pattern analysis
python run_healthbench.py --pipeline --examples 50 --analyze-failures
```

**Results (n=200):**

| Metric | Score |
|--------|-------|
| **Overall** | **0.468** |
| Accuracy | 0.580 |
| Communication Quality | 0.734 |
| Instruction Following | 0.540 |
| Context Awareness | 0.392 |
| Completeness | 0.344 |

| Theme | Score |
|-------|-------|
| Communication | 0.602 |
| Emergency & Referrals | 0.597 |
| Hedging | 0.520 |
| Health Data Tasks | 0.477 |
| Complex Responses | 0.351 |
| Global Health | 0.342 |
| Context Seeking | 0.323 |

The `PatternAnalyzer` tags failed rubric items using GPT-4o, tracks recurring failure patterns, and graduates patterns at 5+ occurrences for systematic improvement.

---

## Datasets

| Dataset | Records | Purpose |
|---------|---------|---------|
| [MedMCQA](https://huggingface.co/datasets/openlifescienceai/medmcqa) | 194k+ | Medical MCQs — categorization and brain building |
| [PubMedQA](https://huggingface.co/datasets/qiaojin/PubMedQA) | 1,000 | Biomedical research QA — citation retrieval |
| [MedQuAD](https://github.com/abachaa/MedQuAD) | 16,000 | NIH consumer health QA — question patterns |

All stored in PostgreSQL with pgvector for embeddings.

## Tests

```bash
pytest tests/ -v
```

20+ test files covering all agents, search, personalization, evaluation, and end-to-end integration.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Core language | Python 3.11+ |
| LLM (synthesis) | Claude Sonnet |
| LLM (classification) | Claude Sonnet (fallback) |
| Embeddings | OpenAI text-embedding-3-small (1536-dim) |
| Database | PostgreSQL + pgvector |
| Web framework | FastAPI |
| Knowledge graph | NetworkX |
| Testing | pytest + pytest-asyncio |

## Constraints

- **Medical accuracy**: Never fabricates health information. Always cites sources. Flags uncertainty.
- **No diagnostic claims**: Provides information, not diagnoses.
- **Data privacy**: User profiles are never logged with identifiable information.
- **Reproducibility**: All experiments reproducible with documented seeds and configs.

## License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Ashleyn Castelino, Keshav Trikha, Blazej Madrzyk
