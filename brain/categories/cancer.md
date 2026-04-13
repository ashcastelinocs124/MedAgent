<!-- STATUS: DRAFT -- awaiting human review -->

# Cancer

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 11,174 | MedMCQA: 5,706 | PubMedQA: 135 | MedQuAD: 1,134
- **Missing explanations**: 584 (5.2%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 3,300 | 30% |
| TIER_B | 5,014 | 45% |
| TIER_C | 1,278 | 11% |
| TIER_D | 1,582 | 14% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Surgery | 1,690 |
| Pathology | 1,333 |
| Gynaecology & Obstetrics | 829 |
| Pharmacology | 748 |
| Medicine | 432 |
| Radiology | 215 |
| Anatomy | 159 |
| Unknown | 135 |
| Microbiology | 69 |
| Biochemistry | 40 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] I have a lump and discomfort in my right arm pit . Mammogram and Scan show no likely breast cancer. I am booked to have an aspiration to withdraw tiss...
- [healthcaremagic_records] [TIER_B] I am an 87yr old lady and when I had to have my appendicitis out last summer a small cancer was found onn one of my kidney s i chose to leave it alone...
- [healthcaremagic_records] [TIER_D] Yes, thank you. I have a large mass under my neck. I had an ultrasound and was told that the lump had some connection to internal organs and I was sen...
- [healthcaremagic_records] [TIER_B] I have a mole that was damaged on my back, and it barley grew back and there is no sign of activity, I mean a layer of skin hasn t came back, it feels...
- [healthcaremagic_records] [TIER_B] Hi, I ve been chewing tobacco for probably about a year and a half now. And I do drink a fair bit, maybe twice a month. And I ve been getting cankers ...

## Links
<!-- Derived from secondary_category co-occurrence in 11,174 DB records -->
- **Strong links:**
  - [Medications & Drug Safety](medications_drug_safety.md) — 980 cross-hits
  - [Kidney & Urinary Health](kidney_urinary.md) — 433 cross-hits
  - [Digestive System & Liver](digestive_liver.md) — 271 cross-hits
- **Weak links:**
  - [Women's & Reproductive Health](womens_reproductive.md) — 250 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 229 cross-hits
  - [Infections & Infectious Disease](infections.md) — 219 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Breast Cancer, Skin & Oral Cancers, Lymphoma & Blood Cancers, Gynecologic Cancers, Gastrointestinal Cancers, Lung & Respiratory Cancers, Cancer Treatment & Side Effects, Benign Tumors & Cysts, Cancer Screening & Diagnosis, Cancer-Related Symptoms & Warning Signs
- **Confidence:** High

## Source Priority
1. National Cancer Institute (cancer.gov)
2. American Cancer Society (cancer.org)
3. Mayo Clinic cancer resources
4. Memorial Sloan Kettering Cancer Center patient education
5. General medical Q&A platforms (ChatDoctor, WebMD community)
**Rationale:** Cancer information requires high accuracy given patient anxiety and treatment stakes; NCI and ACS provide evidence-based, peer-reviewed content specifically designed for consumer audiences. General Q&A platforms are deprioritized because responses may conflate benign and malignant conditions or give overly reassuring answers without proper diagnostic context.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| lump | mass or nodule | Consumers frequently describe lumps in breast, neck, or armpit without knowing if benign or malignant; always prompt evaluation recommendation |
| cancer spot or dark spot | lesion or neoplasm | Consumers use vague visual descriptors for potential skin or oral cancers; mapping helps route to dermatology or oncology content |
| canker sore or mouth sore | oral lesion, leukoplakia, or erythroplakia | Consumers confuse benign canker sores with potentially pre-cancerous oral patches especially in tobacco users |
| swollen glands | lymphadenopathy | Very common consumer symptom that can indicate lymphoma, metastatic cancer, or simple infection; requires careful triage language |
| chemo | chemotherapy | Consumers use shorthand; ensure side effect and drug interaction content maps correctly to full chemotherapy regimens |
| non-cancerous tumor | benign neoplasm or benign tumor | Consumers often confused about distinction between benign and malignant; clear explanation reduces unnecessary panic |
| blood clot with cancer | cancer-associated thrombosis or hypercoagulable state | Consumers may not know cancer can cause clotting disorders; important cross-link to Kidney & Urinary and Medications content |
| biopsy results | histopathology or cytology report | Consumers searching after receiving FNAC or biopsy results need plain-language interpretation of terms like 'atypical' or 'hyperplasia' |

## Common Query Patterns
- Consumer describes a new lump or bump on the body -> system should retrieve content on when lumps require evaluation, red flag signs, and prompt a 'see a doctor' recommendation without confirming or denying cancer
- Consumer asks if a symptom 'could be cancer' -> system should acknowledge the concern, explain common benign causes first, then describe warning signs warranting clinical evaluation, always avoiding definitive diagnosis
- Consumer asks about side effects during or after chemotherapy or radiation -> system should retrieve treatment-specific side effect content and cross-reference Medications & Drug Safety category for drug interaction details
- Consumer shares a diagnosis (e.g. fibroadenosis, meningioma, complex cyst) and asks what it means -> system should explain the condition in plain language, clarify benign vs malignant distinction, and note follow-up care recommendations
- Consumer asks about elevated lab values (e.g. liver enzymes) in context of cancer treatment -> system should cross-reference Digestive System & Liver category and flag that lab interpretation requires a treating physician

## Category-Specific Rules
- Never confirm or rule out a cancer diagnosis based on symptom descriptions alone; always include a clear recommendation to seek in-person clinical evaluation for any lump, lesion, or unexplained symptom
- Distinguish clearly between benign conditions (fibroadenosis, lipoma, reactive lymph nodes) and malignant conditions in all responses; consumer confusion between these is common and high-stakes
- When tobacco or alcohol use is mentioned in the query context, always include relevant cancer risk information (oral cancer, lung cancer) without being alarmist, as this is a key prevention education opportunity
- For questions about abnormal lab values (liver enzymes, blood counts) in cancer patients, always note that results must be interpreted by the treating oncologist given the complex interaction of cancer, treatment, and comorbidities
- Cross-reference Medications & Drug Safety category for any query involving chemotherapy agents, hormonal therapies, or cancer-related anticoagulation to ensure drug safety information is complete and accurate

## Known Pitfalls
- Confusing benign oral lesions (canker sores, fungal patches) with oral cancer; the sample data shows these are frequently conflated by consumers, and responses must carefully explain distinguishing features without false reassurance to tobacco users
- Overly reassuring responses about lumps or swollen lymph nodes without flagging red-flag criteria such as rapid growth, firmness, or accompanying systemic symptoms like night sweats or unexplained weight loss
- Treating 'non-cancerous' or 'benign' diagnoses as requiring no follow-up; the sample data shows benign tumors and complex cysts still require monitoring and that atypical hyperplasia carries significant malignancy risk
- Failing to connect cancer-related symptoms (e.g. blood clots, elevated liver enzymes) to systemic disease mechanisms; agents must avoid siloing cancer questions from relevant cross-category content in Digestive System & Liver and Kidney & Urinary Health

## Dominant Explanation Style
TIER_A responses follow a reassurance-first, mechanism-brief, action-oriented pattern: they acknowledge the consumer's concern, offer a probable benign or less severe explanation, briefly note risk factors or differential diagnoses, and close with a concrete next step such as biopsy, follow-up, or specialist referral. Clinical jargon is used but usually paired with context clues, and responses avoid definitive diagnoses while still providing substantive guidance.

