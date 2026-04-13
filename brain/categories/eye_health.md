<!-- STATUS: DRAFT -- awaiting human review -->

# Eye Health

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 9,475 | MedMCQA: 7,712 | PubMedQA: 10 | MedQuAD: 387
- **Missing explanations**: 177 (1.9%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 2,822 | 30% |
| TIER_B | 4,406 | 47% |
| TIER_C | 1,725 | 18% |
| TIER_D | 522 | 6% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Ophthalmology | 6,916 |
| Anatomy | 216 |
| Physiology | 89 |
| Pharmacology | 78 |
| Medicine | 72 |
| Unknown | 63 |
| Forensic Medicine | 61 |
| Surgery | 53 |
| Pathology | 53 |
| Microbiology | 42 |

## Sample Questions

- [healthcaremagic_records] [TIER_D] I m finding some information that pertains; however, here goes. I m having clenching pain in left cheekbone that radiates to my left eye, along with s...
- [healthcaremagic_records] [TIER_B] Hi, I am allergic to dust and change of temperature, each year in month of jan-feb-march (change of season from winter to summer and vice versa..) it ...
- [healthcaremagic_records] [TIER_B] Hi, I have Eosinophil differential count of 08. MCHC of 35.8. 2 years ago, I had a Eosinophil differentil count of 11 which resulted in my right eye h...
- [healthcaremagic_records] [TIER_D] What are the symptoms of an elevated ammonia level? My 30yr old son takes Depakote for a seizure disorder and bi-polar he also has autism, so I can t ...
- [healthcaremagic_records] [TIER_C] I am 49 and was diagnosed with mitro valve prolapse when I was 22. My symptoms have been  mild over the years.But lately I will have a murmur and its ...

## Links
<!-- Derived from secondary_category co-occurrence in 9,475 DB records -->
- **Strong links:**
  - [Ear, Nose & Throat](ear_nose_throat.md) — 487 cross-hits
  - [Medications & Drug Safety](medications_drug_safety.md) — 327 cross-hits
  - [Children's Health](childrens_health.md) — 274 cross-hits
- **Weak links:**
  - [Skin & Dermatology](skin_dermatology.md) — 223 cross-hits
  - [Emergency & Critical Care](emergency_critical_care.md) — 215 cross-hits
  - [Cancer](cancer.md) — 202 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Vision Problems & Refractive Errors, Eye Injuries & Trauma, Eye Infections & Inflammation, Retinal Conditions, Eyelid & Periorbital Issues, Dry Eye & Eye Comfort, Pediatric Eye Health, Glaucoma & Optic Nerve, Allergic Eye Conditions, Eye Floaters & Visual Disturbances
- **Confidence:** High

## Source Priority
1. American Academy of Ophthalmology (AAO) patient education resources
2. National Eye Institute (NEI) consumer guides
3. Mayo Clinic and Cleveland Clinic ophthalmology pages
4. MedlinePlus eye health encyclopedia entries
5. Community Q&A platforms and general health forums
**Rationale:** Eye conditions range from benign to sight-threatening, so ophthalmologist-reviewed sources like AAO and NEI ensure clinically accurate, consumer-friendly guidance. General forums and Q&A platforms are deprioritized because symptom overlap between serious and minor eye conditions makes unverified advice particularly risky.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| eye floaters | vitreous floaters or muscae volitantes | Extremely common consumer search; important to distinguish benign floaters from sudden-onset floaters that may signal retinal detachment |
| lazy eye | amblyopia | Parents frequently search this term for children; early detection and treatment framing is critical |
| crossed eyes | strabismus | Common pediatric concern; cross-links to Children's Health subcategory |
| pinkeye | conjunctivitis | High-volume consumer term; system must differentiate viral, bacterial, and allergic types as treatments differ |
| black eye | periorbital hematoma or periorbital ecchymosis | Trauma-related; sample data shows consumers asking about lingering swelling or lumps after injury weeks later |
| blurry vision | visual acuity disturbance or refractive error | Broad symptom with many causes; system must triage toward urgent vs. non-urgent based on onset and associated symptoms |
| macular degeneration | age-related macular degeneration (AMD) | Caregivers often search on behalf of older family members; sample data shows treatment-outcome questions |
| eye strain | asthenopia | Very common in digital-device context; often co-searched with headaches and fatigue |

## Common Query Patterns
- Consumer describes persistent swelling or lump after eye/face injury -> retrieve trauma aftercare content and flag if swelling lasts beyond 2-3 weeks as reason to follow up with a physician
- Consumer reports sudden vision changes (flashes, new floaters, curtain over vision) -> treat as urgent and surface emergency triage guidance before general eye health content
- Parent asks about child squinting, wandering eye, or failing school eye test -> route to pediatric eye health subcategory and emphasize importance of early ophthalmology evaluation
- Consumer reports eye redness with discharge and asks if it is an infection -> distinguish viral vs bacterial vs allergic conjunctivitis patterns and advise when to seek care vs monitor at home
- Consumer describes seeing distorted, enlarged, or bubble-like shapes around people -> retrieve content covering both visual disturbance causes (e.g., astigmatism, retinal issues) and note when neurological evaluation may also be warranted

## Category-Specific Rules
- Always distinguish between symptoms requiring urgent or emergency care (sudden vision loss, eye trauma with possible penetration, flashes and floaters onset) and those that are non-urgent; surface urgency guidance at the top of any response involving acute-onset symptoms.
- When a question involves both eye symptoms and systemic symptoms (e.g., fatigue, weight changes, neurological signs as seen in sample data), retrieve content that addresses the eye component but explicitly note that a multi-system workup may be needed and cross-reference relevant categories.
- Do not recommend specific prescription eye drops, steroids, or anti-VEGF treatments (e.g., for macular edema) as consumer-actionable steps; frame these as options a treating ophthalmologist would discuss.
- For trauma-related queries (cheekbone hits, head injuries near the eye), always include follow-up red flags such as double vision, light sensitivity, worsening pain, or vision changes even if initial X-rays or exams were normal.
- When visual disturbances could have either an ocular or neurological origin (e.g., visual hallucinations, field defects, migraine aura), retrieve eye health content but include a clear note that neurological causes must be ruled out by a qualified provider.

## Known Pitfalls
- Assuming persistent post-trauma swelling or a lump is always benign: sample data shows consumers asking about lumps weeks or months after facial injury; agents must not reassure without flagging that organized hematomas or cysts warrant evaluation.
- Conflating systemic symptom clusters (fatigue, weight gain, mood changes, heavy eyes) with primary eye conditions: sample data shows these presentations often reflect thyroid, mental health, or nutritional issues, not purely ophthalmologic causes.
- Treating all red or irritated bump questions near the eye as simple skin infections without considering conditions like chalazion, hordeolum (stye), or periorbital cellulitis, which have different urgency and treatment profiles.
- Over-simplifying macular edema questions by only addressing laser treatment: sample data shows patients whose laser treatment failed and who have complex follow-up questions; agents must acknowledge treatment failure scenarios and the existence of alternative therapies like anti-VEGF injections without prescribing them.

## Dominant Explanation Style
TIER_A responses are written in a reassuring, conversational tone that briefly validates the consumer's concern before offering a working diagnosis and general management advice. Explanations lean on probable causes and practical next steps rather than exhaustive clinical detail, and they consistently close with a recommendation to follow up with a physician or specialist.

