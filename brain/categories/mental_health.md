<!-- STATUS: DRAFT -- awaiting human review -->

# Mental Health

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 8,633 | MedMCQA: 5,071 | PubMedQA: 33 | MedQuAD: 29
- **Missing explanations**: 192 (2.2%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 1,176 | 14% |
| TIER_B | 4,914 | 57% |
| TIER_C | 1,646 | 19% |
| TIER_D | 897 | 10% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Psychiatry | 4,430 |
| Anatomy | 220 |
| Pharmacology | 162 |
| Forensic Medicine | 108 |
| Medicine | 60 |
| Unknown | 18 |
| Anaesthesia | 16 |
| Microbiology | 16 |
| Pathology | 13 |
| Physiology | 12 |

## Sample Questions

- [healthcaremagic_records] [TIER_C] Dear! I Want to conceive 2nd baby for that Dr gv Prolifen after 1month I got my periods which didnt stop till 18 days dn Dr gv Primlut N....now period...
- [healthcaremagic_records] [TIER_D] what is the prognosis of bipolar depression when detected in a young individual say at 2o yrs.?Whether the individual can focus on study during treatm...
- [healthcaremagic_records] [TIER_A] i feel like there an earthquake in my chest/throat area... i dont know what it is..been going on for a couple years now an happens a few times a month...
- [healthcaremagic_records] [TIER_B] I am frozen by my fears..i feel that I cannot do anything at all. I have been suppressed all my life and controlled. Now I am incapable of doing more ...
- [healthcaremagic_records] [TIER_A] i m suffuring from depression and pannic attack, i m taking etizola plus 10 mg and etizola .5 since last 20 days, in one whole day in evening i feel l...

## Links
<!-- Derived from secondary_category co-occurrence in 8,633 DB records -->
- **Strong links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 709 cross-hits
  - [Ear, Nose & Throat](ear_nose_throat.md) — 455 cross-hits
  - [Brain & Nervous System](brain_nervous_system.md) — 254 cross-hits
- **Weak links:**
  - [Heart & Blood Vessels](heart_blood_vessels.md) — 245 cross-hits
  - [Children's Health](childrens_health.md) — 193 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 177 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Anxiety & Panic Disorders, Depression, Bipolar Disorder, Stress & Burnout, Sleep Disorders & Insomnia, Trauma & PTSD, OCD & Intrusive Thoughts, Suicidal Ideation & Crisis Support, Mood Disorders, Medication & Treatment Questions
- **Confidence:** High

## Source Priority
1. National Institute of Mental Health (NIMH)
2. Mayo Clinic Mental Health
3. American Psychological Association (APA)
4. MedlinePlus Mental Health
5. WebMD Mental Health
**Rationale:** NIMH and APA provide evidence-based, clinically reviewed information on mental health conditions and treatments, minimizing stigma and misinformation. Consumer-facing portals like MedlinePlus bridge clinical accuracy with accessible language appropriate for everyday users.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| nervous breakdown | acute mental health crisis or major depressive episode | consumers often use this to describe overwhelming psychological distress; should be mapped to appropriate clinical framing |
| panic attack | panic disorder episode | commonly searched; consumers may confuse with heart attack symptoms, which is a documented pattern in the sample data |
| feeling hopeless or empty | depressive symptoms | consumers rarely self-identify as 'depressed'; these descriptive phrases are the actual search triggers |
| mood swings | affective lability or bipolar disorder | broad term that could indicate multiple conditions; requires careful triage toward appropriate subcategory |
| can't stop worrying | generalized anxiety disorder (GAD) | very common lay phrasing that corresponds to clinical GAD criteria |
| feeling detached or not real | depersonalization or derealization disorder | consumers rarely know clinical terms; descriptive language must trigger relevant results |
| want to hurt myself | suicidal ideation or self-harm | must trigger immediate crisis resource prioritization before any informational content |
| nervous stomach or chest tightness | somatic symptoms of anxiety | as seen in sample data, physical sensations are often the entry point for mental health queries |

## Common Query Patterns
- vague physical symptoms with emotional context (e.g., 'earthquake in my chest and feel like choking') -> cross-reference Brain & Nervous System and Medications categories; surface anxiety/panic disorder content alongside physical cause explanations
- named medication questions (e.g., 'I am taking etizolam and escitalopram, is this normal?') -> retrieve from Medications & Drug Safety cross-category; explain mechanism in plain language and recommend consulting prescriber
- crisis or suicidal language (e.g., 'I tried suicide twice') -> immediately surface crisis hotline resources (988 Suicide & Crisis Lifeline) before any other content; do not delay to match informational records
- life-event-triggered distress (e.g., 'I am going through a divorce and having panic attacks') -> validate emotional context first, then retrieve relevant anxiety/stress subcategory content; avoid purely clinical framing
- chronic illness with mental health overlap (e.g., 'I have chronic Lyme and also depression') -> retrieve co-occurring condition content and flag that mental symptoms may be secondary to physical illness; recommend physician consultation

## Category-Specific Rules
- Any query containing language suggesting suicidal ideation, self-harm, or active crisis must surface the 988 Suicide & Crisis Lifeline and/or emergency resources as the first result, before any knowledge base content is returned.
- Never present medication names, dosages, or drug combinations as recommendations — always frame them as 'your doctor may have prescribed this because...' and direct users to consult their prescriber or pharmacist.
- When physical symptoms (chest tightness, throat sensations, breathing difficulty) co-occur with emotional distress language, retrieve content from both Mental Health and the relevant physical category (e.g., Brain & Nervous System, Ear Nose & Throat) to avoid missing organic causes.
- Avoid language that minimizes mental health conditions — the sample data contains the phrase 'depression is not a disease, it is a disorder' which is clinically contested and stigmatizing; verified sources must reflect current clinical consensus that depression is a treatable medical condition.
- For queries involving minors (under 18), flag the response for age-appropriate framing and, where relevant, include guidance for parents or guardians alongside content directed at the young person.

## Known Pitfalls
- Conflating panic attack symptoms with heart attack: sample data shows consumers frequently describe chest pain and breathing difficulty in mental health queries — agents must not dismiss cardiac causes and should recommend ruling out physical causes when symptoms are ambiguous.
- Over-relying on medication explanations without safety context: sample data includes specific benzodiazepine combinations (etizolam) that carry dependency risks; agents must not retrieve dosage guidance without pairing it with safety and consultation warnings.
- Missing suicidal content in heavily descriptive queries: the sample includes a user describing two suicide attempts embedded in a complaint about smell sensitivity — agents must scan full query text for crisis signals, not just opening phrases.
- Treating mental and physical symptoms as mutually exclusive: multiple sample records show patients with thyroid issues, Lyme disease, and vitamin deficiencies presenting with mental health symptoms — agents must not route purely to Mental Health subcategories when comorbid physical conditions are mentioned.

## Dominant Explanation Style
TIER_A responses follow a reassurance-first, then clinical-explanation pattern, typically acknowledging the consumer's distress before offering a probable diagnosis and next steps. Explanations are moderately technical but consumer-directed, frequently recommending in-person consultation and combining lifestyle, medication, and investigative advice in a single response.

