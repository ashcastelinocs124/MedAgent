<!-- STATUS: DRAFT -- awaiting human review -->

# Blood & Immune Disorders

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 14,858 | MedMCQA: 11,288 | PubMedQA: 15 | MedQuAD: 489
- **Missing explanations**: 1,396 (9.4%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 4,279 | 29% |
| TIER_B | 7,073 | 48% |
| TIER_C | 1,431 | 10% |
| TIER_D | 2,075 | 14% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Pathology | 8,263 |
| Medicine | 1,348 |
| Microbiology | 778 |
| Gynaecology & Obstetrics | 213 |
| Anatomy | 208 |
| Surgery | 180 |
| Physiology | 143 |
| Unknown | 67 |
| Biochemistry | 56 |
| Radiology | 12 |

## Sample Questions

- [healthcaremagic_records] [TIER_C] Hi I was recommended by s gynecologist to have the marina coil fitted.  Due to me having non bleeding PCOS I got this fitted 5 month ago been experien...
- [healthcaremagic_records] [TIER_D] we had sex for the first time,n hymn broke n it started bleeding,v got scared n dint hv sex again,after having sex immediate next day i took meprate t...
- [healthcaremagic_records] [TIER_B] I have been on depo for over a year and no spotting/bleeding and this morning I had spotting not enough for a tampon but more than a normal spotting a...
- [healthcaremagic_records] [TIER_D] my husband was just informed that his hemoglobin was  72, and he must go to hospital tomorrow for a blood transfusiion.  He has prostate cancer, and h...
- [healthcaremagic_records] [TIER_C] i am a 63 year old woman, 5 feet 0 inches, weight 117 pounds who had a dental implant this morning. the tooth has been bleeding for about 8 hours, and...

## Links
<!-- Derived from secondary_category co-occurrence in 14,858 DB records -->
- **Strong links:**
  - [Cancer](cancer.md) — 562 cross-hits
  - [Women's & Reproductive Health](womens_reproductive.md) — 272 cross-hits
  - [Infections & Infectious Disease](infections.md) — 203 cross-hits
- **Weak links:**
  - [Dental & Oral Health](dental_oral.md) — 127 cross-hits
  - [Medications & Drug Safety](medications_drug_safety.md) — 113 cross-hits
  - [Skin & Dermatology](skin_dermatology.md) — 112 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Anemia & Iron Deficiency, Bleeding & Clotting Disorders, Autoimmune & Inflammatory Conditions, White Blood Cell Disorders, Platelet Disorders, Blood Cancers & Lymphoma, Transfusions & Blood Products, Immune Deficiency Conditions
- **Confidence:** High

## Source Priority
1. NIH MedlinePlus and National Heart Lung and Blood Institute (NHLBI)
2. Mayo Clinic and Cleveland Clinic hematology resources
3. American Society of Hematology (ASH) patient education materials
4. CDC disease-specific guidance for immune and blood conditions
5. WebMD and Healthline consumer summaries
**Rationale:** Hematology and immunology information requires precision around lab values, dosing thresholds, and disease mechanisms that are best covered by NHLBI and major academic medical centers. Consumer-facing materials from ASH provide lay-accessible explanations without sacrificing clinical accuracy.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| low blood | anemia / low hemoglobin | Consumers frequently say 'my blood is low' or give a single number like '7' referring to hemoglobin in g/dL; system must recognize this as anemia context |
| bruising easily | ecchymosis / thrombocytopenia / coagulopathy | Easy bruising is a common presenting complaint that can indicate platelet disorders, clotting factor deficiencies, or medication effects |
| low platelets | thrombocytopenia | Consumers rarely use the medical term; system should map any mention of 'low platelet count' to thrombocytopenia pathways |
| immune system attacking itself | autoimmune disease (e.g., SLE, ITP) | Lay description of autoimmunity is commonly used; important for routing SLE, lupus, and related queries correctly |
| blood clot | thrombosis / deep vein thrombosis / pulmonary embolism | Consumers use 'blood clot' broadly; system should clarify location (leg, lung, etc.) to differentiate DVT from PE |
| weak immune system | immunodeficiency / immunosuppression | Often used by consumers post-chemotherapy, post-transplant, or with HIV; context determines whether primary or secondary immunodeficiency |
| iron pills not working | refractory iron deficiency anemia / malabsorption | As seen in sample data, consumers report ongoing symptoms despite supplements; may indicate underlying cause needing further workup |
| blood count results | complete blood count (CBC) | Consumers share raw CBC values (RBC, WBC, hemoglobin, hematocrit) without knowing terminology; system must parse numeric lab values in context |

## Common Query Patterns
- Consumer shares a single lab number like 'my blood is a 7' -> interpret as hemoglobin level in g/dL, flag if below normal range, and explain anemia in plain language with urgency guidance
- Consumer describes bruising, numbness, or swelling after an injury -> assess for signs of internal bleeding or hematoma, recommend in-person evaluation, and note any red flags like increasing pain or inability to bear weight
- Consumer asks why symptoms persist despite taking iron supplements -> explain possible causes such as malabsorption, wrong type of iron, or an underlying condition, and recommend follow-up with a doctor
- Consumer shares full CBC result with medical terms they do not understand -> translate each flagged value into plain language, explain what low or high values may indicate, and emphasize that interpretation requires a clinician
- Consumer describes a chronic condition like lupus or SLE alongside a new symptom -> acknowledge the autoimmune context, explain how SLE can affect multiple organ systems, and strongly recommend consulting the treating specialist

## Category-Specific Rules
- Always flag hemoglobin values below 8 g/dL or platelet counts below 50,000/µL as requiring urgent medical evaluation, and never suggest home management alone for these thresholds.
- When a consumer shares CBC or blood panel results, translate every flagged abnormal value into plain language before offering any interpretation, and always note that final diagnosis requires a licensed clinician.
- For queries involving both bleeding symptoms and recent surgery or trauma (as in hip replacement or crush injury cases), cross-reference with Infections & Infectious Disease and Cancer categories before returning results, since differential diagnosis spans multiple domains.
- Do not conflate types of anemia: iron deficiency anemia, anemia of chronic disease, and hemolytic anemia have different causes and treatments; always ask clarifying questions about lab context before explaining management.
- When autoimmune conditions like SLE or ITP are mentioned, acknowledge that these diseases are unpredictable and multi-systemic, and direct consumers to their rheumatologist or hematologist rather than offering condition management advice.

## Known Pitfalls
- Assuming 'low blood' always means iron deficiency anemia: as shown in the sample data, low hemoglobin can result from bleeding (GI bleed, trauma), infection-related thrombocytopenia, or chronic disease, so the system must not default to iron supplementation advice without context.
- Treating hypochromia on a blood smear as equivalent to low serum iron: the sample data shows a case where iron was 135 but hypochromia was still present, which can occur in thalassemia or early deficiency; the system must not oversimplify the relationship.
- Conflating vaginal bleeding or itching queries as purely gynecological when they appear in this category: the sample data includes such a case where infection (yeast/STI) was the root cause affecting immune response; cross-category routing to Women's & Reproductive Health is essential.
- Underestimating the complexity of pediatric platelet disorders: the infant thrombocytopenia case in the sample data shows that low platelet counts in newborns may resolve but require ongoing monitoring; the system must not reassure caregivers prematurely without noting follow-up requirements.

## Dominant Explanation Style
TIER_A responses in this category follow a structured clinical consultation format: they briefly validate the consumer's concern, offer a ranked differential diagnosis in accessible language, and close with a specific action step (consult a specialist, get a particular test, or monitor a specific symptom). Explanations tend to be direct and semi-technical, assuming the consumer can handle medical terminology if it is briefly defined.

