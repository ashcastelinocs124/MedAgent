<!-- STATUS: DRAFT -- awaiting human review -->

# Ear, Nose & Throat

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 11,584 | MedMCQA: 9,760 | PubMedQA: 33 | MedQuAD: 1,033
- **Missing explanations**: 952 (8.2%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 3,992 | 34% |
| TIER_B | 5,945 | 51% |
| TIER_C | 505 | 4% |
| TIER_D | 1,142 | 10% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| ENT | 4,902 |
| Surgery | 605 |
| Anatomy | 600 |
| Pathology | 595 |
| Forensic Medicine | 547 |
| Radiology | 517 |
| Anaesthesia | 464 |
| Medicine | 425 |
| Gynaecology & Obstetrics | 409 |
| Microbiology | 263 |

## Sample Questions

- [healthcaremagic_records] [TIER_D] i have had a cold now for 12 weeks, will not go have been to the doctors was given a course of tablets about three weeks ago, which did not work. have...
- [healthcaremagic_records] [TIER_B] Hi, I recently had a cavity filled on the upper left part of my mouth. Its been two days since the procedure, and I still have sever pain and tenderne...
- [healthcaremagic_records] [TIER_B] hi. i am nadeem from nagpur. age 42 yrs. i have prob of cold regularly. its allergic i think. when i come in contact with air flow like sitting under ...
- [healthcaremagic_records] [TIER_B] My son has a metabolic condition that is currently in the process of being diagnosed. He has a high ratio of sterified to free carnintine. He is on L-...
- [healthcaremagic_records] [TIER_D] My 5 year old son has had a high temp 38.5, swollen glands behind his ears, white around his tonsilies, face is puffy and red and he also has a lump a...

## Links
<!-- Derived from secondary_category co-occurrence in 11,584 DB records -->
- **Strong links:**
  - [Cancer](cancer.md) — 433 cross-hits
  - [Infections & Infectious Disease](infections.md) — 213 cross-hits
  - [Children's Health](childrens_health.md) — 204 cross-hits
- **Weak links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 141 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 137 cross-hits
  - [Dental & Oral Health](dental_oral.md) — 110 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Sore Throat & Tonsils, Sinusitis & Nasal Congestion, Ear Infections & Ear Pain, Hearing Loss & Tinnitus, Allergies & Hay Fever, Wisdom Teeth & Throat Symptoms, Lymph Node Swelling, Voice & Larynx Disorders, Mouth Sores & Oral Lesions, Pediatric ENT Conditions
- **Confidence:** High

## Source Priority
1. American Academy of Otolaryngology - Head and Neck Surgery (AAO-HNS)
2. Mayo Clinic ENT and Allergy sections
3. CDC respiratory illness and infection guidelines
4. MedlinePlus ENT condition pages
5. WebMD and Healthline ENT articles
**Rationale:** AAO-HNS and Mayo Clinic provide specialist-reviewed, evidence-based ENT guidance most aligned with clinical accuracy for consumer queries. CDC guidelines add authority for infectious ENT conditions which represent the strongest cross-category overlap in this dataset.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| runny nose | rhinorrhea | Extremely common search term; consumers rarely use rhinorrhea and may not recognize it in results |
| sore throat | pharyngitis | High-frequency query term; must map correctly to distinguish viral vs bacterial causes |
| swollen glands | lymphadenopathy | Consumers consistently say 'swollen glands' when referring to enlarged cervical lymph nodes; critical for triage toward cancer or infection flags |
| ear infection | otitis media or otitis externa | Consumers do not distinguish middle vs outer ear infections; clarification affects treatment guidance significantly |
| phlegm dripping down throat | post-nasal drip | Very common descriptive phrase; maps to post-nasal drip and chronic rhinosinusitis contexts |
| stuffy nose | nasal congestion or nasal obstruction | Common symptom query that may indicate allergy, sinusitis, or structural issues like deviated septum |
| snoring loudly | stertor or obstructive sleep apnea symptoms | Consumers describe snoring without awareness of sleep apnea risk; important to flag for further evaluation |
| white patches in throat | tonsillar exudate or oral candidiasis | Consumers often describe this visually; must be mapped carefully as it overlaps with strep, mono, and fungal infection |

## Common Query Patterns
- Symptom cluster questions like 'I have sore throat, ear pain, and swollen glands' -> retrieve multi-symptom differential guidance, flag if symptoms exceed 2 weeks or include unilateral swelling
- Parent queries about infant or child ENT symptoms like 'my 11 month old has green runny nose' -> prioritize pediatric ENT sources, recommend in-person evaluation for infants under 12 months
- Questions linking dental or oral symptoms to ENT like 'can my wisdom tooth cause sore throat' -> address anatomical proximity explanation and advise dual consultation with dentist and ENT
- OTC medication combination questions like 'can I take Reactine and Benylin together' -> redirect to pharmacist consultation, avoid specific dosing advice, note drug interaction risks
- Persistent or unusual symptom questions like 'I have had a swollen lymph node for 3 months' -> escalate to urgent evaluation flag, surface cancer cross-category content, avoid reassuring language that delays care

## Category-Specific Rules
- Always flag unilateral symptoms (one-sided swollen tonsil, one-sided lymph node, one-sided ear pain persisting over 3 weeks) as requiring in-person ENT evaluation due to elevated cancer risk in this category
- Never provide specific antibiotic names or dosages; when antibiotics are mentioned in retrieved content, append a reminder that prescription decisions require a clinician
- For pediatric ENT queries involving infants under 12 months, always recommend prompt medical consultation regardless of symptom severity, as sample data shows these cases often have underlying infections requiring professional assessment
- Distinguish between allergic and infectious causes of nasal and throat symptoms in retrieved content, as treatment paths differ significantly and consumers frequently conflate the two
- When a query involves symptoms lasting more than 3 months (chronic), prioritize content about chronic conditions like chronic rhinosinusitis or persistent lymphadenopathy and explicitly recommend specialist referral rather than home treatment

## Known Pitfalls
- Conflating runny nose with sinus infection: sample data shows runny nose in children is frequently rhinitis or residual URI, not sinusitis; agents must not default to sinus infection framing without supporting symptom evidence
- Assuming mouth sores or white patches are always viral: sample data includes herpes, candidiasis, and dermatitis as possibilities; agents must avoid anchoring on a single diagnosis and should surface differential options
- Dismissing the dental-ENT connection: agents may overlook that wisdom tooth inflammation can genuinely cause throat pain due to anatomical proximity, leading to incomplete or misleading responses on oral-ENT crossover queries
- Over-reassuring parents about pediatric symptoms: sample data shows bad breath plus runny nose in an infant was linked to enterocolitis; agents must not minimize multi-symptom infant presentations even when individual symptoms seem mild

## Dominant Explanation Style
TIER_A responses follow a direct clinical consultation style, opening with acknowledgment of the query, linking the reported symptom to a probable condition with brief mechanistic reasoning, and closing with a conservative recommendation to seek professional evaluation. Explanations are concise and semi-formal, aimed at informing without overwhelming the consumer.

