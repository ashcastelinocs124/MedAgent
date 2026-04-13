<!-- STATUS: DRAFT -- awaiting human review -->

# Heart & Blood Vessels

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 24,439 | MedMCQA: 12,697 | PubMedQA: 87 | MedQuAD: 937
- **Missing explanations**: 2,082 (8.5%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 5,459 | 22% |
| TIER_B | 10,742 | 44% |
| TIER_C | 3,387 | 14% |
| TIER_D | 4,851 | 20% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Medicine | 7,168 |
| Radiology | 2,155 |
| Physiology | 824 |
| Pharmacology | 745 |
| Pathology | 600 |
| Anatomy | 361 |
| Surgery | 285 |
| Gynaecology & Obstetrics | 167 |
| Anaesthesia | 132 |
| Unknown | 128 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] I am 82 yrs. old. My primary doctor gave me a DTP shot on 6/12/14. On Sat., 6/14/14 I got up and within a few minutes I felt faint. I was sweaty and l...
- [healthcaremagic_records] [TIER_D] Hello ! i am 23 years old male and i had a so called panic attack 1 and a half years ago. Since then i am upset regarding my heart and have taking ate...
- [healthcaremagic_records] [TIER_B] I wanted to know if there was a difference in taking (3) venlafaxine er 75 mg capsule, extended versus a 150 mg tablet ? What I had done without consu...
- [healthcaremagic_records] [TIER_C] Thank you. I am seeing a cardiologist, because I sometimes have incidents of chest constriction, discomfort, sometimes lightheadedness (and now on Los...
- [healthcaremagic_records] [TIER_B] when im talking to some one .... and i get the feeling that the heat of this chat is going up ... my hands shake ... i hear my heart beats .... like i...

## Links
<!-- Derived from secondary_category co-occurrence in 24,439 DB records -->
- **Strong links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 1,095 cross-hits
  - [Brain & Nervous System](brain_nervous_system.md) — 771 cross-hits
  - [Breathing & Lungs](breathing_lungs.md) — 652 cross-hits
- **Weak links:**
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 535 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 532 cross-hits
  - [Emergency & Critical Care](emergency_critical_care.md) — 484 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** High Blood Pressure & Hypertension, Heart Attack & Chest Pain, Heart Rhythm & Palpitations, Heart Failure & Fluid Retention, Peripheral Artery & Vein Disease, Cholesterol & Atherosclerosis, Stroke & Blood Clots, Congenital & Structural Heart Conditions
- **Confidence:** High

## Source Priority
1. American Heart Association (AHA) official guidelines and patient resources
2. Mayo Clinic cardiology department articles and symptom checkers
3. NIH MedlinePlus cardiovascular disease pages
4. Cleveland Clinic Heart & Vascular Institute patient education
5. WebMD cardiology articles (use only when corroborated by above sources)
**Rationale:** Cardiovascular conditions carry high risk of serious harm if misunderstood, so only evidence-based, guideline-aligned sources from major cardiology institutions should anchor responses. Consumer-facing portals like WebMD are acceptable supplements but must not be used as sole references given the life-threatening nature of many heart and vessel conditions.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| heart attack | myocardial infarction (MI) | Consumers universally use 'heart attack'; always cross-reference this term when indexing clinical content about MI |
| irregular heartbeat or heart fluttering | arrhythmia or atrial fibrillation | Consumers rarely use 'arrhythmia'; phrasing like 'my heart skips a beat' or 'fluttering chest' are common entry points |
| high blood pressure | hypertension | Nearly all consumer queries use 'high blood pressure' rather than 'hypertension'; both must be indexed together |
| swollen legs or puffy ankles | peripheral edema or lower extremity edema | Swelling in legs is a key symptom consumers describe for both heart failure and PAD; disambiguation is critical |
| chest pressure or heaviness | angina pectoris or cardiac chest pain | Consumers rarely say 'angina'; 'chest heaviness,' 'pressure,' or 'weight on chest' are the typical phrasings |
| heart racing or fast heartbeat | tachycardia or supraventricular tachycardia (SVT) | Consumers describe this symptom narratively; the system must map it to tachycardia-related content while flagging anxiety as a common non-cardiac cause |
| hardening of the arteries | atherosclerosis | Lay phrase used frequently in older consumer queries; must link to cholesterol and plaque buildup content |
| poor circulation | peripheral arterial disease (PAD) or chronic venous insufficiency | Vague consumer term covering multiple diagnoses; system should present differential possibilities rather than a single match |

## Common Query Patterns
- Symptom narrative ('my chest feels tight when I climb stairs') -> retrieve angina and exertional chest pain content, flag for urgent care recommendation if symptoms are new or worsening
- Number-based BP queries ('my blood pressure is 158 over 104, is that bad?') -> retrieve hypertension stage classification content and always recommend physician follow-up, especially if the user mentions stopping medication
- Color or appearance changes in limbs ('my feet turned red and swollen') -> retrieve peripheral vascular disease and edema content, apply urgency flag for bilateral color changes as possible circulatory emergency
- Palpitation or racing heart descriptions ('my heart beats really fast out of nowhere for no reason') -> retrieve content on arrhythmia, SVT, and anxiety-related tachycardia, noting that ECG is needed for diagnosis
- Chest pain conflated with digestion ('feels like burning in my chest, is it my heart or heartburn?') -> retrieve differential content for cardiac vs. GERD chest pain, and recommend evaluation to rule out cardiac cause before assuming GI origin

## Category-Specific Rules
- Always include an urgent care or emergency referral flag when a consumer describes new, sudden, or severe chest pain, jaw pain, left arm pain, or loss of consciousness, regardless of whether a cardiac cause is confirmed in the query.
- Never dismiss cardiovascular symptoms solely because the user is young or reports a normal pulse; the sample data shows that even 13-year-olds with chest pain require ECG and echo to rule out heart disease before attributing symptoms to other causes.
- When a consumer mentions stopping prescribed heart or blood pressure medication, the response must explicitly note the risk of rebound hypertension or decompensation and strongly recommend resuming care under physician supervision.
- Leg swelling, color changes, or limb heaviness queries must trigger retrieval of both cardiac (heart failure, edema) and vascular (PAD, DVT) content, since these symptoms overlap significantly and misclassification has serious consequences.
- Blood pressure numbers provided by consumers should always be contextualized against standard hypertension staging (normal, elevated, Stage 1, Stage 2, hypertensive crisis) so the consumer understands severity, and the response must not suggest self-management without physician involvement.

## Known Pitfalls
- Attributing chest pressure or heaviness to GERD or anxiety without first recommending cardiac evaluation; the sample data shows doctors frequently suggest GERD as a cause, but this must only follow ruling out cardiac origin, not precede it.
- Treating bilateral leg swelling with color changes as a routine postural edema question; the sample data includes a case where feet were red and swollen bilaterally, which can indicate a vascular emergency requiring immediate attention.
- Assuming palpitations and fast heart rate are always anxiety-related in young or otherwise healthy-seeming consumers; the data shows these can be SVT or other arrhythmias requiring ECG diagnosis, not just reassurance.
- Conflating cervical or musculoskeletal pain queries with cardiovascular content simply because they appear in this category; the sample data contains off-topic entries (cervical pain, miscarriage) that represent labeling noise and should not anchor cardiovascular retrieval logic.

## Dominant Explanation Style
The TIER_A explanations follow a reassurance-first, differential-diagnosis pattern where the most common or benign cause is named first before escalating to more serious possibilities, consistently ending with a recommendation for a specific diagnostic test (ECG, MRI, blood work) or specialist referral. Explanations are written in plain, conversational language that acknowledges the consumer's concern before providing a structured clinical rationale.

