<!-- STATUS: DRAFT -- awaiting human review -->

# Hormones, Metabolism & Nutrition

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 18,031 | MedMCQA: 15,726 | PubMedQA: 39 | MedQuAD: 268
- **Missing explanations**: 977 (5.4%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 6,366 | 35% |
| TIER_B | 8,890 | 49% |
| TIER_C | 1,382 | 8% |
| TIER_D | 1,393 | 8% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Biochemistry | 7,178 |
| Physiology | 4,964 |
| Medicine | 1,384 |
| Surgery | 700 |
| Pharmacology | 699 |
| Pathology | 311 |
| Anatomy | 211 |
| Gynaecology & Obstetrics | 160 |
| Unknown | 59 |
| Radiology | 38 |

## Sample Questions

- [healthcaremagic_records] [TIER_D] I am an 18 year old female taking seizure medication from almost three years.I also suffer from hyperthyroidism and have a history of hamstring muscle...
- [healthcaremagic_records] [TIER_B] I have edema in my lower legs due to obesity . They have become dark, hard and scaley with a built up of a oily dirty film. How can I removve the buil...
- [healthcaremagic_records] [TIER_B] Bilirubin elevated to 2.7, I m 57 y/o have high blood pressure, mostly controlled with medicine, high cholesterol, & hypothyroidism. 40 lbs overweight...
- [healthcaremagic_records] [TIER_A] Hi Sir, I got few lumps on my face around 20 now.. It increased.. It doesn t pain but but when i shave it disturb and some time by mistake i cut them ...
- [healthcaremagic_records] [TIER_B] I have slight PCOD. I am 37 years. Doctor advised me to take Obimet SR 500 mg twice a day alongwith Ovacare and B vitamin tablet Nurac HR. What are it...

## Links
<!-- Derived from secondary_category co-occurrence in 18,031 DB records -->
- **Strong links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 773 cross-hits
  - [Cancer](cancer.md) — 407 cross-hits
  - [Heart & Blood Vessels](heart_blood_vessels.md) — 67 cross-hits
- **Weak links:**
  - [Emergency & Critical Care](emergency_critical_care.md) — 56 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 48 cross-hits
  - [Women's & Reproductive Health](womens_reproductive.md) — 47 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Thyroid Disorders, Diabetes & Blood Sugar, Vitamin & Mineral Deficiencies, Hormonal Imbalances, Metabolic Disorders, Anemia & Blood Health, Obesity & Weight Management, Bone & Calcium Metabolism
- **Confidence:** High

## Source Priority
1. NIH MedlinePlus and National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)
2. American Thyroid Association and Endocrine Society patient resources
3. Mayo Clinic and Cleveland Clinic condition explainers
4. WebMD and Healthline with editorial medical review
5. Community health forums and peer-reported symptom descriptions
**Rationale:** Hormonal and metabolic conditions require precise lab reference ranges and evidence-based treatment thresholds that only major endocrine health authorities and academic medical centers reliably provide. Consumer-facing forum content is useful for symptom framing but must be cross-validated against clinical guidelines due to high risk of misinterpretation of lab values.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| thyroid problems | hypothyroidism / hyperthyroidism | Consumers rarely distinguish under- from over-active thyroid; system must clarify direction of dysfunction based on symptoms described |
| blood sugar | serum glucose / glycemia | Consumers use 'blood sugar' broadly for both fasting glucose and post-meal readings; clarify which type is being referenced |
| low vitamin D | vitamin D deficiency / 25-hydroxyvitamin D insufficiency | Consumers frequently self-diagnose via fatigue and bone pain; system should explain lab threshold differences between deficiency and insufficiency |
| iron levels low | iron deficiency anemia / hypoferritinemia | Consumers conflate low iron with anemia broadly; system should distinguish iron stores (ferritin) from hemoglobin-based anemia |
| hormonal imbalance | endocrine dysfunction / dysregulation of sex or adrenal hormones | Extremely vague consumer term applied to a wide range of symptoms; system must ask clarifying questions about specific symptoms or lab results |
| metabolism is slow | hypometabolism / low basal metabolic rate | Often linked by consumers to thyroid issues; system should map to hypothyroidism workup while noting other causes like caloric restriction |
| calcium supplement | calcium carbonate / calcium citrate supplementation | Consumers rarely distinguish forms of calcium; system should note that absorption differs and context (with food, vitamin D co-administration) matters |
| B12 deficiency | cobalamin deficiency / megaloblastic changes | Consumers associate B12 with energy and nerve symptoms; system should connect to dietary sources, absorption issues, and metformin interaction |

## Common Query Patterns
- Consumer reports vague fatigue with lab results mentioned -> system should extract specific lab values, compare to standard reference ranges, and suggest relevant follow-up tests such as TSH, ferritin, or vitamin D levels
- Consumer asks whether a supplement is safe alongside diabetes or BP medication -> system must flag potential interactions, recommend pharmacist or physician review, and avoid confirming safety without clinical context
- Consumer describes tingling, numbness, or weakness alongside a chronic condition like diabetes -> system should highlight neuropathy as a likely complication, explain the mechanism in plain language, and recommend clinical evaluation
- Consumer shares a lab report with unfamiliar terms like 'hypochromic' or 'anisopoikilocytosis' -> system should define each term in plain language, explain what it may indicate clinically, and note that diagnosis requires physician interpretation
- Consumer asks if their symptoms could be hormonal -> system should avoid confirming 'hormonal imbalance' without specifics, instead map symptoms to plausible hormonal conditions and recommend targeted blood tests

## Category-Specific Rules
- Always contextualize lab values against standard reference ranges when a consumer shares numbers, and explicitly state that normal ranges can vary by lab and population before drawing any interpretive conclusion
- When thyroid symptoms are described and TSH has been tested as 'normal', flag that a full thyroid panel (free T3, free T4, thyroid antibodies) may still be warranted, as TSH alone can miss subclinical dysfunction
- Never recommend stopping or adjusting doses of diabetes, thyroid, or hormonal medications based on consumer-reported symptoms alone; always direct the consumer to their prescribing physician for medication changes
- When a consumer with a chronic metabolic condition (e.g., thalassemia, diabetes, CKD) reports new symptoms, the system must consider disease-related complications first before suggesting unrelated causes
- Distinguish clearly between nutritional supplementation advice (e.g., vitamin D, B12, calcium) and prescription hormone therapy; over-the-counter supplements carry different safety profiles and should not be conflated with prescription treatments

## Known Pitfalls
- Assuming 'thyroid ruled out' based on TSH alone is complete: sample data shows TSH screening can miss hypothyroid states, and agents must not accept a single normal TSH as definitive exclusion of thyroid disease
- Conflating anemia with iron deficiency: sample data shows conditions like thalassemia cause anemia through a different mechanism than iron deficiency, and recommending iron supplementation in such cases can cause harmful iron overload
- Attributing all fatigue, weakness, or tingling to a single cause like vitamin deficiency: sample data reveals these symptoms overlap across thyroid dysfunction, diabetes, anemia, and nerve damage, requiring agents to present a differential rather than a single explanation
- Treating consumer-reported supplement names (e.g., 'Shelcal-CT') as self-sufficient explanations for symptoms: agents must look up the active ingredients and explain the actual mechanism rather than validating the supplement by brand name alone

## Dominant Explanation Style
TIER_A responses in this category follow a pattern of acknowledging the consumer's specific lab values or symptoms, offering a ranked set of likely diagnoses with brief mechanistic explanations, and closing with concrete next steps such as additional tests or specialist referrals. The tone is direct and clinically informed but accessible, often explicitly noting what further workup is needed rather than offering a single definitive answer.

