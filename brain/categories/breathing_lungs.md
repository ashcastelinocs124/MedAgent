<!-- STATUS: DRAFT -- awaiting human review -->

# Breathing & Lungs

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 12,422 | MedMCQA: 4,147 | PubMedQA: 26 | MedQuAD: 182
- **Missing explanations**: 367 (3.0%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 2,551 | 21% |
| TIER_B | 6,382 | 51% |
| TIER_C | 1,099 | 9% |
| TIER_D | 2,390 | 19% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Medicine | 1,250 |
| Physiology | 632 |
| Pathology | 496 |
| Radiology | 321 |
| Anatomy | 292 |
| Microbiology | 262 |
| Surgery | 242 |
| Biochemistry | 228 |
| Pharmacology | 178 |
| Unknown | 83 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] Yes, I first felt a lump pea size on tight side of neck. Went to doctor and he gave me antbiotics but did not help. Next were xrays and cat scans and ...
- [healthcaremagic_records] [TIER_B] Hi, I am XXXXXXX. I regularly suffer from cold, cough , mouth alcer and some allergy problem.I am taking Bio C for the past 1 month. I don t see much ...
- [healthcaremagic_records] [TIER_B] My children and husband all had upper respertory infection that lasted about a week. I got it a week ago and just as I thought I was recovering I can ...
- [healthcaremagic_records] [TIER_D] First of all thanks for your gesture in providing this query facility. Kindly enlighten why we get cold and cough when ever weather changes from hot t...
- [healthcaremagic_records] [TIER_B] Yesterday I started 500 mg twice a day of clarithromycin for bronchitis and sinusitis. last night I received a deep cat bite from a stray himilayan. m...

## Links
<!-- Derived from secondary_category co-occurrence in 12,422 DB records -->
- **Strong links:**
  - [Infections & Infectious Disease](infections.md) — 1,843 cross-hits
  - [Cancer](cancer.md) — 974 cross-hits
  - [Medications & Drug Safety](medications_drug_safety.md) — 352 cross-hits
- **Weak links:**
  - [Heart & Blood Vessels](heart_blood_vessels.md) — 297 cross-hits
  - [Emergency & Critical Care](emergency_critical_care.md) — 267 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 258 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Asthma & Bronchospasm, Infections & Bronchitis, COPD & Emphysema, Pleural Conditions, Tuberculosis & Chronic Lung Disease, Pediatric Respiratory Issues, Lung Cancer & Nodules, Sleep Apnea & Breathing Disorders, Medications & Inhalers, Structural & Anatomical Conditions
- **Confidence:** High

## Source Priority
1. CDC and NIH respiratory disease guidelines (most trusted)
2. American Lung Association patient education resources
3. Mayo Clinic and Cleveland Clinic clinical explainers
4. Peer-reviewed pulmonology journals (e.g. Chest, Thorax) summarized for consumers
5. General health Q&A platforms and forums (least trusted)
**Rationale:** Respiratory conditions range from common infections to life-threatening emergencies, so guideline-backed sources from CDC, NIH, and major clinical institutions ensure accuracy on diagnosis, treatment, and medication safety. Consumer-facing resources from the American Lung Association bridge technical accuracy with plain-language accessibility appropriate for everyday users.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| chest infection | lower respiratory tract infection / pneumonia / bronchitis | Consumers use 'chest infection' broadly; agents must clarify whether bacterial or viral origin is implied and prompt for symptom duration |
| collapsed lung | pneumothorax / atelectasis | Consumers conflate these two distinct conditions; pneumothorax is acute air leakage, atelectasis is partial lung collapse from obstruction |
| fluid on the lungs | pleural effusion / pulmonary edema | Pleural effusion is fluid around the lung, pulmonary edema is fluid inside lung tissue — very different causes and treatments |
| wheezing / tight chest | bronchospasm / airway obstruction | Common asthma descriptors; agents should flag worsening wheezing as a potential emergency if paired with inhaler non-response |
| coughing up blood | hemoptysis | Always a red-flag symptom; sample data shows it can be trivialized as pharyngitis but TB, cancer, and PE must be excluded |
| pigeon chest | pectus carinatum | Structural deformity often co-occurring with chronic respiratory issues; consumers may not know the medical name |
| water in lungs | pleural effusion / pulmonary edema | Lay phrase used interchangeably for both conditions; context clues like heart disease vs. infection help differentiate |
| breathing treatment / nebulizer | nebulized bronchodilator therapy (e.g. albuterol, ipratropium) | Consumers describe the device not the drug; agents should map this to specific medication classes when recommending follow-up questions |

