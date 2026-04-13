<!-- STATUS: DRAFT -- awaiting human review -->

# Dental & Oral Health

<!-- ====== AUTO-GENERATED — DO NOT EDIT BELOW THIS LINE ====== -->
## Data Coverage

- **Total**: 13,723 | MedMCQA: 9,595 | PubMedQA: 16 | MedQuAD: 139
- **Missing explanations**: 5,268 (38.4%)

## Quality Tiers

| Tier | Count | % |
|------|-------|---|
| TIER_A | 1,978 | 14% |
| TIER_B | 4,747 | 35% |
| TIER_C | 1,228 | 9% |
| TIER_D | 5,770 | 42% |

## Contributing MedMCQA Subjects

| Subject | Count |
|---------|-------|
| Dental | 8,914 |
| Pathology | 178 |
| Anatomy | 157 |
| Surgery | 130 |
| Radiology | 69 |
| Forensic Medicine | 57 |
| Medicine | 37 |
| Microbiology | 20 |
| Unknown | 13 |
| Physiology | 9 |

## Sample Questions

- [healthcaremagic_records] [TIER_B] hi on the tooth all the way in the back of my mouth i have a bump the size of a #2 earaser and now my whole mouth hurts and my tonsol hurts please hel...
- [healthcaremagic_records] [TIER_B] The inside of my jaw hurts.. maybe my wisdom teeth are coming out but I dont know for sure.. I have had mumps as a child and sore tonsils more than on...
- [healthcaremagic_records] [TIER_A] My daughter is suffering from a bad toothache that started yesterday. It is now affecting her ear. She can t eat or hardly drink. Her dentist appointm...
- [healthcaremagic_records] [TIER_C] Hi I had oral surgery to remove a front upper tooth and also to prep my other front teeth for a bridge.Dentist also did a \"scaling\" of my teeth wher...
- [healthcaremagic_records] [TIER_A] had wisdom teeth pulled 3 weeks ago.  had dry socket in both lower holes.  still having alot of pain in lower left and yellow pus coming out.  been \"...

## Links
<!-- Derived from secondary_category co-occurrence in 13,723 DB records -->
- **Strong links:**
  - [Ear, Nose & Throat](ear_nose_throat.md) — 579 cross-hits
  - [Infections & Infectious Disease](infections.md) — 433 cross-hits
  - [Skin & Dermatology](skin_dermatology.md) — 388 cross-hits
