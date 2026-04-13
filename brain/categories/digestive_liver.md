<!-- STATUS: DRAFT -- awaiting human review -->

# Digestive System & Liver

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 27,598 | MedMCQA: 13,688 | PubMedQA: 68 | MedQuAD: 1,577
- **Missing explanations**: 1,557 (5.6%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 7,738 | 28% |
| TIER_B | 12,348 | 45% |
| TIER_C | 2,807 | 10% |
| TIER_D | 4,705 | 17% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Surgery | 8,363 |
| Medicine | 1,226 |
| Anatomy | 1,221 |
| Pathology | 952 |
| Physiology | 534 |
| Microbiology | 407 |
| Gynaecology & Obstetrics | 286 |
| Radiology | 276 |
| Unknown | 156 |
| Biochemistry | 140 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] i have gastric problem how it can remove...
- [healthcaremagic_records] [TIER_D] Severe lower abdominal pain, collitis, fever 97.7-99.4 today, new symptom lower to mid back pain, rapid breathing, high WBC, tingling and numbness rec...
- [healthcaremagic_records] [TIER_B] how long does it take benadryl to leave your system? I have allergies to soy and took it several times last week and now I have been sick to my stomac...
- [healthcaremagic_records] [TIER_B] My jaw aches on both sides on bottom of my mouth. Its a dull achy pain. Doesnt hurt when I eat, only when sitting quietly it occurs, mostly at night. ...
- [healthcaremagic_records] [TIER_B] Dear Sir/ Madam, I have been suffering from Jaundice since last one month.My Bilirubin count is now 0.9mg/dl however there is not much improvement in ...

## Links
<!-- Derived from secondary_category co-occurrence in 27,598 DB records -->
- **Strong links:**
  - [Cancer](cancer.md) — 2,185 cross-hits
  - [Infections & Infectious Disease](infections.md) — 1,308 cross-hits
  - [Kidney & Urinary Health](kidney_urinary.md) — 983 cross-hits
- **Weak links:**
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 477 cross-hits
  - [Women's & Reproductive Health](womens_reproductive.md) — 362 cross-hits
  - [Medications & Drug Safety](medications_drug_safety.md) — 348 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Liver Disease & Function, Acid Reflux & GERD, Inflammatory Bowel Disease, Gallbladder & Bile Ducts, Diarrhea & Loose Stools, Hepatitis & Jaundice, Fatty Liver Disease, Colorectal & Bowel Health, Stomach & Duodenal Disorders, Digestive Enzyme & Absorption Issues
- **Confidence:** High

## Source Priority
1. NIH National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)
2. Mayo Clinic Gastroenterology & Hepatology
3. American College of Gastroenterology (ACG) patient resources
4. Cleveland Clinic digestive disease guides
5. WebMD / Healthline consumer digestive health articles
**Rationale:** NIDDK and ACG provide reference-cited, guideline-based content specifically covering digestive and liver conditions at a consumer-accessible level. Mayo Clinic and Cleveland Clinic offer clinically reviewed explanations that align with the mechanism-based explanation style dominant in this category.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| liver enzymes high | elevated SGPT / ALT or SGOT / AST | Consumers frequently report lab result names without understanding what organ or process is affected; mapping helps retrieve liver injury content |
| acid reflux | gastroesophageal reflux disease (GERD) | GERD is the clinical diagnosis but consumers almost always search using 'acid reflux' or 'heartburn' |
| loose motions | diarrhea | Common phrasing in South Asian consumer queries; system must recognize this as equivalent to diarrhea to retrieve correct results |
| yellowing of skin or eyes | jaundice / hyperbilirubinemia | Consumers describe the visible symptom rather than the condition name; bilirubin level context is often missing |
| fatty liver | hepatic steatosis / non-alcoholic fatty liver disease (NAFLD) | Consumers use 'fatty liver' colloquially; clinical records may use steatosis or NAFLD which must be cross-referenced |
| stomach bloating or food stuck feeling | gastroparesis / dyspepsia / delayed gastric emptying | Vague symptom descriptions often pointing to GERD or motility disorders; careful triage to avoid over- or under-matching |
| gallstones | cholelithiasis | Cholelithiasis appears in clinical reports and sample data; consumers will not recognize this term and need plain-language bridging |
| Crohn's or IBD pain | Crohn's disease / inflammatory bowel disease / duodenitis | Consumers may conflate IBD with IBS or general stomach pain; distinguishing inflammation-based pain from functional pain is critical |

