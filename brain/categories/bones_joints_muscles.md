<!-- STATUS: DRAFT -- awaiting human review -->

# Bones, Joints & Muscles

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 24,562 | MedMCQA: 13,469 | PubMedQA: 67 | MedQuAD: 533
- **Missing explanations**: 1,017 (4.1%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 5,413 | 22% |
| TIER_B | 11,490 | 47% |
| TIER_C | 4,178 | 17% |
| TIER_D | 3,481 | 14% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Anatomy | 8,393 |
| Orthopaedics | 2,988 |
| Surgery | 851 |
| Physiology | 256 |
| Medicine | 176 |
| Pathology | 144 |
| Forensic Medicine | 142 |
| Radiology | 142 |
| Unknown | 119 |
| Anaesthesia | 112 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] Hi, Lately I have been getting, numbness and a tingling sensation in my hands and fingers. Particularly the wrists side of my little finger and my rin...
- [healthcaremagic_records] [TIER_D] I heard a click or pop in my left knee like it tore something while I was at my Physical Therapy session for my right leg problem. Same thing happened...
- [healthcaremagic_records] [TIER_C] I have Wegeners. Last Rituxan infusion Jan 2013 and Prednisone free since Nov 2013. I was taking Plaquenil and the occasional Diclofenac and have wean...
- [healthcaremagic_records] [TIER_C] My ankle hurts. There is no bruising, swollen slightly. I have a bad back an the area that my back hurts is the same side. I have my ankle in a suppor...
- [healthcaremagic_records] [TIER_C] my left calf muscle has been very tight for about 4 weeks now, i cant walk properly as it feels like the tendons r being squeezed, two times it has fe...

## Links
<!-- Derived from secondary_category co-occurrence in 24,562 DB records -->
- **Strong links:**
  - [Emergency & Critical Care](emergency_critical_care.md) — 712 cross-hits
  - [Skin & Dermatology](skin_dermatology.md) — 439 cross-hits
  - [Cancer](cancer.md) — 419 cross-hits
