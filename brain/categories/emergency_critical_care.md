<!-- STATUS: DRAFT -- awaiting human review -->

# Emergency & Critical Care

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 11,427 | MedMCQA: 8,101 | PubMedQA: 32 | MedQuAD: 180
- **Missing explanations**: 465 (4.1%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 2,737 | 24% |
| TIER_B | 5,307 | 46% |
| TIER_C | 2,216 | 19% |
| TIER_D | 1,167 | 10% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Forensic Medicine | 4,108 |
| Anaesthesia | 1,789 |
| Surgery | 919 |
| Pharmacology | 408 |
| Anatomy | 229 |
| Medicine | 205 |
| Microbiology | 103 |
| Pathology | 95 |
| Unknown | 62 |
| Gynaecology & Obstetrics | 60 |

## Sample Questions

- [healthcaremagic_records] [TIER_C] my neck is very stiff. it appears a knot above collar bone, back side. its painful,have trouble sleeping. when i try to massage it, a small sharp shoc...
- [healthcaremagic_records] [TIER_D] Good day,today I experienced a strange feeling ,my right arm became lame ! I was unable to open the car door with my right arm , I raised my arm to my...
- [healthcaremagic_records] [TIER_C] Hello Dr, I am a 39 year old female I am 52 and weight 112 I was told I have a follicular cyst few months ago. Recently I had another ultrasound done ...
- [healthcaremagic_records] [TIER_C] i m 29 yrs old , my husband is 34 yrs old . we got marriage before 9 months , i went to doctor before 6 months for getting pregant . she gave tablets ...
- [healthcaremagic_records] [TIER_B] I was asleep then i woke up with a fast heartbest and throwing up. It lastes for 5 minutes now my heart is normal. I dont smoke and i only drink water...

## Links
<!-- Derived from secondary_category co-occurrence in 11,427 DB records -->
- **Strong links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 438 cross-hits
  - [Dental & Oral Health](dental_oral.md) — 132 cross-hits
  - [Cancer](cancer.md) — 91 cross-hits
- **Weak links:**
  - [Heart & Blood Vessels](heart_blood_vessels.md) — 75 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 61 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 56 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Traumatic Injuries & Falls, Lumps & Swellings, Nerve Pain & Sensory Symptoms, Oral & Tongue Emergencies, Post-Procedure Complications, Head & Facial Injuries, Unexplained Pain & Tenderness, Tremors & Neurological Symptoms
- **Confidence:** High

## Source Priority
1. Emergency medicine clinical guidelines (ACEP, UpToDate)
2. NIH MedlinePlus emergency and first aid pages
3. Mayo Clinic emergency symptoms and triage guides
4. WebMD symptom checker with physician-reviewed content
5. Community health forums with physician-moderated responses
**Rationale:** Emergency and critical care queries often involve symptoms that may indicate serious underlying conditions, so clinically validated triage guidelines and physician-reviewed content must take precedence over general wellness sources. Misinformation in this category carries higher patient safety risk than in most other categories.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| golf ball lump | hematoma or post-injection mass | consumers describe swelling by size and shape rather than clinical terms after procedures |
| burning tongue | glossitis or burning mouth syndrome | very common lay description that maps to multiple distinct diagnoses requiring differentiation |
| nerve burning procedure | radiofrequency ablation or nerve block injection | consumers rarely know the clinical name of interventional pain procedures |
| lightheaded after hitting nose | vasovagal response or concussion symptom | head trauma symptoms are often minimized by consumers; lightheadedness post-impact needs triage |
| tremor or shocking feeling in foot | fasciculation or peripheral nerve irritation | consumers describe neurological symptoms in sensory metaphors like electric shock |
| lump on butt cheek | subcutaneous abscess, epidermoid cyst, or infected follicle | anatomical imprecision is common; location and duration help differentiate benign from urgent |
| white sores on tongue | aphthous ulcers or oral candidiasis | consumers conflate canker sores with fungal infections; treatment differs significantly |
| tender ankle after fall | ligament sprain, tendinitis, or stress fracture | ability to bear weight is a key triage factor consumers mention but may not recognize as clinically significant |

## Common Query Patterns
- Consumer describes a new lump or swelling after a procedure -> system should flag potential post-procedural complication, recommend contacting the treating provider urgently, and explain red-flag signs like rapid growth, fever, or numbness
- Consumer describes burning or sore tongue lasting more than a week -> system should present differential (vitamin deficiency, candida, aphthous ulcer, contact irritant) and recommend dental or medical evaluation if not resolving
- Consumer describes fall with pain and swelling but can still walk -> system should explain that weight-bearing does not rule out fracture or tendon injury and recommend X-ray evaluation within 24-48 hours
- Consumer asks about a recurring tremor or electric-shock sensation in a limb -> system should emphasize the need for a neuromuscular evaluation, avoid speculating on ALS or MS without clinical context, and describe what the assessment involves
- Consumer reports head or facial impact with subsequent dizziness or headache -> system should apply concussion triage logic, list red-flag escalation symptoms (loss of consciousness, worsening headache, vomiting), and advise seeking care

## Category-Specific Rules
- Always apply a triage layer first: before explaining a condition, assess whether the described symptoms (sudden neurological changes, rapid swelling post-procedure, post-trauma dizziness) warrant immediate ER referral.
- Never reassure a consumer that a post-procedure complication is normal without explicitly noting that the treating provider must be contacted, since procedural adverse events require professional follow-up.
- When multiple diagnoses are plausible for a lump or swelling, list them in order from most benign to most urgent and clearly state which symptoms would push the situation toward the urgent end.
- For any head or facial trauma query, always include a checklist of concussion red-flag symptoms (worsening headache, repeated vomiting, confusion, unequal pupils) regardless of how mild the consumer describes the impact.
- Cross-reference with Medications & Drug Safety when a consumer describes worsening symptoms after a medical procedure or medication, since drug reactions and procedural complications frequently overlap in this category.

## Known Pitfalls
- Assuming a lump is benign because it is not growing rapidly: the sample data shows consumers often wait days or weeks before asking, by which time an abscess or hematoma may already be progressing.
- Treating all tongue burning or soreness as a single condition: the sample data reveals that candidiasis, aphthous ulcers, vitamin deficiency, and contact dermatitis all present similarly but require different treatments.
- Underweighting post-procedure complications: consumers may describe significant adverse events (e.g., worsened pain and swelling after a nerve ablation) in vague terms, and the system must not default to reassurance without flagging the need for provider contact.
- Conflating ability to bear weight after a fall with absence of serious injury: sample data shows consumers self-triage based on weight-bearing, but tendinitis, stress fractures, and ligament tears can all coexist with preserved ambulation.

## Dominant Explanation Style
TIER_A responses in this category follow a structured triage-then-explain pattern: they acknowledge the consumer's concern, offer 2-3 differential diagnoses ranked by likelihood, and close with a specific clinical action (imaging, specialist referral, or ER visit). Responses are directive and safety-first rather than exploratory or reassuring.