- **Weak links:**
  - [Children's Health](childrens_health.md) — 326 cross-hits
  - [Bones, Joints & Muscles](bones_joints_muscles.md) — 275 cross-hits
  - [Emergency & Critical Care](emergency_critical_care.md) — 217 cross-hits
<!-- ====== AUTO-GENERATED — DO NOT EDIT ABOVE THIS LINE ====== -->

## Metadata
- **Subcategories:** Toothache & Tooth Pain, Gum Disease & Periodontal Health, Dental Infections & Abscesses, Wisdom Teeth & Extractions, Oral Sores & Lesions, Root Canals & Dental Procedures, Jaw Pain & Swelling, Dry Socket & Post-Extraction Complications
- **Confidence:** High

## Source Priority
1. American Dental Association (ADA) patient resources (most trusted)
2. Mayo Clinic dental health pages
3. Cleveland Clinic oral health content
4. MedlinePlus dental topics
5. WebMD dental section (least trusted)
**Rationale:** The ADA provides professionally vetted, evidence-based patient education that is both accurate and consumer-accessible. Established medical institutions like Mayo Clinic and Cleveland Clinic offer reliable explanations of dental conditions with clear guidance on when to seek professional care.

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| bubble on gum | dental abscess or gum boil (parulis) | Consumers frequently describe abscesses as bubbles or bumps; correct identification is critical because these signal serious infection |
| gum infection | periodontitis or pericoronitis | Generic term that could indicate early gingivitis or advanced periodontal disease; context clues like tooth mobility help distinguish severity |
| dry socket | alveolar osteitis | Consumers already widely use this lay term, but the system should recognize it and connect it to post-extraction pain protocols |
| loose tooth (adult) | tooth mobility due to periodontitis | Tooth mobility in adults is a red flag for advanced bone loss, unlike in children where it is normal |
| root canal | endodontic therapy | Consumers understand 'root canal' but often conflate the procedure with extraction; clarification reduces unnecessary fear |
| wisdom tooth pain | pericoronitis or impacted third molar | Pain around a partially erupted wisdom tooth is often pericoronitis, which carries infection risk distinct from simple eruption discomfort |
| lump on jaw or gum | dental abscess, cyst, or lymphadenopathy | A jaw lump may indicate spreading infection requiring urgent care; the system must flag this for prompt professional evaluation |
| toothache spreading to ear | referred pain from dental infection or pulpitis | Consumers interpret ear pain as separate from dental issues; clarifying referred pain pathways helps them understand urgency |

## Common Query Patterns
- Consumer describes pain spreading from tooth to ear or jaw -> explain referred pain, flag as potentially urgent infection, advise same-day or emergency dental visit
- Consumer asks about a bump, bubble, or swelling on gums -> identify likely abscess, explain infection risk, strongly recommend prompt dental evaluation and avoid advising to pop or drain at home
- Consumer describes post-extraction symptoms like pain, pus, or foul smell after several days -> assess for dry socket or infected socket, recommend returning to dentist, offer interim comfort measures like warm saline rinse
- Consumer expresses fear of the dentist and is delaying care -> acknowledge dental anxiety empathetically, explain risks of untreated infection spreading, provide practical tips for communicating fears to the dentist
- Consumer asks whether their gum or jaw issue needs the ER vs. waiting for a dentist appointment -> triage based on red-flag symptoms such as spreading swelling, difficulty swallowing or breathing, fever, or trismus, and recommend ER if any are present

## Category-Specific Rules
- Always flag signs of spreading dental infection (swelling extending to neck or floor of mouth, difficulty swallowing, high fever, trismus) as potential emergencies requiring immediate ER evaluation, not just a dentist visit.
- Do not recommend specific prescription antibiotics (e.g., Amoxicillin dosages) or advise consumers to self-medicate; instead, explain that a dentist or physician must assess and prescribe based on the individual case.
- When a consumer mentions tooth mobility in an adult, treat it as a red flag for advanced periodontal disease and recommend professional evaluation promptly rather than offering reassurance that it may resolve on its own.
- Cross-reference ENT and Infections categories when dental symptoms involve ear pain, sinus pressure, or systemic flu-like symptoms, as these may indicate spreading orofacial infection beyond the oral cavity.
- Always distinguish between normal post-procedure discomfort and complication warning signs (e.g., pus, worsening pain after 3+ days, fever following extraction) so consumers know when to call their provider versus manage at home.

## Known Pitfalls
- Assuming ear pain is purely an ENT issue when the consumer also reports toothache: dental infections commonly cause referred ear pain, and missing this connection leads to delayed treatment of the actual source.
- Treating all post-extraction pain as normal healing: the sample data shows dry socket and infected sockets are common and distinct from expected soreness, requiring timely identification and professional follow-up rather than reassurance to wait it out.
- Underestimating a jaw or gum lump as cosmetic or minor: multiple sample cases show lumps that represent deep abscesses or spreading periodontal infections that can become life-threatening if untreated.
- Reinforcing dental anxiety by overemphasizing painful or invasive procedures: the sample data highlights patients delaying necessary care due to fear; responses should balance honest information with reassurance about modern pain management and the greater risks of untreated infection.

## Dominant Explanation Style
TIER_A responses in this category follow a clinical-to-consumer translation style: they briefly validate the symptom, offer a likely diagnosis with a short mechanistic explanation, and then give concrete next steps (consult a dentist, apply warm saline rinse, use OTC numbing gel) while noting when urgency is warranted. Answers are direct and practical, avoiding excessive medical jargon, and frequently reference the need for clinical examination or X-ray to confirm the cause.

