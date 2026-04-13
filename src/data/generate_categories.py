"""
Generate fully populated category files following the Brain Pattern System
Design plan (Approach C: Graph-Linked Flat Files).

Each file follows the template from docs/plans/2026-02-15-brain-patterns-design.md
section 4.1, with substantive domain content for all sections.
"""

import csv
import os
from collections import Counter, defaultdict
from pathlib import Path

BRAIN_DIR = Path(__file__).parent.parent.parent / "brain"
CAT_DIR = BRAIN_DIR / "categories"

# ─── Read stats from category_mapping.csv ────────────────────────────────────

def load_stats() -> dict:
    """Load categorization stats from existing CSV."""
    stats = defaultdict(lambda: {
        "total": 0, "medmcqa": 0, "pubmedqa": 0,
        "tier_a": 0, "tier_b": 0, "tier_c": 0, "tier_d": 0,
        "subjects": Counter(), "missing_exp": 0,
    })

    csv_path = BRAIN_DIR / "category_mapping.csv"
    if not csv_path.exists():
        return stats

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["primary_category"]
            stats[cat]["total"] += 1
            stats[cat][row["dataset"]] += 1
            stats[cat][row["quality_tier"].lower()] += 1
            if row["subject_name"]:
                stats[cat]["subjects"][row["subject_name"]] += 1
            if row["has_explanation"] == "False":
                stats[cat]["missing_exp"] += 1

    return stats

# ─── Category Definitions ────────────────────────────────────────────────────

