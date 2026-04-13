<!-- STATUS: DRAFT -- awaiting human review -->

# Public Health & Prevention

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 24,496 | MedMCQA: 11,972 | PubMedQA: 10 | MedQuAD: 5,220
- **Missing explanations**: 1,539 (6.3%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 9,239 | 38% |
| TIER_B | 8,262 | 34% |
| TIER_C | 3,531 | 14% |
| TIER_D | 3,464 | 14% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Social & Preventive Medicine | 11,863 |
| Gynaecology & Obstetrics | 24 |
| Surgery | 16 |
| Medicine | 16 |
| Unknown | 13 |
| Pathology | 12 |
| Anatomy | 8 |
| Microbiology | 7 |
| Radiology | 6 |
| Anaesthesia | 3 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] hlw sir i am 24 years old bt unmarried.i do hand practice from when i am in 6 class.i have problem that is when i went in bathroom then automatically ...
- [healthcaremagic_records] [TIER_C] Hello, I feel pain some times in my penis, especially in the left-hand side of it. This pain comes for a second and go, then come again for a second a...
- [healthcaremagic_records] [TIER_B] Hi, I have a low wbc and used botox.  Loved the results.  Felt fine.  However I went to get a physical and my wbc lowered from 3.7 to 2.1.  So I waite...
- [healthcaremagic_records] [TIER_B] i have back pain since from 6 month. please advise me to which hospital i should i contact. let me know reason for back pain as i am getting lot of ba...
- [healthcaremagic_records] [TIER_B] Hi Doctor,i have wheatisChatDoctorplexion and i am 26 years old girl.i want to know that is there any way to get fair complexion,and please suggest me...

## Links
<!-- Derived from secondary_category co-occurrence in 24,496 DB records -->
- **Strong links:**
  - [Infections & Infectious Disease](infections.md) — 1,039 cross-hits
  - [Children's Health](childrens_health.md) — 495 cross-hits
  - [Ear, Nose & Throat](ear_nose_throat.md) — 338 cross-hits
- **Weak links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 293 cross-hits
  - [Women's & Reproductive Health](womens_reproductive.md) — 289 cross-hits
  - [Cancer](cancer.md) — 276 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Vaccinations & Immunization, Infection Prevention & Hygiene, Screening & Early Detection, Nutrition & Lifestyle Prevention, Environmental & Occupational Health, Mental Health Promotion, Maternal & Child Public Health, Chronic Disease Prevention, Outbreak & Epidemic Awareness, Sexual Health & STI Prevention
- **Confidence:** High

## Source Priority
1. CDC (Centers for Disease Control and Prevention)
2. WHO (World Health Organization)
3. NIH / MedlinePlus
4. Mayo Clinic / Cleveland Clinic
5. WebMD / Healthline (consumer-facing summaries)
**Rationale:** Public health guidance is most reliably grounded in CDC and WHO policy documents, which reflect consensus across epidemiological evidence and are updated with outbreaks and new data. Consumer-facing clinic sites are useful for plain-language explanation but should be cross-checked against authoritative public health bodies.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| flu shot | influenza vaccination | Consumers rarely search for 'influenza immunization' — mapping ensures retrieval of vaccine schedules and efficacy data |
| swollen glands | lymphadenopathy / lymphadenitis | Extremely common consumer complaint that may signal infection, autoimmune issue, or malignancy — seen directly in sample data |
| spreading germs | pathogen transmission / communicable disease spread | Lay framing used in hygiene and prevention queries; maps to routes of transmission content |
| lump | mass / nodule / cyst / bursitis | Highly ambiguous consumer term seen repeatedly in sample data; could indicate benign or serious pathology |
| booster shot | vaccine booster dose / supplemental immunization | Common in adult and travel vaccine queries; maps to immunization schedule guidance |
| tingling in hands and feet | peripheral neuropathy / paresthesia | Common symptom query that may indicate systemic disease — seen in sample data, important for early detection screening guidance |
| snap or clicking sound in jaw | temporomandibular disorder (TMD) / crepitus | Consumers describe sounds mechanically; maps to TMJ/TMD clinical content as shown in sample data |
| carrier of a disease | asymptomatic carrier / disease reservoir | Public health concept that consumers encounter during outbreak education and STI prevention contexts |

## Common Query Patterns
- Consumer describes a physical symptom and asks if it is serious -> system should triage by flagging red-flag symptoms, provide general prevention context, and strongly recommend in-person evaluation
- Consumer asks how to prevent catching a specific illness -> retrieve CDC/WHO prevention guidelines, include hygiene, vaccination, and exposure-reduction steps in plain language
- Consumer asks about a lump, swelling, or abnormal growth -> clarify range of benign and serious causes, avoid alarm language, emphasize that diagnosis requires clinical examination as shown in sample data
- Consumer asks whether a vaccine is necessary or safe -> retrieve current immunization schedule guidance, acknowledge common concerns, cite CDC/WHO sources, do not validate anti-vaccine claims
- Consumer describes recent exposure to an infected person -> provide incubation period information, symptom monitoring advice, and when to seek testing or care based on CDC guidance

## Category-Specific Rules
- Always distinguish between general prevention advice (appropriate to provide) and individual clinical diagnosis (must be referred to a healthcare provider), especially when sample queries describe specific symptoms like lumps or neurological tingling.
- When returning vaccination information, always specify whether guidance applies to children, adults, or specific risk groups, and link to the current CDC immunization schedule rather than generic statements.
- For queries involving swollen lymph nodes, lumps, or masses, the system must surface red-flag indicators (rapidly growing, painless, persistent over 2 weeks, accompanied by fever or weight loss) and recommend professional evaluation without speculating on diagnosis.
- Cross-reference with the Infections & Infectious Disease category when queries involve communicable disease prevention, outbreak exposure, or symptom onset after contact with a sick individual.
- Do not provide dosage, prescription, or treatment protocol recommendations under the Public Health & Prevention category — route consumer to Medications & Drug Safety or a clinician for those queries.

## Known Pitfalls
- Conflating a consumer symptom query (e.g., 'lump on my palate') with a pure prevention question — sample data shows many queries in this category are actually symptom-driven and require clinical referral language, not just prevention education.
- Assuming all 'swollen gland' queries are minor infections — sample data includes occipital lymphadenitis described as potentially serious, so agents must not default to reassurance without flagging when professional evaluation is warranted.
- Over-generalizing prevention advice without accounting for individual risk factors (age, post-surgical history, chronic conditions) — the low sperm count sample shows that personal medical history significantly changes the appropriate guidance.
- Treating clicking or snapping joint sounds as purely mechanical without noting that persistent or painful crepitus (as in the TMD sample) may require imaging or specialist referral, not just self-care prevention tips.

## Dominant Explanation Style
Responses in the TIER_A data follow a reassurance-first, differential-diagnosis structure where the expert acknowledges the consumer's concern, lists two to four possible causes ranked by likelihood, and closes with a clear recommendation to seek in-person evaluation or further investigation. Explanations use accessible anatomical language with brief technical terms introduced parenthetically.

