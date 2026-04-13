<!-- STATUS: DRAFT -- awaiting human review -->

# Skin & Dermatology

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 10,208 | MedMCQA: 2,923 | PubMedQA: 10 | MedQuAD: 261
- **Missing explanations**: 158 (1.5%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 1,857 | 18% |
| TIER_B | 4,554 | 45% |
| TIER_C | 1,958 | 19% |
| TIER_D | 1,839 | 18% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Skin | 1,765 |
| Surgery | 332 |
| Pathology | 204 |
| Forensic Medicine | 184 |
| Medicine | 146 |
| Microbiology | 85 |
| Anatomy | 63 |
| Pharmacology | 41 |
| Unknown | 41 |
| Physiology | 18 |

## Sample Questions

- [healthcaremagic_records] [TIER_A] Hi!Few days ago I noticed red rings on my skin (chest and belly area). Not itchy, slightly swollen, inner part skin-coloured, ring cca 1mm in thicknes...
- [healthcaremagic_records] [TIER_A] I have oozing from foreskin, redness of forskin just below the head and redness of the head. I have washed it everyday for two weeks and put neosporin...
- [healthcaremagic_records] [TIER_B] i have beensuffering from shingles on my scalp for 3 months started eish rash blisters itcthing now a full line on my left side of scalp been given an...
- [healthcaremagic_records] [TIER_B] Hi, Im 29 yrs old and married for 6 yrs and not yet conceived at all. Had been in treatment from the 8th month of my marriage and took breaks too. GG,...
- [healthcaremagic_records] [TIER_C] i have had upper dentures for 3 years now. For most of this time I have noticed what appear to be skin tags on the outer gum. These become quite painf...

## Links
<!-- Derived from secondary_category co-occurrence in 10,208 DB records -->
- **Strong links:**
  - [Emergency & Critical Care](emergency_critical_care.md) — 452 cross-hits
  - [Infections & Infectious Disease](infections.md) — 308 cross-hits
  - [Medications & Drug Safety](medications_drug_safety.md) — 300 cross-hits
- **Weak links:**
  - [Cancer](cancer.md) — 256 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 234 cross-hits
  - [Dental & Oral Health](dental_oral.md) — 226 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Rashes & Skin Reactions, Acne & Pimples, Fungal & Bacterial Skin Infections, Wound Care & Skin Lesions, Eczema & Dermatitis, Psoriasis & Chronic Skin Conditions, Skin Growths & Lumps, Pediatric Skin Conditions
- **Confidence:** High

## Source Priority
1. American Academy of Dermatology (AAD) – aad.org
2. National Institutes of Health MedlinePlus – medlineplus.gov
3. Mayo Clinic Dermatology – mayoclinic.org
4. Cleveland Clinic Skin Health – my.clevelandclinic.org
5. WebMD Skin & Beauty – webmd.com
**Rationale:** The AAD provides board-certified dermatologist-reviewed content that is authoritative for diagnosis patterns, treatment guidelines, and condition classification. Government and major academic medical center sources offer evidence-based explanations free from commercial bias, which is critical when consumers are distinguishing between look-alike conditions.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| ring-shaped rash | annular lesion / tinea corporis / erythema migrans | Ring rashes have multiple causes including ringworm, Lyme disease, and eczema — the distinction is safety-critical and must trigger a differential explanation |
| skin rash | dermatitis / exanthem / urticaria | Extremely broad consumer term; system must probe location, appearance, and timeline to narrow subcategory |
| pimples | acne vulgaris / folliculitis / milia | Consumers conflate acne with folliculitis and other papular eruptions, especially in infants where neonatal acne is common |
| itchy skin | pruritus | Pruritus is a symptom, not a diagnosis; cross-category flags needed for systemic causes like liver disease or allergic drug reactions |
| fungal infection / jock itch / ringworm | tinea cruris / tinea corporis / dermatophytosis | Consumers use 'ringworm' for any ring-shaped rash and 'jock itch' for any groin rash; correct mapping prevents misidentification |
| lump under skin | lipoma / cyst / lymphadenopathy / abscess | Lumps near lymph node regions (groin, armpit, neck) require cross-category flagging toward Infections and potentially Cancer |
| cold sore / mouth blister | herpes labialis / aphthous ulcer / stomatitis | Consumers often confuse cold sores (viral, HSV-1) with canker sores (non-infectious); treatment pathways differ significantly |
| oozing / weeping skin | exudate / serous discharge / purulent discharge | Oozing signals possible infection or severe eczema; color and consistency of discharge are key triage signals |

## Common Query Patterns
- Consumer describes shape/color/location of a skin mark -> system should present a ranked differential list with distinguishing features and a clear recommendation to see a dermatologist if the mark is changing or persistent
- Consumer asks if a rash or skin issue is contagious -> system should identify likely condition, explain transmission risk clearly, and cross-reference Infections & Infectious Disease category if relevant
- Consumer says a prescribed cream or antibiotic is not working -> system should explain why first-line treatments sometimes fail (e.g., fungal vs. bacterial misdiagnosis), suggest the consumer report back to their doctor, and flag medication safety concerns via cross-reference to Medications & Drug Safety
- Consumer asks about a skin condition on a baby or young child -> system should flag pediatric-specific differentials (neonatal acne, eczema, heat rash), reassure when appropriate, and always recommend pediatrician confirmation
- Consumer describes a lump or swelling near groin, armpit, or neck -> system should explain possible lymph node involvement, cross-reference Infections and Cancer categories, and recommend prompt in-person evaluation rather than self-treatment

## Category-Specific Rules
- Always ask for or flag the importance of three key descriptors before attempting a differential: lesion appearance (color, texture, shape), body location, and duration — these are the minimum viable inputs for dermatology triage
- When a consumer describes a ring-shaped, bullseye, or expanding rash, immediately surface Lyme disease (erythema migrans) as a possibility and escalate urgency to 'see a doctor promptly,' especially if the consumer mentions recent outdoor activity or tick exposure
- Cross-reference the Emergency & Critical Care category for any skin presentation accompanied by fever, difficulty breathing, rapidly spreading redness, or swelling — these may indicate cellulitis, sepsis, or anaphylaxis requiring emergency care
- Do not recommend specific prescription medications by name; instead describe the class of treatment (e.g., 'a topical antifungal' or 'an oral antihistamine') and direct the consumer to confirm with a pharmacist or physician, especially for steroid or antibiotic use
- For pediatric skin queries, always note that infant and child skin conditions often have different causes and treatments than adult equivalents, and recommend a pediatrician or pediatric dermatologist rather than adult-oriented OTC guidance

## Known Pitfalls
- Conflating fungal and bacterial infections: the sample data shows cases where antibiotics (cephalexin) were prescribed for what was likely a fungal infection (tinea), and vice versa — the system must flag when treatment non-response suggests a misdiagnosis of infection type
- Over-reassuring on recurring or persistent lesions: several sample cases show conditions that returned after initial treatment (e.g., recurring mouth ulcers, recurring rashes) — the system must avoid framing recurrence as automatically benign and should recommend follow-up evaluation
- Treating 'mouth ulcers' and 'skin rashes' near the mouth as purely dermatological when they may reflect systemic causes: sample data links oral lesions to acid reflux, nutritional deficiency, and immune dysfunction — the system must flag cross-category possibilities rather than defaulting to topical treatment advice
- Assuming neonatal or infant skin conditions are the same as adult conditions: the sample shows neonatal acne being driven by maternal testosterone, not the same mechanism as adolescent acne — applying adult acne logic to infant rashes is a key pitfall to avoid

## Dominant Explanation Style
TIER_A responses follow a symptom-acknowledgment then differential-diagnosis pattern, naming a likely condition and its mechanism before suggesting a specific treatment class (topical steroids, antifungals, antihistamines) with occasional lab or follow-up recommendations. Explanations are concise and directive, written as if from a consulting physician, with moderate medical terminology softened by brief plain-language clarifications.