CATEGORIES = {
    "heart_blood_vessels": {
        "name": "Heart & Blood Vessels",
        "source_subjects": "Medicine (CVS, coronary, valvular), Pathology (cardiovascular), Pharmacology (CVS, anti-anginal, ACE inhibitors), Physiology (cardiovascular), Surgery (aortic, vascular), Radiology (angiography, echocardiography), Anatomy",
        "subcategories": "Hypertension & Blood Pressure, Heart Failure, Arrhythmias & Rhythm Disorders, Coronary Artery Disease, Congenital Heart Defects, Valvular Heart Disease, Peripheral Vascular Disease, ECG Interpretation",
        "confidence": "High",
        "strong_links": [
            ("medications_drug_safety", "antihypertensives, anticoagulants, statins, anti-arrhythmics"),
            ("emergency_critical_care", "cardiac arrest, acute MI, hypertensive crisis, cardiogenic shock"),
            ("breathing_lungs", "pulmonary hypertension, pulmonary edema, heart-lung interactions"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "diabetes-cardiovascular risk, metabolic syndrome, lipid metabolism"),
            ("brain_nervous_system", "stroke overlap, autonomic regulation of heart rate"),
            ("kidney_urinary", "cardiorenal syndrome, renal artery stenosis, hypertension-kidney link"),
        ],
        "source_priority": [
            "ACC/AHA and ESC clinical practice guidelines (updated frequently)",
            "PubMed systematic reviews on cardiovascular outcomes",
            "MedMCQA TIER_A explanations (Harrison's, Ganong's)",
            "Consumer health sites (AHA patient pages, Mayo Clinic heart section)",
            "Community QA -- lowest priority, verify all claims",
        ],
        "source_rationale": "Cardiovascular guidelines update frequently (e.g., hypertension thresholds changed in 2017 ACC/AHA guidelines). Always use the most recent guideline version.",
        "terminology": [
            ("heart attack", "myocardial infarction (MI)", "Distinguish STEMI vs NSTEMI for clinical context"),
            ("blood pressure medicine", "antihypertensive agents", "Multiple drug classes -- specify when possible"),
            ("irregular heartbeat", "arrhythmia / dysrhythmia", "Many subtypes -- atrial fibrillation is the most common consumer query"),
            ("heart failure", "congestive heart failure (CHF)", "Not 'heart stopped' -- clarify for low-literacy users"),
            ("chest pain", "angina pectoris", "Must differentiate cardiac vs non-cardiac causes"),
            ("blood thinner", "anticoagulant / antiplatelet", "Different mechanisms -- important distinction for patient safety"),
            ("high cholesterol", "hyperlipidemia / dyslipidemia", "Consumer often conflates with diet alone"),
            ("heart murmur", "cardiac murmur", "Often benign -- distinguish functional vs pathological"),
        ],
        "query_patterns": [
            '"Is my blood pressure normal?" -> Requires user age/context. Reference current ACC/AHA thresholds (130/80 as of 2017 guidelines). Always recommend regular monitoring.',
            '"Side effects of [heart medication]" -> Strong link to Medications. Cross-reference FDA label. Include common vs rare side effects.',
            '"Symptoms of heart attack in women" -> Presentation differs by sex. Highlight atypical symptoms (jaw pain, nausea, fatigue vs classic chest pain).',
            '"Can stress cause heart problems?" -> Multi-factor. Link to Mental Health for stress/anxiety component. Cite Takotsubo cardiomyopathy as extreme example.',
        ],
        "category_rules": [
            "ECG interpretation questions: flag that visual/diagram context may be needed -- text-only answers may be insufficient",
            "Hypertension threshold questions: always cite the specific guideline year -- thresholds have changed (140/90 pre-2017, 130/80 post-2017)",
            "Drug dosing for cardiac medications: ALWAYS include 'consult your cardiologist/pharmacist' -- narrow therapeutic windows (warfarin, digoxin)",
            "Congenital heart defects: queries may involve pediatric context -- follow link to Children's Health",
        ],
        "pitfalls": [
            "Pre-2017 hypertension sources use 140/90 threshold (now considered outdated by ACC/AHA)",
            "'Heart failure' is commonly misunderstood by consumers as 'heart stopped working' -- requires careful explanation of pump dysfunction",
            "Statin controversy: community sources often contain misinformation -- prioritize Tier 1 clinical trial data",
            "Aspirin for primary prevention: guidelines changed in 2019 -- no longer universally recommended for low-risk patients",
        ],
        "explanation_style": "Pathophysiology-heavy. Most MedMCQA explanations describe the mechanism of disease progression (atherosclerosis, pump failure, conduction abnormalities). Pharmacology questions lean on drug mechanisms, half-lives, and receptor interactions.",
    },

    "brain_nervous_system": {
        "name": "Brain & Nervous System",
        "source_subjects": "Medicine (CNS), Anatomy (neuroanatomy, cerebrum), Pharmacology (CNS drugs), Pathology (nervous system), Surgery (cerebrovascular, neurosurgery)",
        "subcategories": "Stroke & Cerebrovascular Disease, Headache & Migraine, Seizures & Epilepsy, Neurodegenerative Diseases, Meningitis & CNS Infections, Spinal Cord Disorders, Peripheral Neuropathy, Cranial Nerve Disorders",
        "confidence": "High",
        "strong_links": [
            ("mental_health", "neuropsychiatric overlap -- depression in Parkinson's, anxiety in epilepsy, dementia classification"),
            ("medications_drug_safety", "anticonvulsants, anti-Parkinson drugs, analgesics, CNS depressants"),
            ("emergency_critical_care", "stroke (time-critical), head trauma, status epilepticus, raised ICP"),
        ],
        "weak_links": [
            ("eye_health", "optic nerve pathology, visual field defects in stroke, papilledema"),
            ("infections", "meningitis, encephalitis, brain abscess, neurocysticercosis"),
            ("bones_joints_muscles", "spinal cord compression, vertebral fractures, nerve entrapment"),
        ],
        "source_priority": [
            "AAN (American Academy of Neurology) clinical practice guidelines",
            "PubMed reviews on neurological outcomes",
            "MedMCQA TIER_A explanations (Harrison's CNS chapters, neuroanatomy texts)",
            "NIH NINDS patient information pages",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "Neurology is highly subspecialized. Stroke management evolves rapidly (thrombectomy windows expanded). Always check recency of stroke and epilepsy guidelines.",
        "terminology": [
            ("stroke", "cerebrovascular accident (CVA)", "Distinguish ischemic vs hemorrhagic -- treatment differs completely"),
            ("brain bleed", "intracranial hemorrhage", "Multiple types: subdural, epidural, subarachnoid, intracerebral"),
            ("fits / seizures", "epileptic seizures / epilepsy", "Single seizure != epilepsy. Clarify terminology."),
            ("pins and needles", "paresthesia", "Can indicate neuropathy, nerve compression, or vascular issue"),
            ("slipped disc", "herniated nucleus pulposus (HNP)", "Consumer term often used loosely"),
            ("shaking palsy", "Parkinson's disease", "Older consumer term still in use"),
            ("memory loss", "amnesia / cognitive impairment", "Many causes -- not always dementia"),
        ],
        "query_patterns": [
            '"What are the warning signs of a stroke?" -> FAST mnemonic (Face, Arms, Speech, Time). Emphasize urgency. Link to Emergency.',
            '"What causes numbness in hands/feet?" -> Differential diagnosis approach: peripheral neuropathy, carpal tunnel, cervical radiculopathy, diabetic neuropathy. Link to Hormones (diabetes).',
            '"Is my headache serious?" -> Red flags: sudden onset (thunderclap), worst-ever headache, neurological symptoms, fever + stiff neck -> Emergency.',
            '"Can Parkinson\'s be cured?" -> Currently no cure. Explain symptomatic management, L-DOPA therapy. Link to Medications.',
        ],
        "category_rules": [
            "Stroke queries are time-critical -- always include urgency messaging and emergency link",
            "Distinguish between central and peripheral nervous system in all responses",
            "Neuroanatomy questions often require spatial/visual context -- flag when text-only answer is insufficient",
            "Drug side effects causing neurological symptoms: follow strong link to Medications",
        ],
        "pitfalls": [
            "Stroke thrombolysis window has expanded (endovascular thrombectomy up to 24h in select patients) -- outdated sources say 3-4.5h only",
            "'Dementia' is an umbrella term, not a specific diagnosis -- always specify type (Alzheimer's, vascular, Lewy body, frontotemporal)",
            "Consumer confusion between epilepsy and single seizure -- important distinction for prognosis and treatment",
            "Bell's palsy (peripheral facial nerve) vs stroke (central facial nerve) -- critical differential that consumers often confuse",
        ],
        "explanation_style": "Neuroanatomy-driven. Most explanations describe lesion localization (which nerve, which tract, which brain region). Pathology questions focus on pathological mechanisms (demyelination, neurodegeneration, vascular occlusion).",
    },

    "mental_health": {
        "name": "Mental Health",
        "source_subjects": "Psychiatry (schizophrenia, neurotic disorders, sleep disorders, pharmacotherapy, psychoanalysis, substance use), Pharmacology (psychiatric illness, CNS)",
        "subcategories": "Depression & Mood Disorders, Anxiety & OCD, Schizophrenia & Psychotic Disorders, Substance Use & Addiction, Sleep Disorders, Dementia & Cognitive Decline, Suicide Risk Assessment, Child & Adolescent Psychiatry",
        "confidence": "High",
        "strong_links": [
            ("brain_nervous_system", "neuropsychiatric overlap -- organic causes of psychiatric symptoms, neuroimaging"),
            ("medications_drug_safety", "antidepressants (SSRIs), antipsychotics, benzodiazepines, mood stabilizers (lithium)"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "thyroid-depression link, cortisol in stress, vitamin D and mood"),
            ("womens_reproductive", "postpartum depression, premenstrual dysphoric disorder, menopause and mood"),
            ("childrens_health", "ADHD, childhood anxiety, autism spectrum"),
        ],
        "source_priority": [
            "APA (American Psychiatric Association) clinical practice guidelines, DSM-5-TR criteria",
            "NICE mental health guidelines, Cochrane reviews",
            "PubMed meta-analyses on psychopharmacology and psychotherapy outcomes",
            "NAMI (National Alliance on Mental Illness) patient resources",
            "Community QA -- very low priority, high misinformation risk",
        ],
        "source_rationale": "Mental health carries high stigma and misinformation. Consumer sources vary wildly in quality. Always prioritize evidence-based guidelines. Suicide-related queries require special handling.",
        "terminology": [
            ("feeling down / sad all the time", "major depressive disorder (MDD)", "Duration matters -- 2+ weeks of symptoms for clinical diagnosis"),
            ("panic attack", "panic disorder", "Single panic attack vs recurrent disorder -- different implications"),
            ("hearing voices", "auditory hallucinations", "Not always schizophrenia -- differential includes substance use, delirium"),
            ("mood swings", "bipolar disorder / cyclothymia", "Consumer term is vague -- distinguish from normal emotional variation"),
            ("nervous breakdown", "acute stress reaction / psychiatric crisis", "Not a clinical term but widely used by consumers"),
            ("split personality", "dissociative identity disorder (DID)", "NOT schizophrenia -- common consumer confusion"),
            ("addiction", "substance use disorder (SUD)", "DSM-5 uses spectrum: mild, moderate, severe"),
        ],
        "query_patterns": [
            '"Am I depressed?" -> Cannot diagnose. Provide PHQ-9 screening criteria. Recommend professional evaluation. Include crisis resources.',
            '"Side effects of antidepressants" -> Link to Medications. Common (sexual dysfunction, weight change, GI) vs serious (serotonin syndrome, suicidal ideation in youth).',
            '"How to help someone with suicidal thoughts" -> ALWAYS include crisis hotline (988 Suicide & Crisis Lifeline). Safety planning. Professional referral.',
            '"Is anxiety normal?" -> Distinguish normal anxiety from anxiety disorders (GAD, social anxiety, panic disorder). Duration and impairment criteria.',
        ],
        "category_rules": [
            "CRITICAL: Any query involving suicidal ideation must ALWAYS include crisis resources (988 hotline, Crisis Text Line) before any other content",
            "Never minimize mental health symptoms -- validate the user's experience",
            "Substance use: use person-first, non-stigmatizing language ('person with substance use disorder' not 'addict')",
            "Sleep disorder queries: rule out medical causes first (sleep apnea, thyroid), then consider psychiatric causes",
        ],
        "pitfalls": [
            "'Schizophrenia' is NOT 'split personality' -- this is the most common consumer misconception in mental health",
            "Benzodiazepine prescribing has changed -- long-term use now discouraged for anxiety due to dependence risk",
            "SSRI discontinuation syndrome exists -- do not advise stopping medications abruptly",
            "Lithium has a very narrow therapeutic window -- any dosing query must defer to prescriber",
        ],
        "explanation_style": "Diagnostic criteria-focused. MedMCQA explanations lean on DSM classification, symptom clusters, and pharmacotherapy mechanisms (receptor pharmacology of psychiatric drugs). Less pathophysiology than other categories.",
    },

    "digestive_liver": {
        "name": "Digestive System & Liver",
        "source_subjects": "Surgery (GIT, hepatic tumors, gall bladder, oesophagus, rectum, hernias), Medicine (GIT, malabsorption), Anatomy (GIT), Physiology (GIT), Pathology (liver)",
        "subcategories": "Stomach & Peptic Ulcers, Liver Disease & Hepatitis, Gallbladder & Bile Duct Disorders, Inflammatory Bowel Disease, Pancreatitis, Hernias, Appendicitis, GI Cancers, Malabsorption Syndromes",
        "confidence": "High",
        "strong_links": [
            ("cancer", "GI cancers (colorectal, gastric, pancreatic, hepatocellular) -- 40 cross-category hits in training data"),
            ("infections", "hepatitis A/B/C, H. pylori, intestinal parasites, C. difficile"),
            ("medications_drug_safety", "PPIs, NSAIDs causing GI bleeding, hepatotoxic drugs, laxatives"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "diabetes and gastroparesis, malnutrition, vitamin malabsorption"),
            ("childrens_health", "pediatric GI (intussusception, pyloric stenosis, Hirschsprung's) -- 11 cross-hits"),
            ("emergency_critical_care", "acute abdomen, GI hemorrhage, bowel obstruction, perforated ulcer"),
        ],
        "source_priority": [
            "ACG (American College of Gastroenterology) and AGA guidelines",
            "PubMed reviews on hepatology and gastroenterology",
            "MedMCQA TIER_A explanations (Bailey & Love for surgery, Harrison's for medicine)",
            "NIDDK patient information (NIH)",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "GI and liver disease is the highest-overlap category with Surgery (surgical vs medical management decisions). Hepatitis treatment has evolved dramatically (DAAs for Hep C). Always verify treatment recency.",
        "terminology": [
            ("stomach ulcer", "peptic ulcer disease (PUD)", "Includes both gastric and duodenal ulcers"),
            ("heartburn / acid reflux", "gastroesophageal reflux disease (GERD)", "Chronic reflux vs occasional heartburn -- different management"),
            ("fatty liver", "non-alcoholic fatty liver disease (NAFLD) / MASLD", "New nomenclature: MASLD replacing NAFLD as of 2023"),
            ("gallstones", "cholelithiasis", "Distinguish from cholecystitis (inflammation) and cholangitis (infection)"),
            ("stomach flu", "viral gastroenteritis", "NOT influenza -- important consumer distinction"),
            ("IBS", "irritable bowel syndrome", "Functional disorder vs IBD (inflammatory bowel disease) -- consumers often confuse"),
            ("Crohn's / colitis", "inflammatory bowel disease (IBD)", "Two distinct conditions with different distributions"),
            ("jaundice", "hyperbilirubinemia / icterus", "Multiple causes: pre-hepatic, hepatic, post-hepatic"),
        ],
        "query_patterns": [
            '"What causes stomach pain?" -> Broad differential. Ask about location, timing, associated symptoms. Consider peptic ulcer, gastritis, gallstones, pancreatitis, appendicitis.',
            '"Is fatty liver serious?" -> Depends on stage. NAFLD can progress to NASH, fibrosis, cirrhosis. Link to Hormones (metabolic syndrome association).',
            '"Can hepatitis be cured?" -> Depends on type. Hep C: yes (DAAs). Hep B: managed not cured. Hep A: self-limiting. Always specify type.',
            '"Do I need surgery for gallstones?" -> Not all gallstones need surgery. Symptomatic cholelithiasis → cholecystectomy. Asymptomatic → observation.',
        ],
        "category_rules": [
            "Acute abdomen presentation: always link to Emergency -- may need urgent surgical intervention",
            "Liver function test interpretation: requires clinical context, never interpret in isolation",
            "H. pylori eradication: triple/quadruple therapy evolves with resistance patterns -- cite current guidelines",
            "Colon cancer screening guidelines: age thresholds changed (now 45+ per USPSTF 2021) -- verify recency",
        ],
        "pitfalls": [
            "NAFLD nomenclature changed to MASLD/MASH in 2023 -- older sources use different terms",
            "Hepatitis C is now curable with DAAs (95%+ SVR) -- pre-2014 sources describe interferon-based treatment (outdated)",
            "Appendicitis: antibiotics-first approach is now an accepted alternative to surgery in uncomplicated cases -- older sources mandate surgery",
            "'IBS' and 'IBD' sound similar but are fundamentally different conditions -- must distinguish clearly for consumers",
        ],
        "explanation_style": "Split between surgical anatomy (anatomical landmarks, surgical approaches, complications) and pathophysiology (disease mechanisms, lab interpretation). Surgery-sourced questions are procedure-oriented; Medicine-sourced are diagnostic-oriented.",
    },

    "breathing_lungs": {
        "name": "Breathing & Lungs",
        "source_subjects": "Medicine (respiratory system, pleural effusion), Pathology (respiration), Physiology (respiratory system), Surgery (thoracic), Pharmacology (respiratory drugs)",
        "subcategories": "Asthma, COPD, Pneumonia, Tuberculosis (Pulmonary), Lung Cancer, Pleural Diseases, Bronchiectasis, Pulmonary Embolism, Interstitial Lung Disease, Sleep Apnea",
        "confidence": "High",
        "strong_links": [
            ("infections", "pneumonia, tuberculosis, COVID-19, fungal lung infections -- 10 cross-hits"),
            ("cancer", "lung cancer (NSCLC, SCLC), mesothelioma"),
            ("emergency_critical_care", "pulmonary embolism, respiratory failure, tension pneumothorax, acute asthma"),
        ],
        "weak_links": [
            ("heart_blood_vessels", "pulmonary hypertension, pulmonary edema in heart failure"),
            ("childrens_health", "pediatric asthma, croup, bronchiolitis -- 9 cross-hits"),
            ("medications_drug_safety", "bronchodilators, inhaled corticosteroids, anti-TB drugs"),
        ],
        "source_priority": [
            "GINA (Global Initiative for Asthma), GOLD (Global Initiative for COPD) guidelines",
            "ATS/ERS respiratory guidelines, WHO TB guidelines",
            "PubMed reviews on pulmonology",
            "Lung.org and American Lung Association patient resources",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "Asthma and COPD guidelines (GINA, GOLD) are updated annually. TB management varies by drug resistance patterns. Always check local epidemiology for infectious respiratory disease.",
        "terminology": [
            ("trouble breathing", "dyspnea", "Acute vs chronic -- different urgency levels"),
            ("asthma attack", "acute asthma exacerbation", "Distinguish mild from severe/life-threatening"),
            ("coughing up blood", "hemoptysis", "Red flag symptom -- needs urgent evaluation"),
            ("fluid in lungs", "pulmonary edema / pleural effusion", "Different conditions -- distinguish for accurate retrieval"),
            ("collapsed lung", "pneumothorax", "Spontaneous vs traumatic -- different management"),
            ("blood clot in lung", "pulmonary embolism (PE)", "Medical emergency -- link to Emergency"),
            ("smoker's cough", "chronic bronchitis / COPD", "May indicate progressive disease"),
        ],
        "query_patterns": [
            '"How do I use an inhaler?" -> Technique matters significantly. Specify MDI vs DPI. Include spacer recommendation.',
            '"Is my cough serious?" -> Duration (acute <3 weeks vs chronic >8 weeks), associated symptoms (hemoptysis, weight loss = red flags), productive vs dry.',
            '"Can asthma be cured?" -> No cure, but excellent control achievable. Explain stepwise therapy. Link to Medications.',
            '"TB treatment duration" -> Standard: 6 months (2HRZE + 4HR). MDR-TB: 9-20 months. Always verify local resistance patterns.',
        ],
        "category_rules": [
            "Hemoptysis is always a red flag -- include urgent evaluation recommendation",
            "Asthma action plans: reference color-coded zone system (green/yellow/red) for consumer understanding",
            "Smoking cessation: integrate into all COPD and lung cancer responses",
            "TB: distinguish latent TB infection (LTBI) from active TB disease -- very different management",
        ],
        "pitfalls": [
            "COPD GOLD classification updated regularly -- verify which version the source uses",
            "Asthma: SABA-only treatment is no longer first-line in GINA 2019+ guidelines -- outdated sources recommend salbutamol monotherapy",
            "Pulmonary embolism can present subtly (tachycardia only, pleuritic pain) -- don't dismiss non-classic presentations",
            "TB drug interactions: rifampicin is a potent CYP450 inducer -- affects many other medications",
        ],
        "explanation_style": "Physiology-heavy. Explanations frequently reference lung volumes, gas exchange mechanisms, ventilation-perfusion mismatch. Pharmacology questions focus on inhaler devices and drug delivery.",
    },

    "blood_immune": {
        "name": "Blood & Immune Disorders",
        "source_subjects": "Pathology (haematology, blood, immunodeficiency), Medicine (blood, immune system), Microbiology (immunology), Physiology (blood)",
        "subcategories": "Anemia (Iron-Deficiency, Sickle Cell, Thalassemia, Megaloblastic), Leukemia & Lymphoma, Bleeding & Clotting Disorders, Thrombocytopenia, Autoimmune Conditions, Immunodeficiency, Blood Transfusion",
        "confidence": "High",
        "strong_links": [
            ("cancer", "hematologic malignancies (leukemia, lymphoma, myeloma) -- 12 cross-hits"),
            ("infections", "immunodeficiency and opportunistic infections, HIV/AIDS"),
            ("medications_drug_safety", "anticoagulants, chemotherapy, immunosuppressants, iron supplements"),
        ],
        "weak_links": [
            ("childrens_health", "pediatric hematology (sickle cell, thalassemia), neonatal jaundice"),
            ("kidney_urinary", "renal anemia (EPO deficiency), TTP/HUS"),
            ("womens_reproductive", "iron-deficiency anemia in menstruation, pregnancy-related anemia"),
        ],
        "source_priority": [
            "ASH (American Society of Hematology) guidelines, BCSH guidelines",
            "PubMed reviews on hematology and immunology",
            "MedMCQA TIER_A explanations (Robbins for pathology, Harrison's for clinical)",
            "Sickle Cell Disease Association, patient advocacy sites",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "Hematology intersects heavily with oncology and immunology. Treatment protocols (especially for leukemia/lymphoma) evolve rapidly with targeted therapies and immunotherapy.",
        "terminology": [
            ("low blood count", "anemia / cytopenia", "Specify which cell line is low (RBC, WBC, platelets)"),
            ("blood cancer", "leukemia / lymphoma / myeloma", "Three distinct diseases -- different prognosis and treatment"),
            ("blood clot", "thrombosis (venous or arterial)", "DVT vs PE vs arterial -- very different conditions"),
            ("low immunity", "immunodeficiency", "Primary (genetic) vs secondary (HIV, drugs, malnutrition)"),
            ("bruising easily", "thrombocytopenia / coagulation disorder", "Platelet vs clotting factor issue"),
            ("blood test results", "complete blood count (CBC)", "Most common lab test -- explain normal ranges"),
        ],
        "query_patterns": [
            '"What does my blood test mean?" -> Explain CBC components (Hb, WBC, platelets). Normal ranges vary by age/sex. Recommend follow-up with provider for interpretation.',
            '"Why am I always tired?" -> Anemia is one differential among many. Ask about diet (iron), menstruation, chronic disease. Link to Hormones (thyroid).',
            '"Is sickle cell disease curable?" -> Gene therapy emerging but not standard. Hydroxyurea is mainstay. Bone marrow transplant in select cases.',
            '"What is an autoimmune disease?" -> Explain immune system attacking self. Common types: lupus, RA, MS, type 1 diabetes. Link to multiple organ categories.',
        ],
        "category_rules": [
            "CBC interpretation: always provide age and sex-specific reference ranges",
            "Anticoagulant therapy: always include bleeding risk warnings and INR monitoring for warfarin",
            "Sickle cell: crisis management is often emergency-level -- link to Emergency",
            "Immunodeficiency: always ask about medication history (steroids, chemotherapy, biologics)",
        ],
        "pitfalls": [
            "Anemia has many causes -- iron deficiency is most common but B12, folate, chronic disease, and hemolytic causes must be considered",
            "Direct oral anticoagulants (DOACs) have largely replaced warfarin for many indications -- older sources may overemphasize warfarin",
            "Immunology terminology is complex -- consumers often confuse 'immunodeficiency' with 'autoimmunity' (opposite problems)",
            "Normal lab values vary by laboratory and population -- never give absolute cutoffs without context",
        ],
        "explanation_style": "Pathology-dominant. Explanations focus on cellular morphology (blood smear findings), pathophysiology of cell line disorders, and immunological mechanisms (complement, cytokines, hypersensitivity types).",
    },

    "cancer": {
        "name": "Cancer",
        "source_subjects": "Pathology (neoplasia, tumor biology), Surgery (breast, rectal, prostate, thyroid), Medicine (oncology), Radiology (tumor imaging), Gynaecology (gynecologic oncology), Pharmacology (chemotherapy)",
        "subcategories": "Breast Cancer, Lung Cancer, GI Cancers (Colorectal, Gastric, Pancreatic, Hepatocellular), Blood Cancers (Leukemia, Lymphoma), Skin Cancer (Melanoma, BCC, SCC), Gynecologic Cancers, Prostate Cancer, Brain Tumors, Tumor Markers & Staging, Oncology Treatment Principles",
        "confidence": "High",
        "strong_links": [
            ("medications_drug_safety", "chemotherapy, targeted therapy, immunotherapy, side effects -- 20 cross-hits"),
            ("blood_immune", "hematologic malignancies, tumor immunology, paraneoplastic syndromes -- 12 cross-hits"),
            ("womens_reproductive", "breast cancer, cervical cancer, ovarian cancer, HPV link"),
        ],
        "weak_links": [
            ("digestive_liver", "GI cancers, hepatocellular carcinoma -- 24+40 cross-hits (highest overlap pair)"),
            ("breathing_lungs", "lung cancer, mesothelioma"),
            ("skin_dermatology", "melanoma, basal cell carcinoma, squamous cell carcinoma"),
            ("kidney_urinary", "renal cell carcinoma, bladder cancer, prostate cancer -- 30 cross-hits"),
        ],
        "source_priority": [
            "NCCN (National Comprehensive Cancer Network) guidelines -- gold standard for oncology",
            "WHO IARC (International Agency for Research on Cancer)",
            "PubMed clinical trials and Cochrane reviews",
            "NCI (National Cancer Institute) patient information",
            "Cancer.org (American Cancer Society) for consumer-level information",
        ],
        "source_rationale": "Cancer treatment evolves extremely rapidly (immunotherapy, targeted therapy). Guidelines are cancer-type-specific and stage-specific. ALWAYS verify recency -- a 3-year-old source may be substantially outdated.",
        "terminology": [
            ("cancer", "malignant neoplasm / carcinoma / sarcoma", "Carcinoma = epithelial, Sarcoma = mesenchymal -- important distinction"),
            ("tumor", "neoplasm", "Not all tumors are malignant -- benign vs malignant"),
            ("cancer spread", "metastasis", "Explain local invasion vs distant metastasis"),
            ("chemo", "chemotherapy / systemic therapy", "Now includes targeted therapy and immunotherapy, not just traditional chemo"),
            ("cancer stage", "TNM staging", "Explain what T, N, M mean in consumer terms"),
            ("lump / growth", "mass / lesion", "Not all lumps are cancer -- but evaluation is important"),
            ("biopsy", "tissue sampling for histopathological examination", "Explain different types: needle, excisional, incisional"),
            ("remission", "complete or partial remission", "Distinguish from 'cured' -- explain monitoring"),
        ],
        "query_patterns": [
            '"Is this lump cancer?" -> Cannot diagnose remotely. Recommend clinical evaluation. Explain what a biopsy is and why it is needed.',
            '"What is stage 4 cancer?" -> Explain TNM staging in plain language. Stage 4 = distant metastasis. Emphasize that treatment options still exist for many cancers.',
            '"Side effects of chemotherapy" -> Common: nausea, fatigue, hair loss, immunosuppression. Serious: neutropenic fever. Link to Medications.',
            '"Can cancer be prevented?" -> Modifiable risk factors: smoking, obesity, sun exposure, HPV vaccination. Screening programs by cancer type.',
        ],
        "category_rules": [
            "NEVER provide prognosis or survival statistics without explicit disclaimer that individual outcomes vary",
            "Screening guidelines differ by cancer type, age, and risk factors -- always specify which guideline",
            "Immunotherapy and targeted therapy are distinct from traditional chemotherapy -- clarify mechanism differences",
            "Tumor marker levels (CEA, PSA, CA-125) should not be interpreted in isolation -- explain context",
        ],
        "pitfalls": [
            "PSA screening controversy: USPSTF recommendations have evolved -- shared decision-making now recommended for men 55-69",
            "Immunotherapy (checkpoint inhibitors) has transformed many cancers -- sources pre-2015 may not reflect current standard of care",
            "Consumer fear of 'stage 4' may cause despair -- many stage 4 cancers now have years of quality survival with modern treatment",
            "HPV vaccine prevents cervical and other cancers -- misinformation is common in community sources",
        ],
        "explanation_style": "Pathology-centric with high TIER_A rate (81%). Explanations describe tumor biology (histology, grading, molecular markers), staging systems, and treatment protocols. PubMedQA provides strong research evidence in this category.",
    },

    "infections": {
        "name": "Infections & Infectious Disease",
        "source_subjects": "Microbiology (bacteriology, virology, parasitology, mycology), Medicine (infectious disease), Social & Preventive Medicine (communicable diseases), Pediatrics (childhood infections)",
        "subcategories": "Bacterial Infections, Viral Infections (HIV, Hepatitis, Influenza), Parasitic Infections, Fungal Infections, Tuberculosis, Sexually Transmitted Infections, Hospital-Acquired Infections, Vaccines & Immunization",
        "confidence": "High",
        "strong_links": [
            ("public_health_prevention", "epidemiology, outbreak management, vaccination programs -- 15 cross-hits"),
            ("medications_drug_safety", "antibiotics, antivirals, antifungals, antiparasitics, drug resistance"),
            ("blood_immune", "immunodeficiency and opportunistic infections, HIV/AIDS"),
        ],
        "weak_links": [
            ("breathing_lungs", "pneumonia, TB, respiratory viral infections -- 10 cross-hits"),
            ("digestive_liver", "hepatitis, GI infections, C. difficile -- 13 cross-hits"),
            ("childrens_health", "childhood infections, vaccination schedule -- 15 cross-hits"),
            ("skin_dermatology", "cellulitis, fungal skin infections, herpes, leprosy"),
        ],
        "source_priority": [
            "WHO, CDC, IDSA (Infectious Diseases Society of America) guidelines",
            "PubMed reviews on infectious disease, antimicrobial resistance",
            "MedMCQA TIER_A explanations (Ananthanarayan, Jawetz for microbiology)",
            "CDC.gov and WHO patient information",
            "Community QA -- lowest priority, very high misinformation risk (especially for vaccines)",
        ],
        "source_rationale": "Infectious disease is the fastest-evolving field. Antimicrobial resistance patterns change locally. Vaccine recommendations update annually. ALWAYS check recency and geographic applicability.",
        "terminology": [
            ("stomach bug", "viral gastroenteritis", "Not influenza -- different virus families"),
            ("superbug", "multidrug-resistant organism (MDRO)", "MRSA, VRE, CRE, ESBL -- specify which"),
            ("STD", "sexually transmitted infection (STI)", "Preferred term is now STI (includes asymptomatic infections)"),
            ("flu", "influenza", "Consumers use 'flu' for many viral illnesses -- clarify when discussing actual influenza"),
            ("food poisoning", "foodborne illness / gastroenteritis", "Multiple causative agents: Salmonella, E. coli, Staphylococcus, etc."),
            ("yeast infection", "candidiasis", "Vaginal, oral (thrush), systemic -- different contexts"),
        ],
        "query_patterns": [
            '"Do I need antibiotics?" -> Antibiotics work only for bacterial infections, NOT viral. Explain antibiotic stewardship.',
            '"Is [disease] contagious?" -> Explain transmission mode (droplet, contact, airborne, fecal-oral, vector-borne). Isolation precautions.',
            '"Are vaccines safe?" -> Reference robust safety data. Address common concerns (autism myth debunked). Cite VAERS and post-marketing surveillance.',
            '"How long is [infection] contagious?" -> Varies by pathogen. Provide specific incubation and infectious periods.',
        ],
        "category_rules": [
            "Antibiotic resistance: always mention that empiric therapy may need adjustment based on culture results",
            "Vaccine queries: counter misinformation with Tier 1 evidence only -- do not engage with debunked claims",
            "HIV: PrEP and U=U (Undetectable = Untransmittable) are current standard messaging -- verify source knows this",
            "TB: always distinguish latent from active -- treatment and public health implications differ completely",
        ],
        "pitfalls": [
            "Antibiotic resistance patterns are LOCAL -- global guidelines may not apply to specific regions",
            "COVID-19 and pandemic-era changes: many infection control practices evolved rapidly -- verify currency",
            "Hepatitis C is now curable (DAAs, 95%+ SVR) -- older sources describe it as chronic/incurable",
            "Malaria prophylaxis varies by destination -- one-size-fits-all recommendations are dangerous",
        ],
        "explanation_style": "Organism-centric. Explanations describe morphology (gram stain, culture characteristics), virulence factors, transmission, and antimicrobial susceptibility. Parasitology questions describe life cycles.",
    },

    "bones_joints_muscles": {
        "name": "Bones, Joints & Muscles",
        "source_subjects": "Orthopaedics (fractures, sports injury, congenital hip, spine injuries), Anatomy (upper/lower extremity, general), Physiology (muscle), Pathology (musculoskeletal)",
        "subcategories": "Fractures & Trauma, Arthritis (OA, RA), Spinal Disorders, Sports Injuries, Congenital Bone Disorders, Metabolic Bone Disease (Osteoporosis, Rickets), Soft Tissue Injuries",
        "confidence": "High",
        "strong_links": [
            ("emergency_critical_care", "fractures, trauma, compartment syndrome, spinal injury"),
            ("childrens_health", "congenital disorders, growth plate injuries, developmental dysplasia of hip"),
            ("medications_drug_safety", "NSAIDs, DMARDs, bisphosphonates, opioids for pain management"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "osteoporosis, vitamin D, calcium metabolism, rickets"),
            ("cancer", "bone tumors (osteosarcoma, Ewing's, metastatic bone disease)"),
            ("brain_nervous_system", "spinal cord compression, nerve entrapment syndromes"),
        ],
        "source_priority": [
            "AAOS (American Academy of Orthopaedic Surgeons) guidelines, EULAR for rheumatology",
            "PubMed reviews on orthopedic outcomes and arthritis management",
            "MedMCQA TIER_A explanations (orthopedic textbooks, anatomy texts)",
            "OrthoInfo.org (AAOS patient site), Arthritis Foundation",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "Orthopedics is highly procedural. Surgical technique choices evolve but slower than medical fields. Rheumatoid arthritis treatment has been revolutionized by biologics.",
        "terminology": [
            ("broken bone", "fracture", "Many types: simple, compound, comminuted, stress, pathological"),
            ("slipped disc", "herniated disc / HNP", "Location matters: cervical vs lumbar -- different symptoms"),
            ("arthritis", "osteoarthritis (OA) vs rheumatoid arthritis (RA)", "Degenerative vs autoimmune -- very different treatment"),
            ("torn ligament", "ligament rupture / sprain (grade III)", "ACL, MCL, etc. -- specify which ligament"),
            ("brittle bones", "osteoporosis", "Not the same as osteogenesis imperfecta (OI) -- clarify"),
            ("back pain", "lumbago / lumbar pain", "95% non-specific -- red flags: night pain, weight loss, neurological deficit"),
        ],
        "query_patterns": [
            '"Do I need surgery for a fracture?" -> Depends on fracture type, location, displacement. Many heal with conservative management (casting/splinting).',
            '"What is the difference between OA and RA?" -> OA = wear-and-tear, worse with use, asymmetric. RA = autoimmune, morning stiffness >30min, symmetric.',
            '"How to prevent osteoporosis?" -> Weight-bearing exercise, calcium, vitamin D, fall prevention. DEXA screening for at-risk populations.',
            '"When to see a doctor for back pain?" -> Red flags: bowel/bladder dysfunction, progressive weakness, fever, history of cancer, night pain.',
        ],
        "category_rules": [
            "Spinal injury with neurological deficit: always flag as emergency -- link to Emergency & Critical Care",
            "Compartment syndrome: time-critical emergency requiring fasciotomy -- include in fracture discussions",
            "Pediatric fractures: growth plate injuries have different implications -- link to Children's Health",
            "Chronic pain management: balance between adequate analgesia and opioid stewardship",
        ],
        "pitfalls": [
            "Back pain red flags are underemphasized in consumer sources -- cauda equina syndrome requires urgent surgical decompression",
            "RA treatment has been transformed by biologics (TNF inhibitors, JAK inhibitors) -- older sources may not reflect current standard",
            "Osteoporosis screening: DEXA scan recommendations vary by guideline (USPSTF vs NOF) -- specify which",
            "Sports injury management: RICE (Rest, Ice, Compression, Elevation) has been partially superseded by PEACE & LOVE framework",
        ],
        "explanation_style": "Anatomy-driven. Explanations describe anatomical landmarks, mechanism of injury (fall on outstretched hand, twisting), and surgical approaches. Clinical tests (McMurray, Lachman, Thomas) are frequently referenced.",
    },

    "kidney_urinary": {
        "name": "Kidney & Urinary Health",
        "source_subjects": "Medicine (kidney, dialysis), Surgery (urology), Anatomy (urinary tract), Physiology (renal), Pharmacology (kidney, diuretics)",
        "subcategories": "Chronic Kidney Disease, Acute Kidney Injury, Kidney Stones, Urinary Tract Infections, Dialysis, Prostate Disorders, Nephrotic/Nephritic Syndrome, Electrolyte Disorders",
        "confidence": "High",
        "strong_links": [
            ("heart_blood_vessels", "cardiorenal syndrome, renal artery stenosis, hypertension-kidney link"),
            ("medications_drug_safety", "nephrotoxic drugs, diuretics, ACE inhibitors in CKD, dose adjustment in renal failure"),
            ("infections", "UTIs, pyelonephritis"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "diabetic nephropathy, electrolyte disorders, vitamin D activation"),
            ("cancer", "renal cell carcinoma, bladder cancer, prostate cancer -- 30 cross-hits"),
            ("childrens_health", "pediatric nephrology, vesicoureteral reflux, nephrotic syndrome in children"),
        ],
        "source_priority": [
            "KDIGO (Kidney Disease: Improving Global Outcomes) guidelines",
            "AUA (American Urological Association) guidelines for urologic conditions",
            "PubMed reviews on nephrology",
            "National Kidney Foundation patient resources",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "CKD staging (KDIGO) and dialysis guidelines are well-standardized. Drug dosing in renal impairment requires careful adjustment -- always reference renal dosing guidelines.",
        "terminology": [
            ("kidney failure", "chronic kidney disease (CKD) / end-stage renal disease (ESRD)", "CKD has 5 stages -- not binary"),
            ("kidney stones", "nephrolithiasis / renal calculi", "Multiple types: calcium oxalate, uric acid, struvite, cystine"),
            ("kidney infection", "pyelonephritis", "Upper UTI -- more serious than simple cystitis"),
            ("water pill", "diuretic", "Multiple classes: loop, thiazide, potassium-sparing -- different uses"),
            ("dialysis", "hemodialysis / peritoneal dialysis", "Two major modalities -- explain differences for patient decision-making"),
            ("protein in urine", "proteinuria", "Can indicate kidney damage -- quantification matters"),
            ("UTI / bladder infection", "urinary tract infection / cystitis", "Lower vs upper UTI distinction important"),
        ],
        "query_patterns": [
            '"What do my kidney function tests mean?" -> Explain creatinine, GFR, BUN. Provide CKD stage based on GFR. Recommend provider follow-up.',
            '"How to prevent kidney stones?" -> Hydration (2-3L/day), dietary modification based on stone type, reduce sodium. Stone analysis guides prevention.',
            '"When do I need dialysis?" -> GFR <15 or symptoms of uremia. Explain options (hemodialysis vs peritoneal). Not emergency unless acute indications.',
            '"Can a UTI become serious?" -> Untreated lower UTI can progress to pyelonephritis, urosepsis. Red flags: fever, flank pain, confusion in elderly.',
        ],
        "category_rules": [
            "Drug dosing: always check if renal dose adjustment is needed -- many drugs accumulate in CKD",
            "Electrolyte disorders (hyperkalemia, hyponatremia): can be life-threatening -- link to Emergency when acute",
            "Prostate queries in older men: distinguish BPH from prostate cancer -- different management entirely",
            "UTIs: recurrent UTIs in women vs UTIs in men have different evaluation pathways",
        ],
        "pitfalls": [
            "CKD staging uses GFR categories AND albuminuria categories (KDIGO heat map) -- older sources use GFR only",
            "Contrast-induced nephropathy risk may be overestimated in recent evidence -- older protocols overly restrictive",
            "ACE inhibitors in CKD: beneficial despite initial GFR drop -- don't discontinue based on small creatinine rise (up to 30%)",
            "PSA screening for prostate cancer: separate from urinary/kidney issues -- route to Cancer category",
        ],
        "explanation_style": "Physiology-heavy for renal questions (filtration, reabsorption, electrolyte handling). Surgery-oriented for urological questions (stone management, prostate surgery). Heavy emphasis on lab value interpretation.",
    },

    "womens_reproductive": {
        "name": "Women's & Reproductive Health",
        "source_subjects": "Gynaecology & Obstetrics (oncology, contraception, pregnancy complications, menstrual disorders, STDs, anatomy, fetal monitoring), Medicine, Pharmacology",
        "subcategories": "Pregnancy & Childbirth, Contraception, Menstrual Disorders, Gynecologic Cancers, Infertility, STIs in Women, Menopause, Pre-eclampsia & Pregnancy Complications, Polycystic Ovary Syndrome (PCOS)",
        "confidence": "High",
        "strong_links": [
            ("cancer", "breast cancer, cervical cancer, ovarian cancer, endometrial cancer"),
            ("childrens_health", "pregnancy-neonatal continuum, teratogenic exposures, breastfeeding"),
            ("medications_drug_safety", "contraceptives, drugs in pregnancy (teratogenicity), hormone therapy"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "PCOS, thyroid-menstrual link, gestational diabetes"),
            ("infections", "STIs, TORCH infections in pregnancy"),
            ("mental_health", "postpartum depression, premenstrual dysphoric disorder"),
        ],
        "source_priority": [
            "ACOG (American College of Obstetricians and Gynecologists) guidelines",
            "WHO reproductive health guidelines, RCOG (Royal College)",
            "PubMed reviews on obstetrics and gynecology",
            "MedMCQA TIER_A explanations (Shaw's, Dutta's)",
            "Planned Parenthood, womenshealth.gov for consumer information",
        ],
        "source_rationale": "Obstetric and gynecologic guidelines are updated regularly. Drug safety in pregnancy (FDA categories replaced by narrative labeling in 2015) requires careful sourcing.",
        "terminology": [
            ("period problems", "menstrual disorders (amenorrhea, menorrhagia, dysmenorrhea)", "Specify which problem: absent, heavy, or painful periods"),
            ("morning sickness", "nausea and vomiting of pregnancy (NVP) / hyperemesis gravidarum", "Distinguish mild NVP from severe hyperemesis"),
            ("birth control", "contraception", "Many methods: hormonal, barrier, IUD, natural -- effectiveness varies widely"),
            ("hot flashes", "vasomotor symptoms of menopause", "Treatment options: HRT, SSRIs, lifestyle changes"),
            ("miscarriage", "spontaneous abortion", "Medical term may be distressing to patients -- use 'miscarriage' or 'pregnancy loss'"),
            ("cervical smear / Pap test", "cervical cytology / Pap smear", "Screening for cervical pre-cancer -- now co-tested with HPV"),
        ],
        "query_patterns": [
            '"Is this normal during pregnancy?" -> Ask about trimester, specific symptom. Common concerns: bleeding (threatened miscarriage vs normal), contractions, decreased fetal movement.',
            '"Which birth control is best?" -> Depends on patient factors. Most effective: IUD, implant. Most common: pills. Discuss with provider for personalized choice.',
            '"What are PCOS symptoms?" -> Irregular periods, hirsutism, acne, weight gain, infertility. Explain metabolic implications. Link to Hormones.',
            '"When should I worry about heavy periods?" -> Changing pad/tampon every 1-2 hours, clots >1 inch, anemia symptoms. Evaluate for fibroids, polyps, endometrial causes.',
        ],
        "category_rules": [
            "Drug safety in pregnancy: never recommend any medication without checking teratogenicity. Use LactMed for breastfeeding.",
            "Emergency obstetric conditions (eclampsia, placental abruption, ectopic pregnancy): always link to Emergency",
            "Cervical cancer screening: guidelines differ by age and HPV status -- always specify which guideline",
            "Sensitive language: use 'pregnancy loss' or 'miscarriage' rather than 'spontaneous abortion' in consumer-facing content",
        ],
        "pitfalls": [
            "FDA pregnancy categories (A, B, C, D, X) were officially replaced by narrative labeling in 2015 -- older sources still use them",
            "Hormone replacement therapy (HRT): WHI trial findings were nuanced -- benefits outweigh risks for most women starting within 10 years of menopause",
            "HPV vaccine now recommended for all genders up to age 45 -- older sources limit to women only",
            "Ectopic pregnancy can be life-threatening -- always flag when patient reports early pregnancy + abdominal pain + bleeding",
        ],
        "explanation_style": "Clinical presentation-oriented. Explanations describe obstetric management protocols, contraceptive mechanisms, and oncologic staging. Heavy emphasis on clinical decision-making and patient counseling.",
    },

    "childrens_health": {
        "name": "Children's Health",
        "source_subjects": "Pediatrics (newborn, CVS, infections, metabolism, development, fluid/electrolyte, neoplastic disorders), Medicine",
        "subcategories": "Newborn Care, Growth & Development Milestones, Childhood Infections, Congenital Disorders, Pediatric Nutrition, Childhood Cancers, Inborn Errors of Metabolism, Vaccination Schedule, Pediatric Emergencies",
        "confidence": "High",
        "strong_links": [
            ("infections", "childhood infections, vaccine-preventable diseases -- 15 cross-hits"),
            ("womens_reproductive", "pregnancy-neonatal continuum, congenital conditions"),
            ("hormones_metabolism_nutrition", "growth disorders, inborn errors of metabolism, pediatric nutrition"),
        ],
        "weak_links": [
            ("breathing_lungs", "pediatric asthma, croup, bronchiolitis -- 9 cross-hits"),
            ("bones_joints_muscles", "growth plate injuries, developmental dysplasia, congenital conditions"),
            ("ear_nose_throat", "otitis media, tonsillitis -- common pediatric ENT -- 14 cross-hits"),
            ("dental_oral", "pediatric dentistry, fluoride -- 9 cross-hits"),
        ],
        "source_priority": [
            "AAP (American Academy of Pediatrics) guidelines, WHO child health",
            "CDC immunization schedule, Bright Futures preventive care",
            "PubMed reviews on pediatrics",
            "MedMCQA TIER_A explanations (Nelson's, OP Ghai)",
            "HealthyChildren.org (AAP parent site)",
        ],
        "source_rationale": "Pediatric drug dosing is weight-based and age-dependent -- adult doses are NOT applicable. Vaccination schedules update annually. Developmental milestones are age-specific.",
        "terminology": [
            ("immunizations / shots", "vaccinations", "Follow CDC schedule. Address parental vaccine hesitancy with Tier 1 evidence."),
            ("growth chart", "anthropometric assessment / growth percentiles", "Explain percentile concept in plain language"),
            ("failure to thrive", "faltering growth", "Inadequate weight gain -- many causes (nutritional, organic, psychosocial)"),
            ("febrile seizure", "febrile convulsion", "Common (2-5% of children), usually benign -- but frightening for parents"),
            ("blue baby", "cyanotic congenital heart disease", "e.g., Tetralogy of Fallot, TGA -- requires specialist care"),
            ("lazy eye", "amblyopia", "Different from strabismus (misaligned eyes) -- though often related"),
        ],
        "query_patterns": [
            '"Is my child developing normally?" -> Reference WHO/CDC milestones for specific age. Ranges are wide. Recommend pediatrician evaluation if concerned.',
            '"My child has a fever -- when to worry?" -> Age matters critically. Neonate <28 days + fever = emergency. Older: look for source, hydration, activity level.',
            '"What vaccines does my baby need?" -> Reference current CDC schedule. Address common concerns. Explain herd immunity.',
            '"When can I introduce solid foods?" -> Around 6 months (WHO). Signs of readiness: sitting with support, interest in food, loss of tongue-thrust reflex.',
        ],
        "category_rules": [
            "CRITICAL: Neonatal fever (<28 days) is always a medical emergency -- flag urgently",
            "Drug dosing: ALWAYS weight-based in children. Never extrapolate from adult doses.",
            "Developmental milestones: provide ranges, not single-age cutoffs. Each child develops differently.",
            "Vaccination: use only Tier 1 evidence. Do not engage with debunked anti-vaccine claims.",
        ],
        "pitfalls": [
            "Aspirin is contraindicated in children (Reye's syndrome risk) -- use paracetamol/ibuprofen for fever",
            "Neonatal jaundice: physiological vs pathological -- timing of onset is key differentiator",
            "Febrile seizures are frightening but usually benign -- avoid alarmist language while ensuring parents know when to seek care",
            "Growth percentile crossing: one measurement is not a trend -- serial measurements needed",
        ],
        "explanation_style": "Age-specific and milestone-oriented. Explanations frequently reference developmental stages, weight-based calculations, and pediatric-specific disease presentations (which often differ from adult presentations).",
    },

    "eye_health": {
        "name": "Eye Health",
        "source_subjects": "Ophthalmology (uveal tract, conjunctiva, orbit, retina, cornea, glaucoma, community ophthalmology, lens)",
        "subcategories": "Glaucoma, Cataracts, Retinal Diseases, Uveitis, Corneal Disorders, Refractive Errors, Eye Infections, Strabismus & Amblyopia, Diabetic Eye Disease",
        "confidence": "High",
        "strong_links": [
            ("hormones_metabolism_nutrition", "diabetic retinopathy -- diabetes is leading cause of preventable blindness"),
            ("infections", "conjunctivitis, keratitis, endophthalmitis, orbital cellulitis"),
            ("medications_drug_safety", "ophthalmic drugs (timolol, latanoprost), drug-induced eye conditions (steroids → glaucoma)"),
        ],
        "weak_links": [
            ("brain_nervous_system", "optic nerve pathology, visual field defects in stroke, papilledema"),
            ("childrens_health", "pediatric ophthalmology, amblyopia screening, retinopathy of prematurity"),
        ],
        "source_priority": [
            "AAO (American Academy of Ophthalmology) guidelines",
            "PubMed reviews on ophthalmology",
            "MedMCQA TIER_A explanations (Khurana, Yanoff)",
            "NEI (National Eye Institute) patient information",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "Ophthalmology is highly specialized. Visual symptoms often require clinical examination (slit lamp, fundoscopy) for diagnosis. Remote assessment is limited.",
        "terminology": [
            ("eye pressure", "intraocular pressure (IOP)", "Elevated IOP is a risk factor for glaucoma but not the only one"),
            ("nearsighted / farsighted", "myopia / hyperopia", "Refractive errors correctable with lenses/surgery"),
            ("pink eye", "conjunctivitis", "Viral, bacterial, or allergic -- different treatment for each"),
            ("floaters", "vitreous floaters", "Usually benign but sudden onset with flashes → retinal detachment → emergency"),
            ("cataract", "lens opacity", "Age-related is most common -- explain surgical option (phacoemulsification)"),
            ("lazy eye", "amblyopia", "Different from strabismus -- but often related"),
        ],
        "query_patterns": [
            '"Why am I seeing floaters?" -> Usually benign age-related vitreous changes. Red flags: sudden onset, flashes, curtain/shadow in vision → possible retinal detachment → Emergency.',
            '"How often should I get my eyes checked?" -> Depends on age and risk factors. Diabetics: annual dilated exam. General: every 1-2 years after age 40.',
            '"Can glaucoma be cured?" -> No cure but progression can be slowed/stopped with treatment. Eye drops, laser, surgery. Emphasize adherence.',
            '"Do I need surgery for cataracts?" -> Only when vision impairment affects daily activities. Modern surgery (phaco) is highly safe and effective.',
        ],
        "category_rules": [
            "Sudden vision loss: ALWAYS flag as emergency -- requires same-day ophthalmologic evaluation",
            "Retinal detachment symptoms (floaters + flashes + curtain): emergency referral",
            "Diabetic eye disease: link to Hormones -- stress annual screening importance",
            "Steroid eye drops: mention IOP monitoring requirement (steroid-induced glaucoma risk)",
        ],
        "pitfalls": [
            "Red eye differential is broad: conjunctivitis vs acute glaucoma vs uveitis vs foreign body -- severity varies enormously",
            "'Glaucoma' encompasses multiple types (open-angle, angle-closure, normal-tension) -- treatment differs",
            "Contact lens complications (microbial keratitis) are underappreciated by consumers",
            "Over-the-counter eye drops (redness relievers) can mask serious pathology -- not a substitute for evaluation",
        ],
        "explanation_style": "Anatomy-centric. Explanations describe ocular structures (cornea, lens, retina, uvea), examination techniques (slit lamp, gonioscopy), and surgical procedures. Heavy use of clinical signs (e.g., Marcus Gunn pupil, keratic precipitates).",
    },

    "ear_nose_throat": {
        "name": "Ear, Nose & Throat",
        "source_subjects": "ENT (nose and PNS, ear, facial nerve, vestibular function, larynx, pharynx)",
        "subcategories": "Sinusitis & Nasal Disorders, Hearing Loss & Ear Infections, Throat & Larynx, Vertigo & Balance Disorders, Facial Nerve Disorders, Head & Neck Tumors, Tonsils & Adenoids, Epistaxis",
        "confidence": "High",
        "strong_links": [
            ("infections", "otitis media, sinusitis, pharyngitis, tonsillitis -- common infectious ENT"),
            ("childrens_health", "pediatric ENT (otitis media, tonsillectomy, adenoids, hearing screening) -- 14 cross-hits"),
            ("cancer", "head and neck cancers (laryngeal, oropharyngeal, nasopharyngeal)"),
        ],
        "weak_links": [
            ("breathing_lungs", "upper airway obstruction, laryngeal conditions"),
            ("dental_oral", "oral-facial overlap, TMJ, salivary gland disorders -- 12 cross-hits"),
            ("brain_nervous_system", "facial nerve palsy, vestibular disorders (central vs peripheral)"),
        ],
        "source_priority": [
            "AAO-HNS (American Academy of Otolaryngology) guidelines",
            "PubMed reviews on otolaryngology",
            "MedMCQA TIER_A explanations (Dhingra, Scott Brown)",
            "ENTHealth.org (AAO-HNS patient site)",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "ENT conditions are among the most common reasons for primary care visits. Antibiotic stewardship is critical (most sinusitis and otitis are viral initially).",
        "terminology": [
            ("ear infection", "otitis media (middle ear) / otitis externa (outer ear)", "Different treatment for each"),
            ("sinus infection", "rhinosinusitis", "Viral (most common) vs bacterial -- antibiotics only for bacterial"),
            ("dizziness / vertigo", "vertigo (spinning) vs lightheadedness (presyncope)", "Critical distinction -- different causes and management"),
            ("hearing loss", "sensorineural vs conductive hearing loss", "Conductive may be treatable, sensorineural often permanent"),
            ("nosebleed", "epistaxis", "Anterior (common, usually benign) vs posterior (less common, can be serious)"),
            ("sore throat", "pharyngitis / tonsillitis", "Viral (most common) vs bacterial (strep throat) -- determines if antibiotics needed"),
            ("ringing in ears", "tinnitus", "Symptom with many causes -- often no cure but management strategies exist"),
        ],
        "query_patterns": [
            '"Do I need antibiotics for a sinus infection?" -> Most sinusitis is viral (first 10 days). Bacterial suspected if: symptoms >10 days, double worsening, severe onset. Watchful waiting first.',
            '"Why am I dizzy?" -> Differentiate vertigo (room spinning -- inner ear/vestibular) from lightheadedness (presyncope -- cardiovascular). BPPV is most common cause of vertigo.',
            '"My child has recurrent ear infections -- should we do tubes?" -> Tympanostomy tubes considered for: 3+ episodes in 6 months or 4+ in 12 months with persistent effusion.',
            '"Can hearing loss be reversed?" -> Depends on type. Conductive (wax, fluid, ossicle fixation): often yes. Sensorineural: hearing aids, cochlear implant, but rarely reversed.',
        ],
        "category_rules": [
            "Strep throat testing: Centor/McIsaac criteria guide who needs testing and antibiotics",
            "BPPV: Epley maneuver is first-line treatment -- explain or reference instructional resources",
            "Sudden sensorineural hearing loss: requires urgent ENT referral (steroid treatment within 72h)",
            "Epistaxis: anterior bleeds managed with direct pressure -- posterior bleeds may need ENT intervention",
        ],
        "pitfalls": [
            "Antibiotic overuse for viral URI/sinusitis is a major stewardship issue -- many consumers expect antibiotics unnecessarily",
            "Vertigo vs dizziness: consumers use these interchangeably but they indicate different pathology",
            "'Tonsillectomy' indications have become more conservative -- not indicated for every recurrent sore throat",
            "Hearing loss in elderly is underdiagnosed and undertreated -- normalize hearing aid use",
        ],
        "explanation_style": "Clinical examination-oriented. Explanations describe tuning fork tests (Rinne, Weber), endoscopic findings, and surgical anatomy (middle ear ossicles, paranasal sinuses). Vestibular physiology questions are physiology-heavy.",
    },

    "skin_dermatology": {
        "name": "Skin & Dermatology",
        "source_subjects": "Skin (psoriasis, fungal infections, drug reactions), Pathology (dermatology), Dental (autoimmune skin disorders), Microbiology (skin infections)",
        "subcategories": "Psoriasis, Eczema & Dermatitis, Skin Infections (Fungal, Bacterial, Viral), Skin Cancer (Melanoma, BCC, SCC), Autoimmune Skin Disorders (Pemphigus, Lupus Skin), Drug Reactions, Acne, Wound Healing, Urticaria & Allergic Skin",
        "confidence": "Medium",
        "strong_links": [
            ("infections", "cellulitis, fungal skin infections, herpes, leprosy, scabies"),
            ("medications_drug_safety", "drug eruptions (SJS/TEN, fixed drug eruption), topical therapies"),
            ("cancer", "melanoma, basal cell carcinoma, squamous cell carcinoma"),
        ],
        "weak_links": [
            ("blood_immune", "autoimmune skin disorders (lupus skin, dermatomyositis)"),
            ("childrens_health", "pediatric dermatology (eczema, birthmarks, diaper rash)"),
        ],
        "source_priority": [
            "AAD (American Academy of Dermatology) guidelines, BAD (British Association of Dermatologists)",
            "PubMed reviews on dermatology",
            "MedMCQA TIER_A explanations",
            "DermNet NZ (comprehensive dermatology resource)",
            "Community QA -- lowest priority but consumer photos can be helpful for description",
        ],
        "source_rationale": "Dermatology is highly visual -- text descriptions have limitations. Biologic therapies for psoriasis and eczema are rapidly evolving.",
        "terminology": [
            ("rash", "dermatitis / exanthem / eruption", "Extremely broad term -- need characterization (location, morphology, distribution)"),
            ("eczema", "atopic dermatitis", "Chronic, relapsing. Different from contact dermatitis."),
            ("hives", "urticaria", "Allergic or non-allergic. Acute (<6 weeks) vs chronic."),
            ("mole", "melanocytic nevus", "Most are benign. ABCDE criteria for melanoma screening."),
            ("ringworm", "tinea / dermatophyte infection", "Not actually a worm -- fungal infection"),
            ("cold sore", "herpes simplex labialis (HSV-1)", "Recurrent viral infection. Antiviral treatment available."),
        ],
        "query_patterns": [
            '"Is this rash serious?" -> Cannot diagnose from description alone. Red flags: rapid spread, blistering, mucosal involvement (SJS/TEN), fever + rash. Recommend dermatology evaluation.',
            '"What is the ABCDE rule for moles?" -> Asymmetry, Border irregularity, Color variation, Diameter >6mm, Evolving. Screening tool for melanoma.',
            '"How to treat eczema?" -> Moisturization, topical steroids (appropriate potency for location), trigger avoidance. Biologics (dupilumab) for severe cases.',
            '"Is psoriasis contagious?" -> NO -- autoimmune condition, not infectious. Important misconception to address clearly.',
        ],
        "category_rules": [
            "Suspected SJS/TEN (drug-induced blistering + mucosal involvement): EMERGENCY -- link to Emergency",
            "Skin cancer screening: ABCDE criteria for melanoma, but BCC/SCC have different features",
            "Topical steroid potency: face and flexures need mild steroids -- strong steroids cause atrophy",
            "Dermatology is inherently visual -- acknowledge limitations of text-only assessment",
        ],
        "pitfalls": [
            "Topical steroid phobia is common among consumers -- balanced communication about appropriate use",
            "Biologic therapies for psoriasis (IL-17, IL-23 inhibitors) are highly effective but newer sources needed",
            "SJS/TEN is rare but life-threatening -- any new rash + drug exposure + mucosal involvement requires emergency evaluation",
            "Melanoma can occur in sun-protected areas and in people of all skin colors -- screening should not be limited",
        ],
        "explanation_style": "Morphology-descriptive. Explanations describe lesion characteristics (macules, papules, vesicles, plaques), distribution patterns, and histopathological findings. Heavy reliance on visual pattern recognition.",
    },

    "medications_drug_safety": {
        "name": "Medications & Drug Safety",
        "source_subjects": "Pharmacology (ALL -- autonomic NS, CNS, CVS, respiratory, anesthesia, chemotherapy, antibiotics, general pharmacology, pharmacodynamics, pharmacokinetics)",
        "subcategories": "Antibiotics & Antimicrobials, Pain Medications & NSAIDs, Cardiac Drugs, Psychiatric Medications, Chemotherapy & Targeted Therapy, Anesthetics, Drug Side Effects & Interactions, Pharmacokinetics Basics, Over-the-Counter Medications",
        "confidence": "High",
        "strong_links": [
            ("heart_blood_vessels", "antihypertensives, anticoagulants, statins, anti-arrhythmics -- 150 secondary tags"),
            ("mental_health", "antidepressants, antipsychotics, mood stabilizers, anxiolytics -- 10 cross-hits"),
            ("cancer", "chemotherapy, targeted therapy, immunotherapy side effects -- 20 cross-hits"),
        ],
        "weak_links": [
            ("infections", "antibiotics, antivirals, antifungals -- drug resistance concerns"),
            ("hormones_metabolism_nutrition", "insulin, thyroid drugs, corticosteroids -- 20 cross-hits"),
            ("kidney_urinary", "drug dosing in renal impairment, nephrotoxic drugs"),
            ("brain_nervous_system", "anticonvulsants, anti-Parkinson drugs, opioids -- 13 cross-hits"),
        ],
        "source_priority": [
            "FDA drug labels, EMA SmPCs -- gold standard for drug information",
            "UpToDate/Lexicomp drug monographs, BNF (British National Formulary)",
            "PubMed pharmacology reviews, Cochrane reviews on drug efficacy",
            "MedMCQA TIER_A explanations (KD Tripathi, Goodman & Gilman)",
            "Drugs.com, WebMD drug pages for consumer information",
        ],
        "source_rationale": "THIS IS THE CROSS-CUTTING CATEGORY. Almost every clinical question has a drug component. Drug information requires the highest accuracy standard -- errors can cause direct harm. Always use Tier 1 sources for dosing and interactions.",
        "terminology": [
            ("side effects", "adverse drug reactions (ADRs)", "Common (predictable, dose-dependent) vs idiosyncratic (unpredictable)"),
            ("drug interaction", "drug-drug interaction (DDI)", "Pharmacokinetic (CYP450) vs pharmacodynamic interactions"),
            ("generic vs brand", "generic / brand-name medication", "Bioequivalent by regulation -- same active ingredient"),
            ("blood thinner", "anticoagulant (warfarin, DOACs) vs antiplatelet (aspirin, clopidogrel)", "Different mechanisms -- critical distinction"),
            ("painkiller", "analgesic (paracetamol, NSAIDs, opioids)", "Three distinct classes with different risk profiles"),
            ("antibiotic resistance", "antimicrobial resistance (AMR)", "Explain why completing courses and not sharing antibiotics matters"),
        ],
        "query_patterns": [
            '"What are the side effects of [drug]?" -> Reference FDA label. Distinguish common, uncommon, and serious ADRs. Include black box warnings if applicable.',
            '"Can I take [drug A] with [drug B]?" -> Check interaction databases (Lexicomp, Micromedex). CYP450 interactions are most common. Recommend pharmacist consultation.',
            '"Is the generic version as good as the brand?" -> Yes, FDA requires bioequivalence. Exceptions rare (narrow therapeutic index drugs: warfarin, levothyroxine, phenytoin).',
            '"Can I stop taking my medication?" -> NEVER advise stopping medication without provider consultation. Some drugs require tapering (SSRIs, steroids, beta-blockers).',
        ],
        "category_rules": [
            "NEVER provide specific dosing advice -- always defer to prescriber/pharmacist",
            "Drug interactions: verify against 2+ independent databases before including",
            "Pregnancy/breastfeeding: always check teratogenicity. Use LactMed for breastfeeding safety.",
            "Narrow therapeutic index drugs (warfarin, digoxin, lithium, phenytoin): emphasize monitoring importance",
            "Polypharmacy in elderly: flag when multiple drug interactions are possible",
        ],
        "pitfalls": [
            "OTC medications can cause serious harm (paracetamol hepatotoxicity, NSAID GI bleeding, antihistamine sedation)",
            "Herbal/supplement interactions are underappreciated by consumers (St. John's Wort + many drugs, grapefruit + statins)",
            "Antibiotic courses: 'finish the full course' dogma is being nuanced by recent evidence -- but still default advice for most infections",
            "Drug names vary by country (paracetamol vs acetaminophen, adrenaline vs epinephrine) -- clarify for international users",
        ],
        "explanation_style": "Mechanism-of-action focused. Explanations describe receptor pharmacology (agonist/antagonist), drug metabolism (CYP450 pathways), and pharmacokinetic parameters (half-life, bioavailability, protein binding). Classification-heavy (beta-blockers: selective vs non-selective).",
    },

    "hormones_metabolism_nutrition": {
        "name": "Hormones, Metabolism & Nutrition",
        "source_subjects": "Medicine (endocrinology), Physiology (endocrine system), Biochemistry (metabolism, vitamins, enzymes, amino acids, carbohydrates), Pathology (endocrine), Surgery (thyroid, adrenal, breast)",
        "subcategories": "Diabetes (Type 1, Type 2, Gestational), Thyroid Disorders, Vitamin Deficiencies & Supplements, Metabolic Syndrome, Inborn Errors of Metabolism, Adrenal Disorders (Cushing's, Addison's), Pituitary Disorders, Nutrition & Dietary Guidelines, Obesity",
        "confidence": "High",
        "strong_links": [
            ("heart_blood_vessels", "diabetes as cardiovascular risk factor, metabolic syndrome, lipid disorders"),
            ("kidney_urinary", "diabetic nephropathy, electrolyte disorders, acid-base balance"),
            ("medications_drug_safety", "insulin, oral hypoglycemics, thyroid drugs, steroids -- 20 cross-hits"),
        ],
        "weak_links": [
            ("eye_health", "diabetic retinopathy"),
            ("childrens_health", "growth disorders, inborn errors of metabolism, pediatric diabetes"),
            ("brain_nervous_system", "diabetic neuropathy, metabolic encephalopathy"),
            ("womens_reproductive", "PCOS, gestational diabetes, thyroid in pregnancy"),
        ],
        "source_priority": [
            "ADA (American Diabetes Association) Standards of Care (updated annually), Endocrine Society guidelines",
            "ATA (American Thyroid Association) guidelines",
            "PubMed reviews on endocrinology and metabolism",
            "MedMCQA TIER_A explanations (Harrison's endocrinology, Harper's biochemistry)",
            "Diabetes.org, thyroid.org for consumer information",
        ],
        "source_rationale": "Diabetes management evolves rapidly (GLP-1 agonists, SGLT2 inhibitors, CGM technology). ADA Standards of Care update annually. Always check the year of guidelines cited.",
        "terminology": [
            ("sugar / blood sugar", "blood glucose / glycemia", "Fasting vs random vs postprandial -- different thresholds"),
            ("diabetes", "diabetes mellitus (type 1, type 2, gestational)", "Three distinct conditions -- treatment differs fundamentally"),
            ("thyroid problem", "hypothyroidism / hyperthyroidism", "Opposite conditions -- both called 'thyroid problem' by consumers"),
            ("vitamin deficiency", "micronutrient deficiency", "Specify which vitamin (B12, D, iron, folate) -- different causes and treatments"),
            ("metabolism", "basal metabolic rate / metabolic processes", "Consumer use is vague ('fast/slow metabolism') vs clinical meaning"),
            ("hormonal imbalance", "endocrine disorder", "Non-specific consumer term -- needs clarification of which hormones"),
            ("obesity", "obesity (BMI >=30)", "Now classified as a chronic disease -- not a lifestyle choice"),
        ],
        "query_patterns": [
            '"What is my A1C target?" -> Generally <7% for most adults (ADA). Individualized: tighter for young/healthy, looser for elderly/comorbid. Explain what A1C measures.',
            '"Should I take vitamin D supplements?" -> Check levels first. Deficiency (<20 ng/mL): supplement. Insufficiency (20-30): consider. Sufficient (>30): not needed.',
            '"What foods should diabetics avoid?" -> Nuanced -- no single food is banned. Focus on carb quality, portion control, glycemic index. Avoid absolutist dietary advice.',
            '"Is my thyroid causing my weight gain?" -> Hypothyroidism causes modest weight gain (5-10 lbs). Significant obesity is rarely thyroid-alone. Test TSH.',
        ],
        "category_rules": [
            "Diabetes management: always include lifestyle measures alongside pharmacotherapy",
            "Thyroid nodules: distinguish benign from malignant (FNA biopsy). Most nodules are benign.",
            "Vitamin supplementation: evidence-based only. Mega-dosing is not recommended without deficiency.",
            "Inborn errors of metabolism: link to Children's Health (most diagnosed in infancy/childhood)",
            "Obesity: use non-stigmatizing language. Frame as chronic disease, not personal failure.",
        ],
        "pitfalls": [
            "Diabetes treatment has shifted dramatically: GLP-1 agonists and SGLT2 inhibitors now have cardiovascular and renal benefits beyond glucose control -- older sources don't reflect this",
            "Thyroid storm and myxedema coma are endocrine emergencies -- link to Emergency",
            "Vitamin D: optimal level is debated (20 vs 30 ng/mL) -- different guidelines disagree",
            "Metabolic syndrome criteria differ between IDF and ATP III definitions -- specify which",
        ],
        "explanation_style": "Biochemistry-heavy for metabolism questions (enzymatic pathways, Krebs cycle, glycolysis). Endocrinology questions focus on hormonal axes (HPA, HPT, HPG) and feedback loops. Clinical questions emphasize lab interpretation (TSH, A1C, fasting glucose).",
    },

    "emergency_critical_care": {
        "name": "Emergency & Critical Care",
        "source_subjects": "Surgery (trauma), Anaesthesia (complications, agents), Medicine (toxicology, acute presentations), Forensic Medicine (injuries, poisoning, thermal injury, medico-legal)",
        "subcategories": "Trauma & Fractures, Burns, Poisoning & Toxicology, CPR & Resuscitation, Shock (Hypovolemic, Cardiogenic, Septic), Anesthesia & Pain Management, Surgical Emergencies, Snakebite & Envenomation, Forensic & Legal Medicine",
        "confidence": "Medium",
        "strong_links": [
            ("heart_blood_vessels", "cardiac arrest, acute MI, hypertensive emergency -- 16 cross-hits"),
            ("bones_joints_muscles", "fractures, trauma, spinal injury, compartment syndrome"),
            ("breathing_lungs", "respiratory failure, PE, tension pneumothorax, airway management"),
        ],
        "weak_links": [
            ("brain_nervous_system", "stroke, head injury, raised intracranial pressure"),
            ("medications_drug_safety", "overdose, toxicology, anesthetic agents, reversal agents"),
            ("digestive_liver", "acute abdomen, GI hemorrhage, toxicology (paracetamol overdose → liver failure)"),
        ],
        "source_priority": [
            "AHA/ERC CPR and emergency cardiovascular care guidelines (updated every 5 years)",
            "ATLS (Advanced Trauma Life Support) protocols",
            "PubMed reviews on emergency medicine and critical care",
            "MedMCQA TIER_A explanations (surgery and anesthesia texts)",
            "MedlinePlus first aid information",
        ],
        "source_rationale": "Emergency medicine is protocol-driven and time-critical. ACLS/BLS/ATLS/PALS are standardized. Toxicology management varies by agent. Always verify current antidote availability.",
        "terminology": [
            ("CPR", "cardiopulmonary resuscitation", "Hands-only CPR for bystanders. Full CPR with rescue breaths for trained responders."),
            ("shock", "circulatory shock", "Not emotional shock. Multiple types: hypovolemic, cardiogenic, distributive (septic, anaphylactic), obstructive."),
            ("concussion", "mild traumatic brain injury (mTBI)", "Loss of consciousness not required for diagnosis"),
            ("overdose", "drug overdose / poisoning", "Intentional vs accidental. Antidote-specific management."),
            ("burn", "thermal injury", "Classified by depth (superficial, partial, full thickness) and TBSA percentage"),
            ("anaphylaxis", "anaphylactic shock", "Life-threatening allergic reaction. Epinephrine is first-line treatment."),
        ],
        "query_patterns": [
            '"How to do CPR?" -> Current AHA guidelines: push hard, push fast (100-120/min), 2 inches deep. Hands-only CPR for untrained. Call 911 first.',
            '"What to do for a burn?" -> Cool running water for 20 minutes. Do NOT use ice, butter, or toothpaste. Cover loosely. Seek medical attention for large/deep burns.',
            '"My child swallowed [substance]" -> IMMEDIATELY: call Poison Control (1-800-222-1222 in US). Do NOT induce vomiting unless instructed. Bring container to ED.',
            '"Signs of a concussion" -> Headache, confusion, dizziness, nausea, amnesia. Rest and avoid screens initially. Seek evaluation if symptoms worsen.',
        ],
        "category_rules": [
            "ALWAYS prepend emergency queries with: 'If this is an emergency, call 911 or your local emergency number.'",
            "Time-critical conditions: stroke (golden hour), STEMI (door-to-balloon), trauma (golden hour), anaphylaxis (epinephrine NOW)",
            "Poisoning/overdose: always recommend Poison Control and ED evaluation -- do not provide home treatment advice for toxic ingestions",
            "Forensic Medicine questions: provide factual information only -- do not speculate on legal matters",
        ],
        "pitfalls": [
            "CPR ratio changed: 30:2 is standard (not 15:2 which was pediatric-only). Hands-only CPR is now recommended for untrained bystanders.",
            "Activated charcoal for poisoning: no longer universally recommended -- timing and substance matter",
            "Tourniquet use: has been rehabilitated for severe hemorrhage (MARCH protocol) -- older sources discouraged it",
            "'Concussion' terminology: now recognized as mTBI with potentially prolonged recovery -- not 'just a bump on the head'",
        ],
        "explanation_style": "Protocol-driven. Explanations follow ABCDE approach (Airway, Breathing, Circulation, Disability, Exposure), ATLS primary/secondary survey, and specific management algorithms. Anesthesia questions focus on drug pharmacology and airway management.",
    },

    "dental_oral": {
        "name": "Dental & Oral Health",
        "source_subjects": "Dental (restorative, endodontics, periodontics, oral pathology, orthodontics, oral surgery, community dentistry, dental materials, prosthodontics)",
        "subcategories": "Tooth Decay & Fillings, Gum Disease (Periodontics), Oral Cancer, Dental Materials, Orthodontics, Oral Infections, TMJ Disorders, Dental Emergencies, Prosthodontics",
        "confidence": "Medium",
        "strong_links": [
            ("ear_nose_throat", "oral-facial anatomy overlap, salivary gland disorders, oral-antral fistula -- 12 cross-hits"),
            ("infections", "dental infections, oral candidiasis, Ludwig's angina"),
            ("childrens_health", "pediatric dentistry, fluoride, teething, dental trauma in children -- 9 cross-hits"),
        ],
        "weak_links": [
            ("cancer", "oral cancer (squamous cell carcinoma), salivary gland tumors"),
            ("medications_drug_safety", "dental anesthesia, analgesics, antibiotic prophylaxis"),
        ],
        "source_priority": [
            "ADA (American Dental Association) guidelines",
            "PubMed reviews on dentistry and oral health",
            "MedMCQA explanations (CAUTION: 51% null explanations in Dental -- lowest quality)",
            "MouthHealthy.org (ADA patient site)",
            "Community QA -- lowest priority",
        ],
        "source_rationale": "DATA QUALITY WARNING: Dental has the highest null explanation rate (51%) in MedMCQA. Many questions lack context for retrieval. External dental sources are critical to supplement this gap.",
        "terminology": [
            ("cavity", "dental caries", "Caused by acid-producing bacteria, not sugar directly"),
            ("gum disease", "periodontal disease (gingivitis → periodontitis)", "Progressive stages -- gingivitis is reversible, periodontitis is not"),
            ("root canal", "endodontic therapy", "Removal of infected pulp tissue -- saves the tooth"),
            ("wisdom teeth", "third molars", "Not always problematic -- extraction only if symptomatic or impacted"),
            ("filling", "dental restoration (amalgam, composite, ceramic)", "Different materials for different situations"),
            ("braces", "orthodontic appliance", "Fixed (brackets) vs removable (aligners) -- consumer should know options"),
            ("dry socket", "alveolar osteitis", "Complication after extraction -- most common patient concern"),
        ],
        "query_patterns": [
            '"Do I need a root canal?" -> Signs: severe toothache, prolonged sensitivity, darkened tooth, gum swelling. Diagnosis requires clinical and radiographic evaluation.',
            '"How to prevent cavities?" -> Brushing (fluoride toothpaste, 2min, 2x/day), flossing daily, limit sugary snacks, regular dental check-ups, fluoride treatments.',
            '"Is amalgam filling safe?" -> ADA and FDA confirm safety for most patients. Mercury concerns are not supported by evidence. Alternative: composite resin.',
            '"When do wisdom teeth need removal?" -> Impacted, recurrent pericoronitis, cyst formation, damage to adjacent teeth. Asymptomatic fully erupted teeth: observation.',
        ],
        "category_rules": [
            "Dental abscess with facial swelling: potential emergency (Ludwig's angina, airway compromise) -- link to Emergency",
            "Antibiotic prophylaxis: only for specific cardiac conditions per AHA guidelines -- not routine for dental procedures",
            "Fluoride: evidence-based for caries prevention. Address water fluoridation concerns with Tier 1 evidence.",
            "Dental emergencies (avulsed tooth, jaw fracture): time-sensitive -- provide immediate guidance",
        ],
        "pitfalls": [
            "MedMCQA dental data has 51% missing explanations -- do not rely on this dataset alone for dental content",
            "Amalgam/mercury controversy: well-studied and safe per FDA/ADA, but persistent consumer concern -- address with evidence, not dismissal",
            "Antibiotic prophylaxis guidelines have narrowed significantly -- older dental sources may over-recommend",
            "Dental pain can mimic other conditions (sinusitis, referred cardiac pain) -- differential is important",
        ],
        "explanation_style": "Materials science and procedural. Explanations describe dental materials (composition, setting chemistry), surgical techniques, and radiographic interpretation. Less pathophysiology compared to other categories. High proportion of recall-type questions.",
    },

    "public_health_prevention": {
        "name": "Public Health & Prevention",
        "source_subjects": "Social & Preventive Medicine (epidemiology, biostatistics, communicable diseases, non-communicable diseases, health programs, environment, demography, family planning, health education, occupational health)",
        "subcategories": "Vaccination & Immunization, Epidemiology & Disease Surveillance, National Health Programs, Biostatistics Basics, Environmental Health, Maternal & Child Health Programs, Nutrition Programs, Occupational Health, Disaster Management",
        "confidence": "High",
        "strong_links": [
            ("infections", "epidemiology of communicable diseases, outbreak management, vaccination -- 15 cross-hits"),
            ("childrens_health", "immunization schedule, maternal-child health programs"),
            ("womens_reproductive", "maternal health programs, family planning"),
        ],
        "weak_links": [
            ("hormones_metabolism_nutrition", "nutrition programs, NCD prevention"),
            ("emergency_critical_care", "disaster management, mass casualty triage"),
        ],
        "source_priority": [
            "WHO, CDC, national health ministry guidelines",
            "Cochrane reviews on public health interventions",
            "PubMed reviews on epidemiology (NOTE: low PubMedQA coverage -- only 8 questions in sample)",
            "MedMCQA TIER_A explanations (Park's PSM -- primary textbook)",
            "WHO.int and CDC.gov for public information",
        ],
        "source_rationale": "Public health is policy-driven and geographically variable. Indian health programs (from MedMCQA source) may not apply globally. Always contextualize to user's region. PubMedQA coverage is LOW -- need external sources.",
        "terminology": [
            ("epidemic / pandemic", "epidemic (local) / pandemic (global)", "WHO declares pandemic status -- not all outbreaks are pandemics"),
            ("herd immunity", "population immunity threshold", "Varies by disease (measles ~95%, polio ~80%)"),
            ("screening test", "screening (sensitivity/specificity)", "Explain false positives and false negatives in consumer terms"),
            ("incidence vs prevalence", "incidence (new cases) vs prevalence (total cases)", "Different epidemiological measures -- consumers often confuse"),
            ("quarantine vs isolation", "quarantine (exposed) vs isolation (infected)", "Different public health measures"),
            ("BMI", "body mass index", "Screening tool, not diagnostic. Limitations: doesn't distinguish muscle from fat."),
        ],
        "query_patterns": [
            '"Is this vaccine recommended?" -> Reference current national immunization schedule (CDC for US, NHS for UK, NIP for India). Age-specific and risk-factor-specific recommendations.',
            '"What is the survival rate for [disease]?" -> Explain case fatality rate vs mortality rate vs survival rate. Provide context (age, stage, treatment era).',
            '"Is [substance] safe in drinking water?" -> Reference WHO/EPA guidelines for safe limits. Environmental health standards.',
            '"How are diseases tracked?" -> Explain surveillance systems (notifiable diseases, sentinel surveillance, syndromic surveillance). CDC/WHO reporting mechanisms.',
        ],
        "category_rules": [
            "Health program information is GEOGRAPHY-SPECIFIC -- always ask about user's country/region",
            "Biostatistics: explain p-values, confidence intervals, relative risk in consumer-accessible language",
            "Screening recommendations: follow USPSTF (US) or equivalent national body -- specify which guideline",
            "Vaccination: always use Tier 1 evidence. Counter misinformation proactively.",
        ],
        "pitfalls": [
            "MedMCQA PSM content is India-centric (national health programs, Indian epidemiology) -- not directly applicable globally",
            "PubMedQA coverage for public health is very low (only 8 questions in sample) -- significant data gap",
            "Screening guidelines vary significantly by country -- do not universalize one country's recommendations",
            "Biostatistic concepts (p-value, NNT, odds ratio) are frequently misunderstood -- simplified explanations needed",
        ],
        "explanation_style": "Quantitative and policy-oriented. Explanations describe epidemiological measures (rates, ratios, proportions), study designs (RCT, cohort, case-control), and health program structures. Heavy use of tables and numerical data.",
    },
}


# ─── Generate Category File ─────────────────────────────────────────────────

def generate_category_file(cat_key: str, cat_def: dict, stats: dict) -> str:
    """Generate a category markdown file following the plan template."""
    s = stats.get(cat_key, {
        "total": 0, "medmcqa": 0, "pubmedqa": 0,
        "tier_a": 0, "tier_b": 0, "tier_c": 0, "tier_d": 0,
        "subjects": Counter(), "missing_exp": 0,
    })
    total = s["total"] or 1  # avoid division by zero

    lines = []
    lines.append("<!-- STATUS: DRAFT -- awaiting human review -->")
    lines.append(f"# {cat_def['name']}")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append(f"- **Source subjects:** {cat_def['source_subjects']}")
    lines.append(f"- **Question count (sample):** {s['total']:,} (MedMCQA: {s['medmcqa']:,}, PubMedQA: {s['pubmedqa']:,})")
    lines.append(f"- **Subcategories:** {cat_def['subcategories']}")
    lines.append(f"- **Confidence:** {cat_def['confidence']}")
    lines.append("")

    # Links
    lines.append("## Links")
    lines.append("<!-- These become edges in the Phase 2 context graph -->")
    lines.append("- **Strong links:**")
    for link_cat, reason in cat_def["strong_links"]:
        label = CATEGORIES.get(link_cat, {}).get("name", link_cat)
        lines.append(f"  - [{label}]({link_cat}.md) -- {reason}")
    lines.append("- **Weak links:**")
    for link_cat, reason in cat_def["weak_links"]:
        label = CATEGORIES.get(link_cat, {}).get("name", link_cat)
        lines.append(f"  - [{label}]({link_cat}.md) -- {reason}")
    lines.append("")

    # Source Priority
    lines.append("## Source Priority")
    lines.append("<!-- Overrides general_rules.md Tier ordering for this category -->")
    for i, src in enumerate(cat_def["source_priority"], 1):
        lines.append(f"{i}. {src}")
    lines.append(f"**Rationale:** {cat_def['source_rationale']}")
    lines.append("")

    # Terminology Map
    lines.append("## Terminology Map")
    lines.append("| Consumer Term | Medical Term | Notes |")
    lines.append("|--------------|-------------|-------|")
    for consumer, medical, notes in cat_def["terminology"]:
        lines.append(f"| {consumer} | {medical} | {notes} |")
    lines.append("")

    # Common Query Patterns
    lines.append("## Common Query Patterns")
    for pattern in cat_def["query_patterns"]:
        lines.append(f"- {pattern}")
    lines.append("")

    # Category-Specific Rules
    lines.append("## Category-Specific Rules")
    for rule in cat_def["category_rules"]:
        lines.append(f"- {rule}")
    lines.append("")

    # Known Pitfalls
    lines.append("## Known Pitfalls")
    for pitfall in cat_def["pitfalls"]:
        lines.append(f"- {pitfall}")
    lines.append("")

    # Dominant Explanation Style
    lines.append("## Dominant Explanation Style")
    lines.append(cat_def["explanation_style"])
    lines.append("")

    # Key Evidence
    lines.append("## Key Evidence")
    tier_a_pct = s["tier_a"] / total * 100
    missing_pct = s["missing_exp"] / total * 100
    lines.append(f"- **TIER_A (reference-cited):** {s['tier_a']:,} ({tier_a_pct:.0f}%)")
    lines.append(f"- **TIER_B (mechanism-based):** {s['tier_b']:,}")
    lines.append(f"- **TIER_C (minimal):** {s['tier_c']:,}")
    lines.append(f"- **TIER_D (null):** {s['tier_d']:,}")
    lines.append(f"- **Missing explanations:** {s['missing_exp']:,} ({missing_pct:.0f}%)")
    if s["subjects"]:
        lines.append(f"- **Top contributing subjects:** {', '.join(f'{subj} ({count})' for subj, count in s['subjects'].most_common(5))}")
    lines.append("")

    return "\n".join(lines)


def main():
    stats = load_stats()

    for cat_key, cat_def in CATEGORIES.items():
        content = generate_category_file(cat_key, cat_def, stats)
        filepath = CAT_DIR / f"{cat_key}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Wrote {filepath.name}")

    print(f"\nGenerated {len(CATEGORIES)} category files in {CAT_DIR}")


if __name__ == "__main__":
    main()
