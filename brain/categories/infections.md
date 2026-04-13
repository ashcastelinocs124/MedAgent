<!-- STATUS: DRAFT -- awaiting human review -->

# Infections & Infectious Disease

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 24,830 | MedMCQA: 12,044 | PubMedQA: 43 | MedQuAD: 556
- **Missing explanations**: 1,352 (5.4%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 6,551 | 26% |
| TIER_B | 12,643 | 51% |
| TIER_C | 1,734 | 7% |
| TIER_D | 3,902 | 16% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Microbiology | 8,738 |
| Medicine | 962 |
| Surgery | 553 |
| Pathology | 407 |
| Gynaecology & Obstetrics | 402 |
| Pharmacology | 305 |
| Anatomy | 210 |
| Forensic Medicine | 132 |
| Unknown | 123 |
| Biochemistry | 120 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] Hi doctors, ive heard of a \"human embryo\" vaccine for dog bite. can i have this vaccine instead of usual antirabbies (5shots) for my relative? am i ...
- [healthcaremagic_records] [TIER_A] hello doctor,i amm 22 years old.. i heve been masturbating for past 5 years... i am having pain in my testis for about 2 years.. i have done all the t...
- [healthcaremagic_records] [TIER_B] Good day. i just wanted to ask if what are the earliest and visible signs of rabies in humans? i was bitten by a dog 3 days ago and its not that deep ...
- [healthcaremagic_records] [TIER_A] Gud aftrnun sir, My husband is suffering with low grade fever from two months. He also has sore throat n swelling in the throat .doctor says Its becau...
- [healthcaremagic_records] [TIER_D] I have reoccuring yeast infections and i most recently experienced  cracking around my anus and bumps on my vulva and labia and around my anus, the ye...

## Links
<!-- Derived from secondary_category co-occurrence in 24,830 DB records -->
- **Strong links:**
  - [Kidney & Urinary Health](kidney_urinary.md) — 1,022 cross-hits
  - [Skin & Dermatology](skin_dermatology.md) — 937 cross-hits
  - [Dental & Oral Health](dental_oral.md) — 861 cross-hits
- **Weak links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 650 cross-hits
  - [Ear, Nose & Throat](ear_nose_throat.md) — 471 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 422 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Bacterial Infections, Viral Infections, Fungal & Yeast Infections, Sexually Transmitted Infections (STIs), Urinary Tract Infections, Respiratory & Throat Infections, Skin & Wound Infections, Parasitic & Vector-Borne Infections
- **Confidence:** High

## Source Priority
1. CDC (Centers for Disease Control and Prevention)
2. WHO (World Health Organization)
3. NIH / MedlinePlus
4. Mayo Clinic / Cleveland Clinic
5. WebMD / Healthline (consumer-facing)
**Rationale:** CDC and WHO provide authoritative, regularly updated guidance on infectious disease epidemiology, treatment protocols, and public health recommendations. NIH and major academic medical centers offer peer-reviewed, mechanism-grounded explanations appropriate for consumer-level understanding.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| stomach bug | gastroenteritis | Extremely common search term; consumers rarely use 'gastroenteritis' and need bridging to accurate treatment info |
| strep throat | streptococcal pharyngitis | Consumer term is widely understood but agents must distinguish it from viral sore throat since strep requires antibiotics |
| yeast infection | candidiasis | Used for both vaginal and oral (thrush) infections; disambiguation by body site is critical |
| pink eye | conjunctivitis | Consumers use this for both bacterial and viral forms; treatment differs significantly between the two |
| nail fungus | onychomycosis | As seen in sample data, consumers often try home remedies first; agents should flag when prescription antifungals are needed |
| tooth abscess | dental abscess / periapical abscess | Strong cross-category signal with Dental & Oral Health; facial swelling signals potential spread requiring urgent care |
| UTI | urinary tract infection | High cross-category overlap with Kidney & Urinary Health; must distinguish lower UTI from upper (pyelonephritis) |
| chills and shaking | rigors / febrile rigors | Sample data shows consumers describe this vividly without knowing the term; rigors can signal bacteremia and require urgent triage |

## Common Query Patterns
- Symptom-cluster questions ('I have fever, sore throat, and swollen glands') -> map to likely infections, flag red-flag symptoms like prolonged fever or difficulty breathing, and recommend professional evaluation
- Home remedy efficacy questions ('can tea tree oil cure toenail fungus') -> acknowledge partial evidence, explain limitations, and recommend clinically validated treatments such as topical or oral antifungals
- Recurring or treatment-resistant infection questions ('my wife keeps getting H. pylori after antibiotics') -> explain antibiotic resistance, incomplete treatment courses, and the need for specialist referral or test-of-cure
- STI concern questions ('I had unprotected sex and now have symptoms') -> respond factually without judgment, map symptoms to possible STIs, strongly recommend testing at a clinic, and avoid definitive diagnosis
- Duration-based urgency questions ('my son has had a fever for a week') -> use duration and age to tier urgency, highlight when prolonged or high fever warrants immediate medical attention rather than home management

## Category-Specific Rules
- Always triage by red-flag symptoms first: high fever lasting more than 3 days, facial swelling from dental infection, rigors, or swollen lymph nodes with systemic symptoms must prompt an immediate 'seek care now' recommendation
- Never diagnose a specific STI from symptom description alone; always recommend professional STI testing and frame the response around what testing is available and why it matters
- When antibiotics are mentioned by the consumer, clarify whether the drug is appropriate for bacterial vs. viral infections and always reinforce the importance of completing the full prescribed course
- Cross-reference with Kidney & Urinary Health subcategory logic when UTI symptoms are described, and escalate to pyelonephritis risk language if the consumer mentions back pain, high fever, or vomiting alongside urinary symptoms
- For fungal infection queries, distinguish between superficial fungal infections (skin, nail, oral) and invasive fungal infections, and match treatment recommendations (OTC vs. prescription) to severity and infection site

## Known Pitfalls
- Conflating allergy with infection: sample data shows clinicians themselves sometimes blur this distinction; agents must not attribute persistent low-grade fever or swollen lymph nodes to allergy without ruling out infectious causes first
- Underestimating dental infections: sample data shows consumers delay care when pain is absent, but facial swelling from a tooth abscess can indicate spreading infection requiring urgent antibiotics or extraction, not watchful waiting
- Assuming a normal lab result rules out infection: sample data shows patients with pain and abnormal findings can have normal standard tests; agents should not reassure consumers that 'tests were normal so there is no infection' without qualification
- Providing overly specific antibiotic recommendations: sample data mentions drugs like amoxicillin and itraconazole by name; consumer-facing responses should explain drug classes and why a doctor selects them rather than recommending specific medications, to avoid unsafe self-medication

## Dominant Explanation Style
TIER_A responses in this category follow a symptom-validation-then-differential pattern: they acknowledge the consumer's described symptoms, offer 2-3 plausible infectious causes ranked by likelihood, and recommend a specific next clinical step such as a lab test, specialist referral, or prescription class. Explanations are direct and moderately technical, often naming specific pathogens or drug classes while briefly explaining their relevance in plain language.