- **Weak links:**
  - [Ear, Nose & Throat](ear_nose_throat.md) — 277 cross-hits
  - [Children's Health](childrens_health.md) — 243 cross-hits
  - [Kidney & Urinary Health](kidney_urinary.md) — 215 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Back Pain & Spine, Joint Pain & Arthritis, Fractures & Bone Health, Muscle Pain & Injuries, Shoulder & Neck Pain, Knee & Hip Problems, Hand, Wrist & Foot Pain, Autoimmune Joint Conditions, Sports & Overuse Injuries, Nerve-Related Musculoskeletal Pain
- **Confidence:** High

## Source Priority
1. PubMed / NCBI peer-reviewed orthopedic and rheumatology studies
2. Mayo Clinic musculoskeletal and orthopedic content
3. American Academy of Orthopaedic Surgeons (AAOS) patient education
4. Arthritis Foundation condition guides
5. WebMD / Healthline general bone and joint consumer articles
**Rationale:** Peer-reviewed orthopedic literature and major specialty organizations like AAOS provide the most accurate mechanism-based and evidence-grounded explanations for bone and joint conditions. Consumer-facing sources like Arthritis Foundation are valuable for accessibility but should be cross-checked against clinical references given the high cross-category overlap with cardiac and emergency presentations.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| knee giving out | joint instability or ligamentous laxity | consumers describe mechanical buckling which may indicate ligament, meniscal, or neurological causes requiring differentiation |
| pinched nerve | nerve root compression or radiculopathy | very common lay term used to describe cervical or lumbar radiculopathy; mapping helps retrieve accurate mechanism-based content |
| swollen joints | joint effusion or synovitis | consumers rarely distinguish between fluid accumulation and inflammation; relevant to arthritis and autoimmune workup |
| back goes out | acute lumbar muscle spasm or disc herniation | phrase implies sudden-onset back pain event; may need triage toward disc, nerve, or muscular cause |
| bone on bone | severe osteoarthritis with loss of cartilage | frequently used by patients who have been told this by a provider; signals advanced joint degeneration |
| rotator cuff | rotator cuff tendinopathy or tear | consumers often use this term correctly but need guidance on conservative vs surgical management options |
| lump in muscle | soft tissue mass, lipoma, or myositis nodule | sample data shows consumers describing tender lumps along limbs; needs flagging for possible cancer cross-category review |
| morning stiffness | inflammatory arthritis-related morning stiffness | duration of morning stiffness is a key clinical differentiator between OA and RA; important to surface in responses |

## Common Query Patterns
- Multi-symptom whole-body pain query (e.g. 'pain in my back, shoulder, feet, and ankles') -> triage for systemic/autoimmune causes such as rheumatoid arthritis or fibromyalgia before attributing to posture alone
- Pain in arm or shoulder combined with chest tightness -> always cross-reference Emergency & Critical Care rules and flag possible cardiac origin before addressing musculoskeletal causes
- Recent injury followed by new or worsening symptoms in a different body region (e.g. 'broke my thumb and now have shoulder pain') -> address coincidental vs causative relationship clearly and explain referred or nerve-related pain pathways
- Lower back pain after already being tested for kidney, GI, or reproductive causes -> retrieve musculoskeletal and nerve-based explanations such as fibromyalgia, disc issues, or muscle spasm while validating the consumer's diagnostic journey
- Consumer reports a specific diagnosis they consider 'private' or unexplained but lists widespread joint symptoms -> provide general autoimmune and inflammatory joint condition information and recommend rheumatology evaluation without speculating on undisclosed diagnoses

## Category-Specific Rules
- Always screen musculoskeletal queries involving chest pain, left arm pain, or shoulder pain for potential cardiac red flags before providing a bone or joint explanation, and include a prompt to seek emergency care if cardiac symptoms are present.
- When a consumer describes pain in three or more separate body regions simultaneously, retrieve content related to systemic conditions such as rheumatoid arthritis, fibromyalgia, or lupus rather than defaulting to localized mechanical causes.
- For queries involving tender lumps, nodules, or masses along limbs or muscles, apply Cancer cross-category review rules and include a recommendation to have any unexplained soft tissue mass evaluated in person.
- When explaining nerve-related pain (radiculopathy, pinched nerve), always map the consumer-reported symptom location back to the likely spinal level or anatomical nerve pathway to help consumers understand why pain appears in unexpected locations.
- Do not attribute all swelling in the feet and ankles to a musculoskeletal cause; cross-reference Kidney & Urinary Health and Emergency & Critical Care categories when bilateral lower extremity swelling is described alongside other systemic symptoms.

## Known Pitfalls
- Assuming all left-arm or shoulder pain is musculoskeletal: the sample data repeatedly shows consumers presenting with symptoms that overlap cardiac presentations; failing to flag these for emergency triage is a critical safety error.
- Treating multi-site pain as posture or strain by default: the sample data shows experts considering polyarthritis and autoimmune conditions when pain spans multiple unrelated regions, and the system must not oversimplify to mechanical causes.
- Conflating a coincidental injury timeline with causation: as shown in the broken thumb and pinched nerve case, consumers may assume injuries caused distant symptoms; the system must explain anatomical plausibility rather than confirming or denying a causal link without evidence.
- Overlooking cross-category signals in skin plus joint presentations: the sample includes rashes on shoulders alongside musculoskeletal complaints, which may indicate autoimmune conditions like psoriatic arthritis or lupus requiring Skin & Dermatology co-retrieval.

## Dominant Explanation Style
TIER_A explanations follow a pattern of first acknowledging the consumer's described symptoms, then offering a ranked differential of likely causes from most to least probable, and directing the consumer toward specific diagnostic steps or specialist referrals. Responses tend to be clinically grounded but consumer-accessible, using anatomical terms alongside plain-language equivalents and emphasizing when in-person evaluation is necessary.