## Common Query Patterns
- Consumer reports a specific lab value (e.g. 'my SGPT is 280, is that bad?') -> retrieve normal range context, explain what the enzyme measures, flag that elevated values require physician follow-up without diagnosing the cause
- Consumer describes a symptom cluster without a diagnosis (e.g. 'I feel tightness in my chest after eating and can't burp') -> map to likely condition candidates such as GERD or dyspepsia, explain mechanisms in plain language, and recommend evaluation if persistent
- Consumer asks about a family member's condition using report terminology (e.g. 'my father's report says hepatic steatosis and hepatomegaly, what does this mean?') -> define each term in plain language, explain how they relate to each other, and note the importance of specialist follow-up
- Consumer describes a child's ongoing digestive symptom (e.g. 'my baby has had loose motions for 12 days') -> prioritize safety-first response including hydration guidance, flag duration as a reason to seek medical care, and avoid recommending specific medications
- Consumer asks whether a condition is serious or life-threatening (e.g. 'can jaundice kill you?') -> provide clear factual answer about severity spectrum, distinguish between mild and severe causes, and direct to emergency care indicators without causing undue panic

## Category-Specific Rules
- Always flag liver enzyme results (ALT/SGPT, AST/SGOT, bilirubin) as requiring physician interpretation; provide reference ranges for context but never attribute a specific cause based on numbers alone.
- When a query involves a child or infant with digestive symptoms lasting more than 48-72 hours, always include a recommendation to seek in-person medical evaluation before providing general management tips.
- When cross-category signals suggest cancer (e.g. 'liver metastasis', 'tumor marker') appear in a digestive query, retrieve oncology-adjacent content and explicitly note that the consumer should be under specialist care rather than relying on general health information.
- Distinguish between GERD / acid reflux and more serious esophageal conditions (e.g. Barrett's esophagus) when relevant context is present; do not merge these into a single generic acid reflux response.
- For hepatitis-related queries, always clarify the hepatitis type (A, B, C, autoimmune) if mentioned, since transmission risk, treatment, and prognosis differ substantially and conflating them can cause consumer harm.

## Known Pitfalls
- Attributing elevated liver enzymes solely to one cause (e.g. only fatty liver or only medication) when multiple etiologies such as hepatitis, alcohol use, and lipid disorders frequently co-occur, as seen in the sample SGPT/Lipantil case.
- Treating 'loose motions' or diarrhea in infants as a benign self-resolving issue without flagging duration thresholds; 12 days of loose stools in a one-year-old is a red flag that the sample data addresses but agents may underweight.
- Conflating GERD symptom descriptions (chest tightness, difficulty burping, food stuck) with cardiac symptoms or vice versa; the sample data shows multiple GERD cases presenting with chest complaints that require careful differentiation and appropriate referral language.
- Using clinical report terminology (cholelithiasis, hepatomegaly, hepatic steatosis, prostatomegaly) in consumer-facing responses without plain-language translation, which the sample data demonstrates consumers paste directly from reports without understanding.

## Dominant Explanation Style
TIER_A responses in this category follow a symptom-to-mechanism pattern: they first acknowledge the consumer's concern, then explain the physiological reason behind the symptom or lab finding in accessible but medically grounded language, and close with a prioritized list of next steps or management suggestions. Responses are direct and practical, often referencing specific body structures (e.g. esophageal sphincter, bilirubin pathways) to build consumer understanding without overwhelming jargon.

