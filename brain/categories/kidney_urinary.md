<!-- STATUS: DRAFT -- awaiting human review -->

# Kidney & Urinary Health

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 10,825 | MedMCQA: 5,176 | PubMedQA: 34 | MedQuAD: 312
- **Missing explanations**: 455 (4.2%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 2,789 | 26% |
| TIER_B | 4,543 | 42% |
| TIER_C | 1,487 | 14% |
| TIER_D | 2,006 | 19% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Surgery | 1,262 |
| Medicine | 1,049 |
| Pathology | 733 |
| Physiology | 538 |
| Anatomy | 466 |
| Pharmacology | 406 |
| Gynaecology & Obstetrics | 189 |
| Biochemistry | 162 |
| Radiology | 153 |
| Unknown | 68 |

## Sample Questions

- [healthcaremagic_records] [TIER_C] A Contrast CT scan was done on my boyfriend and they sound a solid mass on the upper pole of his left kidney. He also had extremely high blood pressur...
- [healthcaremagic_records] [TIER_B] Hi I have a really severe pain in my back by my kidneys and abdominal pains too . I have been to my gp several times and the first time he gave me ant...
- [healthcaremagic_records] [TIER_D] usg finging shows prostate enlarged in size median lobe enlargement 16.1 mm, U.V 118 ml. doctor suggest for review USG pvr & PSA , DOCTOR ALSO PRESCRI...
- [healthcaremagic_records] [TIER_D] Please tell me about Causes of kidney disease?...
- [healthcaremagic_records] [TIER_C] Hi, my son is just 6months old. Since, three months of his birth, there is huge variation in his body temp (primarily head & foot) and very frequently...

## Links
<!-- Derived from secondary_category co-occurrence in 10,825 DB records -->
- **Strong links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 538 cross-hits
  - [Cancer](cancer.md) — 492 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 382 cross-hits
- **Weak links:**
  - [Heart & Blood Vessels](heart_blood_vessels.md) — 271 cross-hits
  - [Emergency & Critical Care](emergency_critical_care.md) — 239 cross-hits
  - [Infections & Infectious Disease](infections.md) — 228 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Kidney Stones, Urinary Tract Infections, Chronic Kidney Disease, Kidney Transplant & Post-Transplant Care, Renal Lab Values & Diagnostics, Bladder & Urinary Tract Disorders, Dialysis & Kidney Failure, Kidney Cancer & Tumors, Electrolyte & Fluid Balance, Urological Procedures & Surgery
- **Confidence:** High

## Source Priority
1. National Kidney Foundation (kidney.org) — clinical guidelines and patient education
2. National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)
3. Mayo Clinic kidney and urology health pages
4. Urology Care Foundation (urologyhealth.org)
5. WebMD and Healthline kidney/urinary health sections
**Rationale:** The National Kidney Foundation and NIDDK produce peer-reviewed, guideline-aligned patient education specifically for renal conditions, making them the most authoritative sources for this category. Lay-focused sites like Mayo Clinic and Urology Care Foundation are prioritized next because they bridge clinical accuracy with consumer-readable language relevant to the query patterns seen in this category.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| kidney stone | nephrolithiasis or ureterolithiasis | Consumers almost universally say 'kidney stone'; the medical term changes based on stone location but this distinction rarely matters for consumer queries |
| creatinine levels | serum creatinine / eGFR | Consumers often mention creatinine from lab reports without understanding it reflects kidney filtration function; pairing it with eGFR explanation is critical |
| kidney failure | acute kidney injury (AKI) or end-stage renal disease (ESRD) | Consumers use 'kidney failure' for both temporary and permanent conditions; distinguishing acute vs. chronic is essential for accurate guidance |
| bladder infection | urinary tract infection (UTI) / cystitis | Consumers conflate all UTIs with bladder infections; upper vs. lower tract distinction affects urgency and treatment recommendations |
| kidney transplant rejection | allograft rejection (acute or chronic) | Post-transplant consumers frequently search for symptoms of rejection; clarifying acute vs. chronic rejection helps them recognize urgency |
| passing a kidney stone | spontaneous stone passage / ureteral calculus expulsion | Consumers want practical timelines and symptom guidance; stone size and location in the ureter are key clinical factors to communicate |
| protein in urine | proteinuria / albuminuria | A common early sign of kidney disease that consumers notice on urinalysis reports; explaining its significance without causing undue alarm is important |
| swollen kidneys | hydronephrosis | Consumers describe this symptom after imaging; explaining it as fluid backup due to obstruction (often from stones) helps contextualize the diagnosis |