## Common Query Patterns
- Symptom-duration queries ('cough for 2 weeks that won't go away') -> triage by red-flag symptoms (blood, weight loss, fever), then recommend clinical evaluation and flag possible TB or pneumonia overlap
- Medication-mechanism questions ('why do I take this inhaler for asthma') -> provide plain-language explanation of drug class (bronchodilator, corticosteroid, leukotriene inhibitor) with side-effect summary and avoid endorsing specific brands
- Pediatric respiratory concerns ('my child keeps getting colds and coughs') -> assess frequency and pattern, mention adenoid/tonsil issues as per sample data, recommend pediatric consult rather than self-treatment
- Post-injury or structural chest questions ('I hurt my ribs and now have trouble breathing') -> check for pneumothorax indicators, distinguish floating rib anatomy from pathology, advise imaging and urgent care if breathing is compromised
- Inhaler not working queries ('my inhaler makes breathing worse') -> flag as a safety concern, explain possible paradoxical bronchospasm or incorrect inhaler technique, recommend immediate medical contact if acute distress present

## Category-Specific Rules
- Always screen for red-flag symptoms — hemoptysis, unexplained weight loss, night sweats, and prolonged cough over 3 weeks — before providing general respiratory advice, and escalate these to urgent medical referral.
- When a consumer asks about a respiratory medication (inhaler, bronchodilator, steroid), explain the mechanism in plain language and note common side effects, but do not recommend specific dosages or substitute one drug for another.
- Distinguish pediatric respiratory queries from adult queries explicitly, as normal anatomy (e.g. enlarged adenoids), symptom thresholds, and appropriate treatments differ significantly for children under 12.
- For any question involving coughing up blood, chest drainage, or suspected pleural conditions (effusion, empyema, pneumothorax), always recommend in-person evaluation and do not suggest home management as sufficient.
- When tuberculosis is mentioned or plausible (long-duration cough, immigration context, immunocompromised status), flag the need for sputum testing and chest imaging before offering any other guidance, and note the mandatory multi-drug regimen requirement.

## Known Pitfalls
- Underestimating hemoptysis: sample data shows agents may attribute coughing up blood to minor pharyngitis; agents must always treat this as a potential red-flag requiring exclusion of TB, lung cancer, and pulmonary embolism before reassuring the consumer.
- Conflating empyema with emphysema: the sample data contains this exact confusion ('emphysema' used when 'empyema' is meant); agents must verify the specific diagnosis term and not mix up these two distinct conditions in responses.
- Assuming an inhaler making symptoms worse is user error alone: paradoxical bronchospasm is a real adverse reaction, and dismissing worsening symptoms post-inhaler use as technique failure could delay care for a deteriorating asthma episode.
- Treating prolonged pediatric cold/cough as routine without flagging structural causes: sample data shows adenoid enlargement and recurrent infections are linked; agents should not default to generic cold advice for children with multi-week or recurrent respiratory symptoms.

## Dominant Explanation Style
TIER_A responses in this category follow a symptom-acknowledgment then mechanistic-explanation pattern, briefly validating the consumer's concern before naming likely diagnoses and linking them to physiological causes. Explanations then pivot to actionable next steps — specific tests (chest X-ray, sputum culture), drug classes with named examples, and referral recommendations — keeping clinical detail present but embedded in practical guidance.

