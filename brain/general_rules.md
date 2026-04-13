<!-- STATUS: DRAFT -- awaiting human review -->

# General Rules -- Cross-Category Quality & Verification

> **Scope:** Loaded by Agent A (query understanding) and Agent D (verification) on every request.
> These rules are authoritative across all subject categories unless overridden by a category-specific rules file.
> Last updated: see repository changelog. Review cycle: quarterly or after any database rebuild.

---

## Source Quality Rules

### Tier Definitions

The knowledge base contains **311,867 total records** distributed across four quality tiers. Every retrieved record carries a `tier` field that agents MUST inspect before constructing a response.

| Tier | Label | Count | Share | Characteristic |
|------|-------|-------|-------|----------------|
| TIER_A | Reference-cited / textbook | 82,852 | 26.6 % | Explanation cites a named reference, textbook chapter, or guideline |
| TIER_B | Mechanism-based | 140,671 | 45.1 % | Explanation present and mechanistically coherent but no formal citation |
| TIER_C | Minimal / answer-only | 39,380 | 12.6 % | Explanation is a single phrase or restatement of the answer |
| TIER_D | Null explanation | 48,964 | 15.7 % | `explanation` field is null, empty, or whitespace-only |

**Combined TIER_C + TIER_D exposure: 28.3 % of the database (88,344 records).** Agents must assume that more than one in four retrieved records carries little or no supporting rationale.

### How to Use Each Tier

**TIER_A — Use with high confidence.**
- Treat the stated explanation as a primary justification.
- Surface the cited reference or textbook name to the user when present.
- May be used as a standalone source for factual claims if no contradicting TIER_A record exists.
- Example citation pattern: *"According to [Harrison's / Robbins / cited guideline]: …"*

**TIER_B — Use with moderate confidence.**
- Mechanistic reasoning is acceptable support for a claim.
- Prefer TIER_B over TIER_C/D but always prefer TIER_A over TIER_B when both are available for the same claim.
- Do not surface TIER_B as an authoritative textbook citation; describe it as consensus-level reasoning.
- If a TIER_B record contradicts a TIER_A record on the same question, defer to TIER_A and flag the discrepancy in the agent trace.

**TIER_C — Use only as a directional signal.**
- The answer choice may be correct, but the explanation cannot be used to justify the claim to the user.
- Agent D MUST seek at least one corroborating TIER_A or TIER_B record before including a TIER_C-sourced fact in any consumer-facing response.
- If corroboration is unavailable, the response must include an explicit uncertainty marker (see Confidence Thresholds).

**TIER_D — Do not use explanation field; treat answer as unverified.**
- The record's answer field may still carry signal (e.g., for majority-vote across records), but the null explanation provides zero justification.
- Agent D MUST flag any claim whose only supporting records are TIER_D.
- Never present a TIER_D explanation to the user. If no better record exists, respond with the uncertainty protocol (< 50 % confidence path).

### PubMedQA Integration

- PubMedQA records are treated as **TIER_A equivalent** when the `final_decision` field is `yes` or `no` (i.e., the abstract provided a directly answerable conclusion).
- PubMedQA records with `final_decision = maybe` are treated as **TIER_B equivalent** — mechanistic context is present but the conclusion is equivocal.
- Long-form PubMedQA contexts (> 200 words) should be summarised by Agent A before passing to Agent D; do not surface raw abstract text to the consumer.

### Textbook Reference Hierarchy

When multiple TIER_A records cite different sources for conflicting claims, resolve priority in this order:

1. **Current national / international clinical guideline** (e.g., WHO, AHA, NICE, CDC) — highest authority; check publication year and prefer most recent.
2. **Major specialty reference textbook** (e.g., Harrison's Principles of Internal Medicine, Robbins & Cotran Pathology, Goodman & Gilman's Pharmacology, Gray's Anatomy, Bailey & Love Surgery).
3. **Board-review or examination-focused textbook** (e.g., First Aid, Kaplan) — acceptable for factual recall but lower authority for mechanism or dosing claims.
4. **Unnamed or partial citation** (e.g., "as per standard texts") — treat as TIER_B regardless of the record's stated tier.

---

## Verification Rules

### General Cross-Checking Requirements

Agent D applies the following checks to every candidate response before it is returned to the user.

**R-1 · Minimum corroboration**
Every factual claim presented to the user must be supported by at least one TIER_A or TIER_B record. Claims supported only by TIER_C or TIER_D records must be withheld or explicitly flagged as unverified.

**R-2 · Contradiction detection**
If retrieved records disagree on the correct answer or mechanism for the same question, Agent D must:
1. Count records by answer option and by tier.
2. Weight TIER_A records more heavily than TIER_B, TIER_B more heavily than TIER_C, and exclude TIER_D from the vote.
3. Report the majority-weighted answer and note the existence of disagreement in the response when the minority position is held by at least one TIER_A record.

**R-3 · Recency sensitivity**
Certain domains change rapidly. For queries touching **drug approvals, dosing guidelines, vaccine schedules, screening recommendations, or diagnostic criteria**, Agent D must append:
> *"This information is based on training data and database records. Please verify against current guidelines, as recommendations may have changed."*

**R-4 · Consumer safety escalation**
If the query involves any of the following, the verification bar is raised to "TIER_A required" (TIER_B is insufficient alone):
- Medication dosing or overdose thresholds
- Contraindications in pregnancy, paediatrics, or renal/hepatic impairment
- Emergency or life-threatening presentations
- Vaccines and immunisation schedules

### When to Flag Uncertainty

Flag uncertainty explicitly (using the confidence markers defined in Confidence Thresholds) when **any** of the following conditions are met:

- The best available record for the claim is TIER_C or TIER_D.
- The subject area has a missing-explanation rate ≥ 15 % (see Data Quality Warnings) **and** the retrieved records for this specific query include TIER_D records.
- Two or more TIER_A records disagree.
- The query asks for a specific numeric value (dose, duration, sensitivity/specificity figure) and no TIER_A record provides that exact value.
- The query falls in a category flagged in Data Quality Warnings as high-risk (Dental, Medicine, Pharmacology, Surgery).

### Drug Interaction Rules

These rules apply whenever a query contains or implies ≥ 2 pharmacological agents, or asks about a drug's contraindications, side-effect profile, or dosing adjustment.

**DI-1 · Dual-source requirement**
Drug interaction claims require corroboration from at least **two independent records**, each TIER_A or TIER_B. A single record is insufficient regardless of tier.

**DI-2 · Pharmacology subject warning**
The Pharmacology subject has an **18 % missing-explanation rate** across 13,722 records (see Data Quality Warnings). Agent D must check the tier of every pharmacology record used to support a drug interaction claim. If any supporting record is TIER_D, discard it and rerun retrieval.

**DI-3 · Severity labelling**
When a drug interaction or contraindication is identified, the response must label severity:
- **Contraindicated** — do not co-administer under any circumstances per cited source.
- **Caution / monitoring required** — use with clinical supervision; cite the parameter to monitor.
- **Theoretical / mechanistic concern** — no direct evidence of clinical harm; flag as speculative if sourced only from TIER_B.

**DI-4 · Always-escalate list**
The following drug classes require an automatic "consult a pharmacist or prescriber" disclaimer regardless