## Common Query Patterns
- How long does it take to pass a kidney stone -> Provide size-based timelines (small <4mm usually passes in days, 4-6mm may take weeks, >6mm often needs intervention), note that ureter location matters, and advise the consumer to follow up with their doctor if pain is severe or no passage occurs within 4-6 weeks
- My creatinine is high, what does that mean -> Explain that creatinine is a waste product filtered by kidneys and elevated levels may indicate reduced kidney function, recommend discussing eGFR alongside creatinine with their doctor, and flag that a single reading needs context from their full history
- What are the signs of a UTI vs a kidney infection -> Distinguish lower UTI symptoms (burning urination, frequency, cloudy urine) from upper UTI/pyelonephritis symptoms (fever, back/flank pain, nausea), and clearly state that kidney infection symptoms warrant prompt medical evaluation
- What can I eat to prevent kidney stones -> Provide evidence-based dietary guidance (increase water intake, reduce sodium and animal protein, moderate oxalate foods for calcium-oxalate stones), note that stone type determines diet recommendations, and encourage the consumer to ask their doctor for a 24-hour urine analysis to tailor advice
- I had a kidney transplant and now I have [symptom] -> Treat all post-transplant symptom queries with elevated urgency, flag that immunosuppression changes how infections and complications present, advise the consumer to contact their transplant team promptly, and avoid recommending over-the-counter solutions that may interact with immunosuppressants

## Category-Specific Rules
- Always flag kidney stone queries with stone size context: stones larger than 6mm rarely pass on their own and often require urological intervention; never reassure a consumer that a large stone will 'definitely pass' without this caveat
- For any query involving lab values (creatinine, eGFR, BUN, potassium), provide reference ranges and explain what abnormal results generally mean, but always direct the consumer to discuss results with their ordering physician before drawing conclusions
- Post-kidney-transplant queries must be treated as high-sensitivity: immunosuppressant interactions, infection risk, and rejection symptoms require immediate professional follow-up; the system must not suggest home remedies or delayed care for this population
- When a query involves both kidney disease and another category (e.g., multiple myeloma causing kidney failure, or medications causing kidney damage), invoke cross-category retrieval for Medications & Drug Safety or Cancer to provide complete context rather than answering from kidney data alone
- Never conflate acute kidney injury (reversible, sudden) with chronic kidney disease or end-stage renal disease (progressive, long-term); always clarify the distinction when these terms appear in consumer queries or retrieved content

## Known Pitfalls
- Assuming all kidney or flank pain is from kidney stones: the sample data shows queries where rash, scrotal swelling, or stomach pain were actually linked to urinary or post-surgical causes; the system must avoid premature stone attribution and consider broader differential contexts
- Treating high creatinine as a standalone finding: the sample data shows creatinine appearing in contexts ranging from liver disease queries to multiple myeloma; the system must not interpret elevated creatinine as isolated kidney disease without considering the full clinical picture provided by the consumer
- Overlooking post-transplant complexity: the sample data shows transplant patients presenting with unusual symptoms (electric sensations, testicular swelling) that could be misrouted to general urology or neurology; transplant queries must always be flagged for specialized nephrology-level guidance and urgent follow-up
- Confusing gallbladder or digestive symptoms with kidney symptoms: multiple sample questions involve consumers who mention kidney stones but are actually describing symptoms more consistent with gallbladder or GI issues (e.g., spring roll avoidance, stomach discomfort); the system must not default to kidney explanations when the symptom pattern suggests a digestive etiology

## Dominant Explanation Style
TIER_A responses in this category follow a structured clinical-consultation style: they briefly acknowledge the consumer's concern, restate the key facts from the query, offer a probable explanation grounded in the reported symptoms or labs, and then recommend specific next diagnostic steps (e.g., ultrasound, urine culture, blood panel). Explanations are direct and action-oriented rather than purely educational, often listing tests and treatments in plain language while maintaining clinical precision.

