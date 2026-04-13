<!-- STATUS: DRAFT -- awaiting human review -->

# Women's & Reproductive Health

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 12,011 | MedMCQA: 4,617 | PubMedQA: 57 | MedQuAD: 86
- **Missing explanations**: 118 (1.0%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 2,220 | 18% |
| TIER_B | 4,718 | 39% |
| TIER_C | 3,197 | 27% |
| TIER_D | 1,876 | 16% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Gynaecology & Obstetrics | 3,910 |
| Anatomy | 239 |
| Unknown | 102 |
| Radiology | 67 |
| Forensic Medicine | 60 |
| Pathology | 57 |
| Physiology | 48 |
| Medicine | 41 |
| Surgery | 36 |
| Microbiology | 26 |

## Sample Questions

- [healthcaremagic_records] [TIER_C] hi i am trying to get pregnant since my last day of my period witch was july 1,2012 it lasted 4 days only and we had unprotected sex since july 5.. i ...
- [healthcaremagic_records] [TIER_C] Hi, i am 29 years old, i have been trying to conceive... recently i have been on drugs ... clomid , pregnacare conception ,,later i took fertomid but ...
- [healthcaremagic_records] [TIER_C] Hi, I misscarried in early november last year. and went straight back on the pill had one break and a period came. now im on the pill witha week to go...
- [healthcaremagic_records] [TIER_C] HiIm trying to get pregnant I want it more than anything to start a family with my husband but I take laxatives every week and eat around 600 calories...
- [healthcaremagic_records] [TIER_D] i think i may be pregnant because last tuesday i had sex without a condom . i know one of the symptoms is missing your period. i dont get my period of...

## Links
<!-- Derived from secondary_category co-occurrence in 12,011 DB records -->
- **Strong links:**
  - [Children's Health](childrens_health.md) — 338 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 291 cross-hits
  - [Emergency & Critical Care](emergency_critical_care.md) — 275 cross-hits
- **Weak links:**
  - [Blood & Immune Disorders](blood_immune.md) — 249 cross-hits
  - [Medications & Drug Safety](medications_drug_safety.md) — 239 cross-hits
  - [Hormones, Metabolism & Nutrition](hormones_metabolism_nutrition.md) — 231 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Pregnancy & Prenatal Care, Postpartum Health, Menstrual Health & Disorders, Fertility & Conception, Contraception & Family Planning, Gynecological Conditions, Menopause & Perimenopause, Reproductive Anatomy & Physiology, Sexually Transmitted Infections, Hormonal Conditions & Treatments
- **Confidence:** High

## Source Priority
1. ACOG (American College of Obstetricians and Gynecologists) guidelines
2. Mayo Clinic Women's Health & Pregnancy resources
3. NIH Office of Research on Women's Health / MedlinePlus
4. Planned Parenthood clinically reviewed content
5. WebMD / Healthline women's health articles
**Rationale:** ACOG provides the gold standard clinical guidelines for obstetric and gynecological care, while NIH and Mayo Clinic offer peer-reviewed, consumer-accessible explanations. Lower-tier sources may lack clinical depth for sensitive reproductive health topics where accuracy directly impacts patient safety.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| missed period | amenorrhea or delayed menstruation | Extremely common search trigger; can indicate pregnancy, hormonal imbalance, or other conditions — context matters greatly |
| water breaking | rupture of membranes (ROM) | Pregnant consumers use this phrase; system must recognize it as a potential emergency requiring immediate medical attention |
| spotting | intermenstrual bleeding or implantation bleeding | Consumers often cannot distinguish normal spotting from warning signs; responses should clarify when spotting warrants urgent care |
| ovarian cysts | adnexal cysts or follicular cysts | Consumers frequently conflate functional cysts with pathological ones; clarifying the benign vs. serious distinction is important |
| morning sickness | nausea and vomiting of pregnancy (NVP) or hyperemesis gravidarum | Severe cases may indicate hyperemesis gravidarum requiring treatment — severity cues should escalate appropriately |
| tightening in belly during pregnancy | Braxton Hicks contractions or uterine contractions | Consumers often cannot distinguish practice contractions from true labor; gestational age context is critical |
| discharge | vaginal discharge or leukorrhea | Normal vs. abnormal discharge is a frequent concern; color, odor, and consistency clues should guide differentiation |
| getting my tubes tied | bilateral tubal ligation or tubal occlusion | Consumers use colloquial phrasing for a permanent contraceptive procedure; system should provide accurate permanence counseling context |

## Common Query Patterns
- Personal or partner symptom during pregnancy (e.g., 'I am 33 weeks pregnant and my hand is numb') -> Acknowledge pregnancy context first, identify likely benign causes (e.g., carpal tunnel of pregnancy), and flag any red-flag symptoms that would require urgent care
- Postpartum concern framed as new or worsening symptom (e.g., 'I had my baby 6 months ago and now I have severe back pain') -> Link symptom to postpartum physiological changes, recommend specific lifestyle or nutritional considerations, and advise follow-up with provider
- Fertility or conception confusion after a medical procedure (e.g., 'I had endometriosis surgery, when can I get pregnant?') -> Explain how the procedure affects reproductive anatomy, describe realistic timelines, and recommend specialist consultation rather than self-management
- Ambiguous symptom that may or may not be pregnancy-related (e.g., 'I feel nauseous and pee a lot, am I pregnant?') -> List differential causes including pregnancy and infection, explain how to evaluate each, and recommend a pregnancy test as a first step before clinical workup
- Concern about a physical finding during intimacy or self-exam (e.g., 'I felt something hard inside, is that normal?') -> Normalize common anatomical features (e.g., cervix), reassure where appropriate, and advise gynecological examination if uncertainty or other symptoms are present

## Category-Specific Rules
- Always capture gestational age or postpartum timeline when present in the query, as trimester and weeks-postpartum context fundamentally change what symptoms are normal vs. concerning and what advice is appropriate.
- For any pregnancy-related symptom involving abdominal pain, bleeding, reduced fetal movement, or fluid leakage, the system must include an explicit prompt to seek immediate medical evaluation, regardless of how mild the consumer frames it.
- When a query involves a prescription medication in a reproductive context (e.g., hormonal therapies, progesterone supplements, antibiotics during pregnancy), cross-reference with the 'Medications & Drug Safety' category and flag known pregnancy safety classifications.
- Do not provide fertility treatment protocols or specific dosing adjustments for fertility drugs; responses should explain mechanisms and direct users to reproductive endocrinologists or OB-GYNs for personalized plans.
- When a consumer query involves a minor (under 18) in a sexual or reproductive health context, provide accurate health information without judgment, include privacy-sensitive framing, and note availability of confidential care resources such as Planned Parenthood.

## Known Pitfalls
- Assuming all numbness or musculoskeletal symptoms during pregnancy are emergencies — as the sample data shows, conditions like carpal tunnel syndrome are common and benign in pregnancy; over-alarming consumers can cause unnecessary anxiety and ER visits.
- Treating postpartum symptoms as isolated new conditions rather than sequelae of pregnancy — back pain, hormonal fluctuations, and dental changes frequently originate from pregnancy physiology and should be contextualized accordingly.
- Conflating a thin endometrial lining with a single cause — the sample data shows multiple etiologies including poor perfusion, tuberculosis, and prior hormonal treatment; the system must avoid oversimplifying complex gynecological findings.
- Dismissing ambiguous early pregnancy symptoms (nausea, frequent urination, bowel changes) as purely gastrointestinal or infectious without surfacing pregnancy as a plausible explanation, particularly when the user mentions trying to conceive.

## Dominant Explanation Style
TIER_A responses lead with reassurance or a brief normalized explanation of the likely benign cause, then provide a mechanistic rationale grounded in hormonal or anatomical changes, and close with a concrete clinical recommendation (supplement, test, or specialist referral). The tone is direct and conversational, addressing the consumer's emotional concern before delivering clinical detail.

