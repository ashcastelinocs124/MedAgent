<!-- STATUS: DRAFT -- awaiting human review -->

# Healthcare Knowledge Directory

Master index of all consumer-facing health categories derived from
MedMCQA (194k medical MCQs) and PubMedQA (273k biomedical research QA).

## Categories

| # | Category | Total | MedMCQA | PubMedQA | Quality Tier A% | File |
|---|----------|-------|---------|----------|-----------------|------|
| 1 | Digestive System & Liver | 27,598 | 13,688 | 68 | 28% | [digestive_liver.md](categories/digestive_liver.md) |
| 2 | Infections & Infectious Disease | 24,830 | 12,044 | 43 | 26% | [infections.md](categories/infections.md) |
| 3 | Bones, Joints & Muscles | 24,562 | 13,469 | 67 | 22% | [bones_joints_muscles.md](categories/bones_joints_muscles.md) |
| 4 | Public Health & Prevention | 24,496 | 11,972 | 10 | 38% | [public_health_prevention.md](categories/public_health_prevention.md) |
| 5 | Heart & Blood Vessels | 24,439 | 12,697 | 87 | 22% | [heart_blood_vessels.md](categories/heart_blood_vessels.md) |
| 6 | Hormones, Metabolism & Nutrition | 18,031 | 15,726 | 39 | 35% | [hormones_metabolism_nutrition.md](categories/hormones_metabolism_nutrition.md) |
| 7 | Medications & Drug Safety | 16,947 | 14,959 | 96 | 23% | [medications_drug_safety.md](categories/medications_drug_safety.md) |
| 8 | Blood & Immune Disorders | 14,858 | 11,288 | 15 | 29% | [blood_immune.md](categories/blood_immune.md) |
| 9 | Dental & Oral Health | 13,723 | 9,595 | 16 | 14% | [dental_oral.md](categories/dental_oral.md) |
| 10 | Children's Health | 12,452 | 9,292 | 148 | 35% | [childrens_health.md](categories/childrens_health.md) |
| 11 | Breathing & Lungs | 12,422 | 4,147 | 26 | 21% | [breathing_lungs.md](categories/breathing_lungs.md) |
| 12 | Brain & Nervous System | 12,172 | 4,379 | 41 | 34% | [brain_nervous_system.md](categories/brain_nervous_system.md) |
| 13 | Women's & Reproductive Health | 12,011 | 4,617 | 57 | 18% | [womens_reproductive.md](categories/womens_reproductive.md) |
| 14 | Ear, Nose & Throat | 11,584 | 9,760 | 33 | 34% | [ear_nose_throat.md](categories/ear_nose_throat.md) |
| 15 | Emergency & Critical Care | 11,427 | 8,101 | 32 | 24% | [emergency_critical_care.md](categories/emergency_critical_care.md) |
| 16 | Cancer | 11,174 | 5,706 | 135 | 30% | [cancer.md](categories/cancer.md) |
| 17 | Kidney & Urinary Health | 10,825 | 5,176 | 34 | 26% | [kidney_urinary.md](categories/kidney_urinary.md) |
| 18 | Skin & Dermatology | 10,208 | 2,923 | 10 | 18% | [skin_dermatology.md](categories/skin_dermatology.md) |
| 19 | Eye Health | 9,475 | 7,712 | 10 | 30% | [eye_health.md](categories/eye_health.md) |
| 20 | Mental Health | 8,633 | 5,071 | 33 | 14% | [mental_health.md](categories/mental_health.md) |

## Source Trust Hierarchy

1. **PubMedQA** -- peer-reviewed abstracts with structured evidence
2. **MedMCQA TIER_A** -- textbook-referenced explanations
3. **MedMCQA TIER_B** -- mechanism-based explanations
4. **MedMCQA TIER_C** -- answer-only, no reasoning
5. **MedMCQA TIER_D** -- question-answer pair only, no explanation

## Cross-Dataset Coverage Gaps

| Category | MedMCQA | PubMedQA | Gap |
|----------|---------|----------|-----|
| Blood & Immune Disorders | 11,288 | 15 | Low PubMedQA coverage |
| Bones, Joints & Muscles | 13,469 | 67 | Low PubMedQA coverage |
| Brain & Nervous System | 4,379 | 41 | Low PubMedQA coverage |
| Breathing & Lungs | 4,147 | 26 | Low PubMedQA coverage |
| Cancer | 5,706 | 135 | Low PubMedQA coverage |
| Children's Health | 9,292 | 148 | Low PubMedQA coverage |
| Dental & Oral Health | 9,595 | 16 | Low PubMedQA coverage |
| Digestive System & Liver | 13,688 | 68 | Low PubMedQA coverage |
| Ear, Nose & Throat | 9,760 | 33 | Low PubMedQA coverage |
| Emergency & Critical Care | 8,101 | 32 | Low PubMedQA coverage |
| Eye Health | 7,712 | 10 | Low PubMedQA coverage |
| Heart & Blood Vessels | 12,697 | 87 | Low PubMedQA coverage |
| Hormones, Metabolism & Nutrition | 15,726 | 39 | Low PubMedQA coverage |
| Infections & Infectious Disease | 12,044 | 43 | Low PubMedQA coverage |
| Kidney & Urinary Health | 5,176 | 34 | Low PubMedQA coverage |
| Medications & Drug Safety | 14,959 | 96 | Low PubMedQA coverage |
| Mental Health | 5,071 | 33 | Low PubMedQA coverage |
| Public Health & Prevention | 11,972 | 10 | Low PubMedQA coverage |
| Skin & Dermatology | 2,923 | 10 | Low PubMedQA coverage |
| Women's & Reproductive Health | 4,617 | 57 | Low PubMedQA coverage |
