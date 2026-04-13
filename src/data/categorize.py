"""
Medical QA Data Categorization Pipeline

Categorizes MedMCQA and PubMedQA questions into 20 consumer-facing
health categories. Outputs brain/ directory with structured markdown
and CSV mapping files.

Usage:
    python categorize.py --source medmcqa --batches 50
    python categorize.py --source pubmedqa --batches 20
    python categorize.py --source both --batches 50
"""

import requests
import csv
import json
import re
import os
import time
import argparse
from collections import Counter, defaultdict
from pathlib import Path

# ─── 20 Consumer-Facing Categories ───────────────────────────────────────────

CATEGORIES = [
    "heart_blood_vessels",
    "brain_nervous_system",
    "mental_health",
    "digestive_liver",
    "breathing_lungs",
    "blood_immune",
    "cancer",
    "infections",
    "bones_joints_muscles",
    "kidney_urinary",
    "womens_reproductive",
    "childrens_health",
    "eye_health",
    "ear_nose_throat",
    "skin_dermatology",
    "medications_drug_safety",
    "hormones_metabolism_nutrition",
    "emergency_critical_care",
    "dental_oral",
    "public_health_prevention",
]

CATEGORY_LABELS = {
    "heart_blood_vessels": "Heart & Blood Vessels",
    "brain_nervous_system": "Brain & Nervous System",
    "mental_health": "Mental Health",
    "digestive_liver": "Digestive System & Liver",
    "breathing_lungs": "Breathing & Lungs",
    "blood_immune": "Blood & Immune Disorders",
    "cancer": "Cancer",
    "infections": "Infections & Infectious Disease",
    "bones_joints_muscles": "Bones, Joints & Muscles",
    "kidney_urinary": "Kidney & Urinary Health",
    "womens_reproductive": "Women's & Reproductive Health",
    "childrens_health": "Children's Health",
    "eye_health": "Eye Health",
    "ear_nose_throat": "Ear, Nose & Throat",
    "skin_dermatology": "Skin & Dermatology",
    "medications_drug_safety": "Medications & Drug Safety",
    "hormones_metabolism_nutrition": "Hormones, Metabolism & Nutrition",
    "emergency_critical_care": "Emergency & Critical Care",
    "dental_oral": "Dental & Oral Health",
    "public_health_prevention": "Public Health & Prevention",
}

# ─── Subject + Topic → Category Mapping ──────────────────────────────────────

# Direct subject mappings (when topic is null or doesn't change the mapping)
SUBJECT_DEFAULT_MAP: dict[str, str] = {
    "Dental": "dental_oral",
    "ENT": "ear_nose_throat",
    "Ophthalmology": "eye_health",
    "Orthopaedics": "bones_joints_muscles",
    "Pediatrics": "childrens_health",
    "Psychiatry": "mental_health",
    "Skin": "skin_dermatology",
    "Social & Preventive Medicine": "public_health_prevention",
}

# Topic keyword → category mappings (checked against topic_name)
TOPIC_KEYWORD_MAP: list[tuple[list[str], str]] = [
    # Cardiovascular
    (["cardio", "c.v.s", "cvs", "heart", "coronary", "angina", "arrhythm",
      "valvular", "ecg", "electrocardio", "aoic", "aortic", "hypertension",
      "myocardial", "pericardi", "endocarditi"], "heart_blood_vessels"),
    # Brain & Nervous System
    (["c.n.s", "cns", "neuro", "cerebr", "brain", "spinal", "meningi",
      "epilep", "seizure", "stroke", "migraine", "neuropath"], "brain_nervous_system"),
    # Mental Health
    (["psychiatr", "schizophren", "depressi", "anxiety", "psychos",
      "psychoanaly", "sleep disorder", "substance", "addiction", "ocd",
      "bipolar", "dementia", "suicid"], "mental_health"),
    # Digestive & Liver
    (["g.i.t", "git", "gastro", "liver", "hepat", "gall bladder", "bile",
      "oesophag", "esophag", "intestin", "rectum", "anal", "appendic",
      "hernia", "pancrea", "malabsor", "peptic"], "digestive_liver"),
    # Breathing & Lungs
    (["respiratory", "pulmon", "lung", "bronch", "asthma", "copd",
      "pleural", "thoracic", "pneumo"], "breathing_lungs"),
    # Blood & Immune
    (["haemat", "hemat", "blood", "anemia", "anaemia", "leukemia",
      "lymphoma", "thrombocyt", "coagulat", "bleeding disorder",
      "immunodeficien", "immunology", "immun"], "blood_immune"),
    # Cancer
    (["neoplas", "cancer", "oncolog", "tumor", "tumour", "carcinoma",
      "sarcoma", "malignan", "metastas"], "cancer"),
    # Infections
    (["bacteriol", "virology", "parasitol", "mycology", "infect",
      "communicable", "tuberculo", "hiv", "aids", "malaria", "dengue",
      "sexually transmitted", "sti", "std"], "infections"),
    # Bones & Joints
    (["fractur", "orthop", "bone", "joint", "arthriti", "spine",
      "sports injury", "dislocation", "ligament", "musculoskelet"], "bones_joints_muscles"),
    # Kidney & Urinary
    (["kidney", "renal", "urolog", "urinary", "nephro", "dialysis",
      "prostate", "bladder"], "kidney_urinary"),
    # Women's & Reproductive Health
    (["obstetric", "gynae", "gynec", "pregnan", "contracep", "menstrua",
      "ovarian", "cervical", "uterine", "placenta", "caesarean",
      "infertility", "menopaus", "dysmenor", "endometrio"], "womens_reproductive"),
    # Children's Health
    (["pediatr", "paediatr", "newborn", "neonat", "infant", "child development",
      "vaccination schedule", "congenital"], "childrens_health"),
    # Eye Health
    (["ophthalm", "eye", "retina", "cornea", "glaucoma", "uveal",
      "cataract", "conjunctiv", "vision", "ocular", "orbit"], "eye_health"),
    # Ear, Nose & Throat
    (["ent", "ear", "nose", "throat", "larynx", "sinus", "vestibul",
      "facial nerve", "tympan", "mastoid", "pharyn", "tonsil"], "ear_nose_throat"),
    # Skin
    (["skin", "dermat", "psoriasis", "eczema", "melanoma", "urticaria",
      "pemphig", "leprosy"], "skin_dermatology"),
    # Medications & Drug Safety
    (["pharmacodyn", "pharmacokin", "drug interaction", "adverse effect",
      "antiplatel", "fibrinoly", "antibiotic", "antimicrob",
      "antifungal", "antiviral", "chemotherap", "analges"], "medications_drug_safety"),
    # Hormones, Metabolism & Nutrition
    (["endocrin", "hormone", "thyroid", "diabet", "insulin", "adrenal",
      "pituitar", "vitamin", "mineral", "metabolism", "enzyme",
      "amino acid", "carbohydrate", "lipid", "fatty acid",
      "krebs", "glyco", "nutrition"], "hormones_metabolism_nutrition"),
    # Emergency & Critical Care
    (["trauma", "burn", "poison", "toxicol", "emergency", "cpr",
      "resuscit", "shock", "anaesthe", "anesthe", "critical care",
      "snake bite", "envenomation"], "emergency_critical_care"),
    # Public Health
    (["epidemiol", "biostatist", "health program", "health education",
      "environment", "demograph", "family planning", "sanitation",
      "occupational", "disaster", "public health", "preventive"], "public_health_prevention"),
]

# ─── Question Content Keywords (fallback when subject + topic insufficient) ──

QUESTION_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["heart", "cardiac", "myocardial", "angina", "atrial", "ventricular",
      "ecg", "hypertension", "blood pressure", "aortic", "mitral",
      "pericarditis", "endocarditis", "coronary", "stent"], "heart_blood_vessels"),
    (["brain", "cerebral", "meningitis", "stroke", "epilepsy", "seizure",
      "parkinson", "alzheimer", "neuropathy", "spinal cord", "cranial nerve",
      "headache", "migraine"], "brain_nervous_system"),
    (["depression", "anxiety", "schizophrenia", "psychosis", "bipolar",
      "ocd", "ptsd", "suicide", "hallucination", "delusion",
      "lithium", "antipsychotic", "ssri"], "mental_health"),
    (["stomach", "liver", "hepatitis", "cirrhosis", "jaundice",
      "gallstone", "pancreatitis", "appendicitis", "hernia",
      "peptic ulcer", "esophag", "intestin", "colon", "rectum",
      "diarrhea", "constipation", "vomiting"], "digestive_liver"),
    (["lung", "pneumonia", "asthma", "copd", "bronchitis", "tuberculosis",
      "pleural", "dyspnea", "cough", "sputum", "bronchiectasis",
      "pulmonary embolism", "respiratory"], "breathing_lungs"),
    (["anemia", "leukemia", "lymphoma", "thrombocytopenia", "hemophilia",
      "bleeding", "coagulation", "platelet", "bone marrow",
      "transfusion", "sickle cell", "thalassemia", "immunodeficiency",
      "autoimmune"], "blood_immune"),
    (["cancer", "carcinoma", "sarcoma", "tumor", "tumour", "malignant",
      "metastasis", "biopsy", "oncology", "chemotherapy", "radiation therapy",
      "staging", "grading"], "cancer"),
    (["infection", "bacteria", "virus", "fungal", "parasite", "antibiotic",
      "sepsis", "abscess", "fever", "malaria", "hiv", "aids",
      "hepatitis b", "hepatitis c", "tuberculosis", "vaccine"], "infections"),
    (["fracture", "dislocation", "arthritis", "osteoporosis", "spine",
      "femur", "tibia", "hip", "knee", "shoulder", "wrist",
      "ligament", "tendon", "muscle"], "bones_joints_muscles"),
    (["kidney", "renal", "dialysis", "nephritis", "nephrotic",
      "creatinine", "urine", "urinary", "prostate", "bladder",
      "ureter", "urethra", "calculi", "stone"], "kidney_urinary"),
    (["pregnancy", "pregnant", "fetus", "obstetric", "cesarean", "labour",
      "contracepti", "menstrual", "ovarian", "uterus", "cervix",
      "endometri", "menopause", "ovulation", "hcg"], "womens_reproductive"),
    (["child", "infant", "neonat", "newborn", "pediatric", "paediatric",
      "milestone", "breastfeed", "vaccination", "growth chart",
      "congenital", "birth weight"], "childrens_health"),
    (["eye", "vision", "retina", "cornea", "glaucoma", "cataract",
      "conjunctivitis", "optic nerve", "pupil", "lens",
      "intraocular", "fundoscopy"], "eye_health"),
    (["earache", "ear infection", "ear pain", "ear canal", "eardrum",
      "hearing loss", "hearing aid", "deafness", "tinnitus", "vertigo",
      "nasal congestion", "nasal discharge", "runny nose", "nosebleed",
      "sinusitis", "sore throat", "strep throat", "throat pain", "throat infection",
      "larynx", "laryngitis", "tonsil", "tonsillitis", "pharynx", "pharyngitis",
      "vocal cord", "epistaxis", "rhinitis", "postnasal"], "ear_nose_throat"),
    (["skin", "rash", "dermatitis", "psoriasis", "eczema",
      "melanoma", "acne", "urticaria", "blister", "wound",
      "ulcer", "pruritus", "alopecia"], "skin_dermatology"),
    (["drug", "dose", "pharmacokinetic", "half life", "receptor",
      "agonist", "antagonist", "side effect", "adverse",
      "contraindication", "interaction", "overdose"], "medications_drug_safety"),
    (["diabetes", "thyroid", "insulin", "glucose", "hba1c",
      "vitamin", "hormone", "cortisol", "adrenal", "pituitary",
      "metabolic", "enzyme deficiency", "nutrition",
      "malnutrition", "bmi", "obesity"], "hormones_metabolism_nutrition"),
    (["emergency", "trauma", "burn", "poison", "cpr",
      "shock", "hemorrhage", "anesthesia", "intubation",
      "ventilator", "icu", "resuscitation", "drowning"], "emergency_critical_care"),
    (["dental", "tooth", "teeth", "gingiva", "periodontal",
      "caries", "endodontic", "orthodontic", "oral", "mandible",
      "maxilla", "amalgam", "composite"], "dental_oral"),
    (["epidemiology", "prevalence", "incidence", "mortality rate",
      "morbidity", "screening", "surveillance", "biostatistic",
      "standard deviation", "p value", "confidence interval",
      "health program", "sanitation", "public health"], "public_health_prevention"),
]

# ─── Pharmacology Subject: topic-dependent routing ───────────────────────────

PHARMA_TOPIC_MAP: list[tuple[list[str], str]] = [
    (["cardiovascular", "c.v.s", "cvs", "anti-anginal", "antihypertensive",
      "ace inhibitor", "beta blocker", "calcium channel"], "heart_blood_vessels"),
    (["c.n.s", "cns", "central nervous", "anticonvulsant", "antiepileptic",
      "opioid", "analgesic"], "brain_nervous_system"),
    (["psychiatr", "antidepressant", "antipsychotic", "anxiolytic",
      "mood stabilizer", "ssri", "lithium"], "mental_health"),
    (["respiratory", "bronchodilator", "antitussive", "theophylline"], "breathing_lungs"),
    (["kidney", "diuretic", "renal"], "kidney_urinary"),
    (["endocrin", "anti diabetes", "insulin", "thyroid", "steroid",
      "hormone"], "hormones_metabolism_nutrition"),
    (["chemotherap", "cytotoxic", "anticancer", "antineoplastic"], "cancer"),
    (["antibiotic", "antimicrob", "antifungal", "antiviral", "antiparasit",
      "antimalarial", "cell wall synthesis"], "infections"),
    (["anaesthe", "anesthe", "muscle relaxant", "neuromuscular"], "emergency_critical_care"),
    (["autonomic", "parasympathetic", "sympathetic", "adrenergic",
      "cholinergic"], "medications_drug_safety"),
    (["prostaglandin", "nsaid", "anti-inflammatory", "antiplatelet",
      "fibrinolytic", "anticoagulant"], "medications_drug_safety"),
    (["general pharmacology", "pharmacodynamic", "pharmacokinetic",
      "drug interaction", "adverse effect"], "medications_drug_safety"),
    (["skin", "dermat"], "skin_dermatology"),
    (["eye", "ophthalm", "glaucoma"], "eye_health"),
]

# ─── MeSH Term → Category Mapping (for PubMedQA) ────────────────────────────

MESH_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["cardiovascular", "heart", "cardiac", "coronary", "myocardial",
      "hypertension", "stroke", "atrial", "ventricular", "aortic",
      "electrocardiography", "pericarditis", "endocarditis",
      "heart failure", "arrhythmia", "atherosclerosis"], "heart_blood_vessels"),
    (["brain", "cerebral", "hippocampus", "prefrontal cortex", "neuron",
      "nervous system", "nociception", "epilepsy", "parkinson",
      "alzheimer", "meningitis", "neuropath", "spinal cord",
      "migraine", "seizure"], "brain_nervous_system"),
    (["anxiety", "depression", "bipolar", "schizophrenia", "psychotic",
      "stress psychological", "mental disorder", "psychiatric",
      "substance-related", "autistic"], "mental_health"),
    (["gastrointestinal", "liver", "hepat", "pancrea", "esophag",
      "stomach", "intestin", "colon", "rectal", "biliary",
      "gallbladder", "cirrhosis", "gastric"], "digestive_liver"),
    (["lung", "pulmonary", "respiratory", "pneumonia", "asthma",
      "bronchial", "pleural", "tuberculosis"], "breathing_lungs"),
    (["leukocyte", "lymphocyte", "immunity", "immunoglobulin",
      "anemia", "hemoglobin", "platelet", "coagulation", "bleeding",
      "leukemia", "lymphoma", "bone marrow", "transfusion",
      "autoimmune", "immunodeficiency"], "blood_immune"),
    (["neoplasm", "carcinoma", "sarcoma", "tumor", "cancer",
      "metastasis", "oncolog", "malignant", "biomarker tumor",
      "antineoplastic"], "cancer"),
    (["infection", "bacteria", "virus", "parasit", "fungal",
      "sepsis", "antibiotic", "vaccine", "immunization",
      "communicable disease", "hiv", "hepatitis"], "infections"),
    (["bone", "fracture", "arthritis", "osteoporosis", "orthopedic",
      "cartilage", "tendon", "ligament", "muscle", "skeletal",
      "joint"], "bones_joints_muscles"),
    (["kidney", "renal", "nephro", "urinary", "bladder", "prostate",
      "dialysis", "glomerulo"], "kidney_urinary"),
    (["pregnancy", "fetus", "maternal", "obstetric", "cervical",
      "ovarian", "uterine", "breast", "mammary", "contracepti",
      "menstrual", "endometri", "reproductive"], "womens_reproductive"),
    (["infant", "child", "pediatric", "neonatal", "newborn",
      "adolescent", "congenital"], "childrens_health"),
    (["eye", "retina", "cornea", "glaucoma", "optic", "visual acuity",
      "cataract", "ocular", "lens"], "eye_health"),
    (["ear", "hearing", "vestibular", "nasal", "sinusitis",
      "rhinitis", "laryngeal", "pharyngeal", "tonsil"], "ear_nose_throat"),
    (["skin", "dermatitis", "melanoma", "psoriasis", "wound healing",
      "epidermal", "cutaneous"], "skin_dermatology"),
    (["drug therapy", "drug interaction", "pharmaceutical",
      "pharmacokinetic", "dose-response", "drug resistance"], "medications_drug_safety"),
    (["diabetes", "insulin", "thyroid", "vitamin", "hormone",
      "metabolic", "obesity", "nutrition", "enzyme",
      "amino acid"], "hormones_metabolism_nutrition"),
    (["emergency", "trauma", "burns", "critical care", "resuscitation",
      "wounds", "poisoning", "anesthesia"], "emergency_critical_care"),
    (["dental", "tooth", "oral", "periodontal", "mandible",
      "maxillofacial"], "dental_oral"),
    (["epidemiology", "public health", "vaccination", "socioeconomic",
      "health promotion", "screening", "prevention",
      "surveillance"], "public_health_prevention"),
]


# ─── Explanation Quality Tier Detection ──────────────────────────────────────

TEXTBOOK_PATTERNS = [
    r"ref[\s:]+", r"harrison", r"robbins", r"bailey", r"love",
    r"kd tripathi", r"park'?s", r"ganong", r"khurana", r"shaw",
    r"nelson", r"dutta", r"guyton", r"schwartz", r"sabiston",
    r"williams", r"devita", r"braunwald", r"cecil", r"davidson",
    r"\d+th\s+ed", r"\d+/e\s+p", r"page?\s*(no)?\.?\s*\d+",
]

MINIMAL_PATTERNS = [
    r"^ans[\.\s]",
    r"^[a-d]\s+i\.?e\.?",
    r"^answer[\s:-]",
    r"^option\s+[a-d]",
]


def detect_quality_tier(exp: str | None) -> str:
    """Classify the explanation into a quality tier."""
    if not exp or exp.strip().lower() in ("null", "", "none"):
        return "TIER_D"

    exp_lower = exp.lower().strip()

    # Check for textbook references
    for pattern in TEXTBOOK_PATTERNS:
        if re.search(pattern, exp_lower):
            return "TIER_A"

    # Check for minimal answers
    if len(exp_lower) < 50:
        for pattern in MINIMAL_PATTERNS:
            if re.search(pattern, exp_lower):
                return "TIER_C"
        if len(exp_lower) < 20:
            return "TIER_C"

    # Default: mechanism-based
    return "TIER_B"


# ─── Category Assignment ─────────────────────────────────────────────────────

def _match_keywords(text: str, keywords: list[str]) -> bool:
    """Check if any keyword matches in text (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def categorize_medmcqa(row: dict) -> tuple[str, str | None]:
    """
    Assign a MedMCQA question to primary (and optional secondary) category.
    Returns (primary_category, secondary_category_or_None).
    """
    subject = (row.get("subject_name") or "").strip()
    topic = (row.get("topic_name") or "").strip()
    question = (row.get("question") or "").strip()
    exp = (row.get("exp") or "").strip()

    combined_text = f"{topic} {question} {exp}"
    primary = None
    secondary = None

    # Step 1: Direct subject mapping for single-category subjects
    if subject in SUBJECT_DEFAULT_MAP:
        primary = SUBJECT_DEFAULT_MAP[subject]
        # Check if question content suggests a secondary category
        for keywords, cat in QUESTION_KEYWORD_MAP:
            if cat != primary and _match_keywords(question, keywords):
                secondary = cat
                break
        return primary, secondary

    # Step 2: Pharmacology special handling — route based on topic/content
    if subject == "Pharmacology":
        if topic:
            for keywords, cat in PHARMA_TOPIC_MAP:
                if _match_keywords(topic, keywords):
                    primary = cat
                    secondary = "medications_drug_safety"
                    return primary, secondary
        # Fallback: check question content
        for keywords, cat in PHARMA_TOPIC_MAP:
            if _match_keywords(question, keywords):
                primary = cat
                secondary = "medications_drug_safety"
                return primary, secondary
        return "medications_drug_safety", None

    # Step 3: For multi-category subjects, use topic first
    if topic:
        for keywords, cat in TOPIC_KEYWORD_MAP:
            if _match_keywords(topic, keywords):
                primary = cat
                break

    # Step 4: If topic didn't resolve, use question + exp content
    if not primary:
        for keywords, cat in QUESTION_KEYWORD_MAP:
            if _match_keywords(question, keywords):
                primary = cat
                break

    # Step 5: If still unresolved, use broader subject defaults
    if not primary:
        subject_broad_map = {
            "Anatomy": "bones_joints_muscles",
            "Physiology": "hormones_metabolism_nutrition",
            "Biochemistry": "hormones_metabolism_nutrition",
            "Medicine": "heart_blood_vessels",  # largest Medicine sub-topic
            "Surgery": "digestive_liver",  # largest Surgery sub-topic
            "Pathology": "blood_immune",
            "Microbiology": "infections",
            "Forensic Medicine": "emergency_critical_care",
            "Radiology": "heart_blood_vessels",
            "Anaesthesia": "emergency_critical_care",
            "Unknown": "medications_drug_safety",
        }
        primary = subject_broad_map.get(subject, "medications_drug_safety")

    # Step 6: Check for cancer as secondary
    cancer_signals = ["cancer", "carcinoma", "tumor", "tumour", "malignan",
                      "neoplas", "metastas", "sarcoma", "oncolog"]
    if primary != "cancer" and _match_keywords(question, cancer_signals):
        secondary = "cancer"

    return primary, secondary


def categorize_pubmedqa(row: dict) -> tuple[str, str | None]:
    """
    Assign a PubMedQA question to primary (and optional secondary) category
    using MeSH terms and question content.
    """
    question = (row.get("question") or "").strip()
    context = row.get("context", {})
    meshes = context.get("meshes", [])
    mesh_text = " ".join(meshes).lower()

    primary = None
    secondary = None
    scores: dict[str, int] = defaultdict(int)

    # Score each category by MeSH term matches
    for keywords, cat in MESH_KEYWORD_MAP:
        for kw in keywords:
            if kw.lower() in mesh_text:
                scores[cat] += 1

    # Also score by question content
    for keywords, cat in QUESTION_KEYWORD_MAP:
        if _match_keywords(question, keywords):
            scores[cat] += 2  # question content gets higher weight

    if scores:
        sorted_cats = sorted(scores.items(), key=lambda x: -x[1])
        primary = sorted_cats[0][0]
        if len(sorted_cats) > 1 and sorted_cats[1][1] >= 2:
            secondary = sorted_cats[1][0]
    else:
        primary = "medications_drug_safety"  # fallback

    return primary, secondary


def categorize_medquad(row: dict, source_name: str = "") -> tuple[str, str | None]:
    """
    Assign a MedQuAD question to primary (and optional secondary) category.

    MedQuAD CSV columns: question_id, question_type, question, answer
    No focus_area or source column — source is derived from the filename
    and passed in as source_name (e.g. "1_CancerGov_QA", "5_NIDDK_QA").

    Strategy:
      1. Source name pre-routing (strongest signal — each NIH site has a domain)
      2. Question text keyword matching (same QUESTION_KEYWORD_MAP as other datasets)
      3. Answer text keyword matching (answers are often rich with medical terms)
      4. Default to public_health_prevention
    """
    question = (row.get("question") or "").strip()
    answer = (row.get("answer") or "").strip()
    qtype = (row.get("question_type") or "").strip().lower()
    source_lower = source_name.lower()

    primary = None
    secondary = None

    # ── Step 1: Source name pre-routing ───────────────────────────────────────
    # Filename encodes the NIH site which has a strong domain signal
    SOURCE_ROUTE_MAP = [
        ("cancergov",       "cancer"),
        ("niddk",           "digestive_liver"),       # Digestive, Diabetes, Kidney
        ("ninds",           "brain_nervous_system"),  # Neurological disorders
        ("nhlbi",           "heart_blood_vessels"),   # Heart, Lung, Blood
        ("cdc",             "infections"),
        ("seniorhealth",    "public_health_prevention"),
        ("mplusdrugs",      "medications_drug_safety"),
        ("mplusherbssupp",  "medications_drug_safety"),
        ("gard",            None),   # Genetic/rare diseases — too broad, use content
        ("ghr",             None),   # Genetics Home Reference — use content
        ("mplus",           None),   # General health topics — use content
        ("adam",            None),   # General encyclopedia — use content
    ]
    for site_key, mapped_cat in SOURCE_ROUTE_MAP:
        if site_key in source_lower and mapped_cat:
            primary = mapped_cat
            break

    # ── Step 2: Question text keyword matching ────────────────────────────────
    if not primary:
        for keywords, cat in QUESTION_KEYWORD_MAP:
            if _match_keywords(question, keywords):
                primary = cat
                break

    # ── Step 3: Answer text keyword matching (first 300 chars) ───────────────
    if not primary:
        answer_preview = answer[:300]
        for keywords, cat in QUESTION_KEYWORD_MAP:
            if _match_keywords(answer_preview, keywords):
                primary = cat
                break

    # ── Step 4: qtype secondary hint ─────────────────────────────────────────
    # e.g. question_type="treatment" or "side effects" hints at medications
    if qtype in ("treatment", "side effects", "dosage") and primary and primary != "medications_drug_safety":
        secondary = "medications_drug_safety"

    # ── Step 5: Cancer secondary check ───────────────────────────────────────
    cancer_signals = ["cancer", "carcinoma", "tumor", "tumour", "malignan",
                      "neoplas", "metastas", "sarcoma", "oncolog"]
    combined = f"{question} {answer[:200]}"
    if primary and primary != "cancer" and _match_keywords(combined, cancer_signals):
        secondary = "cancer"

    # ── Step 6: Default ───────────────────────────────────────────────────────
    if not primary:
        primary = "public_health_prevention"

    return primary, secondary


# ─── HealthCareMagic Tier Detection ──────────────────────────────────────────

# Medical condition signals: suffixes/terms that indicate a named diagnosis was given
_HCM_CONDITION_SUFFIXES = [
    "disease", "syndrome", "disorder", "infection", "deficiency",
    "itis", "osis", "emia", "uria", "pathy", "plasia", "phobia",
    "algia", "oma", "itis", "ectomy", "otomy", "oscopy",
]

# Mechanism language: explains *why* something happens
_HCM_MECHANISM_PHRASES = [
    "due to", "caused by", "because of", "results from", "leads to",
    "is a type of", "the most likely cause", "this is because",
    "which means", "in this condition", "this occurs when",
    "pathophysiology", "mechanism",
]

# Drug/treatment signals: specific intervention was recommended
_HCM_DRUG_SIGNALS = [
    " mg", "tablet", "capsule", "syrup", "injection", "supplement",
    "antibiotic", "antifungal", "antiviral", "vaccine", "dose ",
    "vitamin ", "zinc", "iron ", "probiotic", "ointment", "cream",
    "inhaler", "drops", "sachet",
]

# Recommendation signals: doctor tells patient to do something
_HCM_RECOMMENDATION_PHRASES = [
    "i suggest", "i recommend", "you should", "please ", "i advise",
    "take ", "avoid ", "consult", "see a doctor", "visit a", "follow up",
    "get a ", "have a ", "do not", "stop ", "start ",
]

# Conditional signals: nuanced guidance with if/unless logic
_HCM_CONDITIONAL_PHRASES = [
    "unless", "however if", "except when", "if not", "in case",
    "if the symptoms", "if there is", "if you have", "if it persists",
    "if no improvement",
]

# Deflection/inability signals
_HCM_DEFLECTION_PHRASES = [
    "i cannot", "i can't", "cannot determine", "unable to",
    "not able to", "i am not able", "i'm not able",
    "impossible to say", "hard to say without",
]


def detect_healthcaremagic_tier(output: str) -> str:
    """
    Classify a HealthCareMagic doctor response into a quality tier.

    Tier criteria:
      TIER_A — names a condition + explains mechanism/reasoning + specific treatment
      TIER_B — names a condition or drug + gives recommendation, lighter on mechanism
      TIER_C — reassurance or generic advice only, no named condition
      TIER_D — deflection, very short, or appears truncated mid-sentence
    """
    if not output:
        return "TIER_D"

    stripped = output.strip()

    # Too short to be useful
    if len(stripped) < 50:
        return "TIER_D"

    text = stripped.lower()

    # Deflection check
    if any(p in text for p in _HCM_DEFLECTION_PHRASES):
        return "TIER_D"

    # Truncation check: no sentence-ending punctuation and short enough to flag
    if stripped[-1] not in ".!?" and len(stripped) < 300:
        return "TIER_D"

    # Named condition: suffix match OR parenthetical abbreviation like (BPPV)
    has_named_condition = any(suffix in text for suffix in _HCM_CONDITION_SUFFIXES)
    if not has_named_condition:
        has_named_condition = bool(re.search(r'\([A-Z]{2,6}\)', stripped))

    has_mechanism = any(p in text for p in _HCM_MECHANISM_PHRASES)
    has_drug = any(p in text for p in _HCM_DRUG_SIGNALS)
    has_recommendation = any(p in text for p in _HCM_RECOMMENDATION_PHRASES)
    has_conditional = any(p in text for p in _HCM_CONDITIONAL_PHRASES)

    # TIER_A: named condition + mechanism + (drug or conditional)
    if has_named_condition and has_mechanism and (has_drug or has_conditional):
        return "TIER_A"

    # TIER_B: named condition or drug + recommendation
    if (has_named_condition or has_drug) and has_recommendation:
        return "TIER_B"

    # TIER_C: has some recommendation but no condition/drug signal
    if has_recommendation:
        return "TIER_C"

    return "TIER_D"


def categorize_healthcaremagic(row: dict) -> tuple[str, str | None]:
    """
    Assign a HealthCareMagic record to primary (and optional secondary) category.

    No subject_name or topic_name — scans patient input text then doctor output
    using the same QUESTION_KEYWORD_MAP used as fallback in other datasets.
    Returns (primary_category, secondary_category_or_None).
    """
    patient_input = (row.get("input") or "").strip()
    doctor_output = (row.get("output") or "").strip()

    primary = None
    secondary = None

    # Step 1: Score by patient input (primary signal)
    scores: dict[str, int] = defaultdict(int)
    for keywords, cat in QUESTION_KEYWORD_MAP:
        if _match_keywords(patient_input, keywords):
            scores[cat] += 2

    # Step 2: Doctor output adds supporting signal (first 300 chars only)
    output_preview = doctor_output[:300]
    for keywords, cat in QUESTION_KEYWORD_MAP:
        if _match_keywords(output_preview, keywords):
            scores[cat] += 1

    if scores:
        sorted_cats = sorted(scores.items(), key=lambda x: -x[1])
        primary = sorted_cats[0][0]
        if len(sorted_cats) > 1 and sorted_cats[1][1] >= 2:
            secondary = sorted_cats[1][0]
    else:
        primary = "public_health_prevention"  # fallback

    # Step 3: Cancer secondary check
    cancer_signals = ["cancer", "carcinoma", "tumor", "tumour", "malignan",
                      "neoplas", "metastas", "sarcoma", "oncolog"]
    combined = f"{patient_input} {output_preview}"
    if primary != "cancer" and _match_keywords(combined, cancer_signals):
        secondary = "cancer"

    return primary, secondary


# ─── API Fetching ────────────────────────────────────────────────────────────

def fetch_medmcqa_batch(offset: int, length: int = 100) -> list[dict]:
    """Fetch a batch of MedMCQA rows from HuggingFace."""
    url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "openlifescienceai/medmcqa",
        "config": "default",
        "split": "train",
        "offset": offset,
        "length": length,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [r["row"] for r in data.get("rows", [])]


def fetch_pubmedqa_batch(
    offset: int, length: int = 100, config: str = "pqa_artificial"
) -> list[dict]:
    """Fetch a batch of PubMedQA rows from HuggingFace."""
    url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "qiaojin/PubMedQA",
        "config": config,
        "split": "train",
        "offset": offset,
        "length": length,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [r["row"] for r in data.get("rows", [])]


# ─── Processing Pipeline ────────────────────────────────────────────────────

BRAIN_DIR = Path(__file__).parent.parent.parent / "brain"


def process_medmcqa(num_batches: int = 50, batch_size: int = 100) -> list[dict]:
    """Process MedMCQA data in batches, return categorized records."""
    results = []
    total = num_batches * batch_size

    # Sample from spread-out offsets for representative coverage
    max_offset = 182_000
    step = max_offset // num_batches
    offsets = [i * step for i in range(num_batches)]

    print(f"Processing MedMCQA: {num_batches} batches x {batch_size} = {total} rows")

    for i, offset in enumerate(offsets):
        try:
            rows = fetch_medmcqa_batch(offset, batch_size)
        except Exception as e:
            print(f"  Batch {i+1}/{num_batches} (offset={offset}) FAILED: {e}")
            time.sleep(2)
            continue

        for row in rows:
            primary, secondary = categorize_medmcqa(row)
            tier = detect_quality_tier(row.get("exp"))

            results.append({
                "id": row.get("id", ""),
                "dataset": "medmcqa",
                "subject_name": row.get("subject_name", ""),
                "topic_name": row.get("topic_name", ""),
                "question": row.get("question", "")[:200],
                "primary_category": primary,
                "secondary_category": secondary or "",
                "quality_tier": tier,
                "has_explanation": bool(row.get("exp") and row["exp"].strip()
                                       and row["exp"].strip().lower() != "null"),
            })

        print(f"  Batch {i+1}/{num_batches} (offset={offset}): {len(rows)} rows processed")
        time.sleep(0.3)  # rate limiting

    return results


def process_pubmedqa(num_batches: int = 20, batch_size: int = 100) -> tuple[list[dict], dict]:
    """Process PubMedQA data, return categorized records + MeSH mapping."""
    results = []
    mesh_category_map: dict[str, Counter] = defaultdict(Counter)
    total = num_batches * batch_size

    max_offset = 211_000
    step = max_offset // num_batches
    offsets = [i * step for i in range(num_batches)]

    print(f"Processing PubMedQA: {num_batches} batches x {batch_size} = {total} rows")

    for i, offset in enumerate(offsets):
        try:
            rows = fetch_pubmedqa_batch(offset, batch_size)
        except Exception as e:
            print(f"  Batch {i+1}/{num_batches} (offset={offset}) FAILED: {e}")
            time.sleep(2)
            continue

        for row in rows:
            primary, secondary = categorize_pubmedqa(row)
            context = row.get("context", {})
            meshes = context.get("meshes", [])

            # Build MeSH → category mapping
            for mesh in meshes:
                mesh_category_map[mesh][primary] += 1

            results.append({
                "id": str(row.get("pubid", "")),
                "dataset": "pubmedqa",
                "subject_name": "",
                "topic_name": ", ".join(meshes[:5]),
                "question": row.get("question", "")[:200],
                "primary_category": primary,
                "secondary_category": secondary or "",
                "quality_tier": "TIER_A",  # PubMedQA is always peer-reviewed
                "has_explanation": True,
            })

        print(f"  Batch {i+1}/{num_batches} (offset={offset}): {len(rows)} rows processed")
        time.sleep(0.3)

    # Resolve MeSH → category: pick the most frequent category for each term
    resolved_mesh_map = {}
    for mesh_term, cat_counts in mesh_category_map.items():
        resolved_mesh_map[mesh_term] = cat_counts.most_common(1)[0][0]

    return results, resolved_mesh_map


def write_category_mapping(results: list[dict], output_path: Path) -> None:
    """Write category_mapping.csv."""
    fieldnames = [
        "id", "dataset", "subject_name", "topic_name", "question",
        "primary_category", "secondary_category", "quality_tier",
        "has_explanation",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(results)} rows to {output_path}")


def write_mesh_mapping(mesh_map: dict[str, str], output_path: Path) -> None:
    """Write mesh_to_category.csv."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["mesh_term", "primary_category", "category_label"])
        for mesh_term, cat in sorted(mesh_map.items()):
            writer.writerow([mesh_term, cat, CATEGORY_LABELS.get(cat, cat)])
    print(f"Wrote {len(mesh_map)} MeSH mappings to {output_path}")


def compute_stats(results: list[dict]) -> dict:
    """Compute distribution statistics from categorized results."""
    stats = {
        "total": len(results),
        "by_dataset": Counter(),
        "by_category": Counter(),
        "by_category_dataset": defaultdict(lambda: Counter()),
        "by_tier": Counter(),
        "by_tier_category": defaultdict(lambda: Counter()),
        "by_subject": Counter(),
        "has_explanation": Counter(),
        "secondary_category": Counter(),
        "no_explanation_by_category": Counter(),
        # Co-occurrence: primary_cat -> {secondary_cat: count}
        "secondary_by_primary": defaultdict(Counter),
    }

    for r in results:
        ds = r["dataset"]
        cat = r["primary_category"]
        tier = r["quality_tier"]
        subject = r["subject_name"]

        stats["by_dataset"][ds] += 1
        stats["by_category"][cat] += 1
        stats["by_category_dataset"][cat][ds] += 1
        stats["by_tier"][tier] += 1
        stats["by_tier_category"][cat][tier] += 1
        stats["by_subject"][subject] += 1
        stats["has_explanation"][r["has_explanation"]] += 1

        if r["secondary_category"]:
            stats["secondary_category"][r["secondary_category"]] += 1
            stats["secondary_by_primary"][cat][r["secondary_category"]] += 1

        if not r["has_explanation"]:
            stats["no_explanation_by_category"][cat] += 1

    return stats


def write_stats_md(stats: dict, output_path: Path) -> None:
    """Write stats.md with distribution data."""
    lines = [
        "<!-- STATUS: DRAFT -- awaiting human review -->",
        "",
        "# Categorization Statistics",
        "",
        f"**Total records processed:** {stats['total']}",
        "",
        "## By Dataset",
        "",
        "| Dataset | Count | % |",
        "|---------|-------|---|",
    ]
    for ds, count in stats["by_dataset"].most_common():
        pct = count / stats["total"] * 100
        lines.append(f"| {ds} | {count:,} | {pct:.1f}% |")

    lines += [
        "",
        "## By Category",
        "",
        "| # | Category | Total | MedMCQA | PubMedQA | % of Total |",
        "|---|----------|-------|---------|----------|------------|",
    ]
    for i, (cat, count) in enumerate(
        sorted(stats["by_category"].items(), key=lambda x: -x[1]), 1
    ):
        label = CATEGORY_LABELS.get(cat, cat)
        med = stats["by_category_dataset"][cat].get("medmcqa", 0)
        pub = stats["by_category_dataset"][cat].get("pubmedqa", 0)
        pct = count / stats["total"] * 100
        lines.append(f"| {i} | {label} | {count:,} | {med:,} | {pub:,} | {pct:.1f}% |")

    lines += [
        "",
        "## Explanation Quality Tiers",
        "",
        "| Tier | Count | % | Description |",
        "|------|-------|---|-------------|",
    ]
    tier_desc = {
        "TIER_A": "Reference-cited (textbook + page)",
        "TIER_B": "Mechanism-based (pathophysiology explained)",
        "TIER_C": "Minimal (answer only, no reasoning)",
        "TIER_D": "Null (no explanation)",
    }
    for tier in ["TIER_A", "TIER_B", "TIER_C", "TIER_D"]:
        count = stats["by_tier"].get(tier, 0)
        pct = count / stats["total"] * 100 if stats["total"] else 0
        lines.append(f"| {tier} | {count:,} | {pct:.1f}% | {tier_desc.get(tier, '')} |")

    lines += [
        "",
        "## Missing Explanations by Category",
        "",
        "| Category | Missing Count | % of Category |",
        "|----------|---------------|---------------|",
    ]
    for cat, missing_count in sorted(
        stats["no_explanation_by_category"].items(), key=lambda x: -x[1]
    ):
        total_cat = stats["by_category"].get(cat, 1)
        pct = missing_count / total_cat * 100
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"| {label} | {missing_count:,} | {pct:.1f}% |")

    lines += [
        "",
        "## MedMCQA Subject Distribution (in sample)",
        "",
        "| Subject | Count |",
        "|---------|-------|",
    ]
    for subject, count in stats["by_subject"].most_common():
        if subject:
            lines.append(f"| {subject} | {count:,} |")

    lines += [
        "",
        "## Secondary Category Tags",
        "",
        "| Secondary Category | Count |",
        "|-------------------|-------|",
    ]
    for cat, count in stats["secondary_category"].most_common(10):
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"| {label} | {count:,} |")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote stats to {output_path}")


def write_directory_md(stats: dict, output_path: Path) -> None:
    """Write directory.md master index."""
    lines = [
        "<!-- STATUS: DRAFT -- awaiting human review -->",
        "",
        "# Healthcare Knowledge Directory",
        "",
        "Master index of all consumer-facing health categories derived from",
        "MedMCQA (194k medical MCQs) and PubMedQA (273k biomedical research QA).",
        "",
        "## Categories",
        "",
        "| # | Category | Total | MedMCQA | PubMedQA | Quality Tier A% | File |",
        "|---|----------|-------|---------|----------|-----------------|------|",
    ]
    for i, (cat, count) in enumerate(
        sorted(stats["by_category"].items(), key=lambda x: -x[1]), 1
    ):
        label = CATEGORY_LABELS.get(cat, cat)
        med = stats["by_category_dataset"][cat].get("medmcqa", 0)
        pub = stats["by_category_dataset"][cat].get("pubmedqa", 0)
        tier_a = stats["by_tier_category"][cat].get("TIER_A", 0)
        tier_a_pct = tier_a / count * 100 if count else 0
        lines.append(
            f"| {i} | {label} | {count:,} | {med:,} | {pub:,} | "
            f"{tier_a_pct:.0f}% | [{cat}.md](categories/{cat}.md) |"
        )

    lines += [
        "",
        "## Source Trust Hierarchy",
        "",
        "1. **PubMedQA** -- peer-reviewed abstracts with structured evidence",
        "2. **MedMCQA TIER_A** -- textbook-referenced explanations",
        "3. **MedMCQA TIER_B** -- mechanism-based explanations",
        "4. **MedMCQA TIER_C** -- answer-only, no reasoning",
        "5. **MedMCQA TIER_D** -- question-answer pair only, no explanation",
        "",
        "## Cross-Dataset Coverage Gaps",
        "",
        "| Category | MedMCQA | PubMedQA | Gap |",
        "|----------|---------|----------|-----|",
    ]
    for cat in sorted(stats["by_category"].keys()):
        label = CATEGORY_LABELS.get(cat, cat)
        med = stats["by_category_dataset"][cat].get("medmcqa", 0)
        pub = stats["by_category_dataset"][cat].get("pubmedqa", 0)
        if pub == 0:
            gap = "MedMCQA only -- need external dataset"
        elif med == 0:
            gap = "PubMedQA only"
        elif pub < med * 0.1:
            gap = "Low PubMedQA coverage"
        else:
            gap = "Good coverage"
        lines.append(f"| {label} | {med:,} | {pub:,} | {gap} |")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote directory to {output_path}")


def write_general_rules(output_path: Path) -> None:
    """Write general_rules.md."""
    content = """<!-- STATUS: DRAFT -- awaiting human review -->

# General Rules -- Cross-Category Quality & Verification

## Source Quality Rules

- **TIER_A explanations** (reference-cited) are preferred retrieval sources for the RAG pipeline
- **TIER_D** (null explanation) questions provide question-answer pairs only, not explanatory knowledge
- **PubMedQA entries** with RESULTS section labels have empirical evidence backing
- Cross-verify claims appearing in only **one question** across both datasets
- Textbook citations in MedMCQA `exp` field indicate authoritative references per domain:
  - **Medicine**: Harrison's Internal Medicine, Davidson's
  - **Pathology**: Robbins Pathologic Basis of Disease
  - **Surgery**: Bailey & Love, Sabiston, Schwartz
  - **Pharmacology**: KD Tripathi, Goodman & Gilman
  - **Preventive Medicine**: Park's Textbook
  - **Physiology**: Ganong, Guyton
  - **Ophthalmology**: Khurana, Yanoff
  - **Obstetrics/Gynaecology**: Shaw's, Dutta
  - **Pediatrics**: Nelson's, OP Ghai
  - **Anatomy**: BDC (BD Chaurasia), Snell
  - **Biochemistry**: Harper
  - **Microbiology**: Ananthanarayan, Jawetz

## Verification Rules

- **Drug interactions**: verify against at least 2 independent questions in the dataset
- **Statistics/percentages** (e.g., "90% sensitivity"): flag for external verification against current guidelines
- **Contradictory explanations** for same topic across questions: flag for human review
- **MedMCQA vs PubMedQA disagreements**: flag and prefer PubMedQA (peer-reviewed)
- **Outdated references**: flag MedMCQA explanations citing editions >10 years old for guideline checks

## Source Trust Hierarchy

1. PubMedQA (peer-reviewed abstracts with structured evidence)
2. MedMCQA TIER_A (textbook-referenced explanations)
3. MedMCQA TIER_B (mechanism-based explanations)
4. MedMCQA TIER_C (answer-only, no reasoning)
5. MedMCQA TIER_D (question-answer pair only, no explanation)

## Data Quality Warnings

- **Dental** subject has ~50%+ null explanations -- treat with low confidence
- **Unknown** subject contains miscategorized questions -- always content-analyze
- **~30-40% of MedMCQA rows** have null `topic_name` -- category assignment relies on content analysis
- **PubMedQA** questions are research-oriented, not consumer language -- need translation layer
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote general rules to {output_path}")


# ─── AUTO-GENERATED Block Markers ────────────────────────────────────────────

AUTO_START = "<!-- ====== AUTO-GENERATED \u2014 DO NOT EDIT BELOW THIS LINE ====== -->"
AUTO_END   = "<!-- ====== AUTO-GENERATED \u2014 DO NOT EDIT ABOVE THIS LINE ====== -->"


def _build_auto_block(
    cat: str,
    stats: dict,
    results: list[dict],
    links: dict | None = None,
) -> str:
    """Build the content of the AUTO-GENERATED block (between the markers)."""
    cat_results = [r for r in results if r["primary_category"] == cat]
    total = stats["by_category"].get(cat, 0)
    tiers = stats["by_tier_category"].get(cat, {})
    med_count = stats["by_category_dataset"].get(cat, {}).get("medmcqa", 0)
    pub_count = stats["by_category_dataset"].get(cat, {}).get("pubmedqa", 0)
    mq_count = stats["by_category_dataset"].get(cat, {}).get("medquad", 0)
    missing = stats["no_explanation_by_category"].get(cat, 0)

    # Top contributing MedMCQA subjects
    subject_counts: Counter = Counter()
    for r in cat_results:
        if r["subject_name"] and r["dataset"] == "medmcqa":
            subject_counts[r["subject_name"]] += 1

    # Sample questions
    samples = cat_results[:5]

    lines = [
        "## Data Coverage",
        "",
        f"- **Total**: {total:,} | MedMCQA: {med_count:,} | PubMedQA: {pub_count:,} | MedQuAD: {mq_count:,}",
        (
            f"- **Missing explanations**: {missing:,} ({missing/total*100:.1f}%)"
            if total
            else f"- **Missing explanations**: {missing:,}"
        ),
        "",
        "## Quality Tiers",
        "",
        "| Tier | Count | % |",
        "|------|-------|---|",
    ]
    for tier in ["TIER_A", "TIER_B", "TIER_C", "TIER_D"]:
        count = tiers.get(tier, 0)
        pct = count / total * 100 if total else 0
        lines.append(f"| {tier} | {count:,} | {pct:.0f}% |")

    lines += [
        "",
        "## Contributing MedMCQA Subjects",
        "",
        "| Subject | Count |",
        "|---------|-------|",
    ]
    for subject, count in subject_counts.most_common(10):
        lines.append(f"| {subject} | {count:,} |")

    lines += ["", "## Sample Questions", ""]
    for s in samples:
        q = s["question"][:150]
        lines.append(f"- [{s['dataset']}] [{s['quality_tier']}] {q}...")

    # Links section (data-driven from co-occurrence)
    cat_links = (links or {}).get(cat, {})
    strong = cat_links.get("strong", [])
    weak = cat_links.get("weak", [])

    lines += [
        "",
        "## Links",
        f"<!-- Derived from secondary_category co-occurrence in {total:,} DB records -->",
    ]
    if strong:
        lines.append("- **Strong links:**")
        for linked_cat, count in strong:
            linked_label = CATEGORY_LABELS.get(linked_cat, linked_cat)
            lines.append(f"  - [{linked_label}]({linked_cat}.md) \u2014 {count:,} cross-hits")
    else:
        lines.append("- **Strong links:** *(TBD \u2014 run --rebuild-brain to populate)*")

    if weak:
        lines.append("- **Weak links:**")
        for linked_cat, count in weak:
            linked_label = CATEGORY_LABELS.get(linked_cat, linked_cat)
            lines.append(f"  - [{linked_label}]({linked_cat}.md) \u2014 {count:,} cross-hits")
    else:
        lines.append("- **Weak links:** *(TBD \u2014 run --rebuild-brain to populate)*")

    return "\n".join(lines)


def _replace_auto_block(existing: str, new_auto_block: str) -> str:
    """Replace the AUTO-GENERATED block in an existing file. Returns updated content."""
    start_idx = existing.find(AUTO_START)
    end_idx = existing.find(AUTO_END)

    if start_idx == -1 or end_idx == -1:
        # No markers found — insert after the title line
        lines = existing.split("\n")
        title_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("# "):
                title_idx = i
                break
        before = "\n".join(lines[: title_idx + 1])
        after = "\n".join(lines[title_idx + 1 :])
        return f"{before}\n\n{AUTO_START}\n{new_auto_block}\n{AUTO_END}\n{after}"

    before = existing[: start_idx]
    after = existing[end_idx + len(AUTO_END) :]
    return f"{before}{AUTO_START}\n{new_auto_block}\n{AUTO_END}{after}"


def _replace_knowledge_sections(content: str, enrichment: dict) -> str:
    """
    Replace the knowledge sections (Source Priority, Terminology Map, etc.)
    with Claude-generated enriched content.

    The knowledge sections live after the AUTO_END marker.
    """
    end_idx = content.find(AUTO_END)
    if end_idx == -1:
        return content

    # Keep everything up to and including the AUTO_END marker
    before = content[: end_idx + len(AUTO_END)]

    lines = ["\n"]

    # Metadata / subcategories
    if enrichment.get("subcategories"):
        lines += [
            "## Metadata",
            f"- **Subcategories:** {enrichment['subcategories']}",
            "- **Confidence:** High",
            "",
        ]

    # Source Priority
    if enrichment.get("source_priority"):
        lines.append("## Source Priority")
        for i, item in enumerate(enrichment["source_priority"], 1):
            lines.append(f"{i}. {item}")
        if enrichment.get("source_priority_rationale"):
            lines.append(f"**Rationale:** {enrichment['source_priority_rationale']}")
        lines.append("")

    # Terminology Map
    if enrichment.get("terminology_map"):
        lines += [
            "## Terminology Map",
            "| Consumer Term | Medical Term | Notes |",
            "|--------------|-------------|-------|",
        ]
        for entry in enrichment["terminology_map"]:
            consumer = entry.get("consumer_term", "")
            medical = entry.get("medical_term", "")
            notes = entry.get("notes", "")
            lines.append(f"| {consumer} | {medical} | {notes} |")
        lines.append("")

    # Common Query Patterns
    if enrichment.get("query_patterns"):
        lines.append("## Common Query Patterns")
        for pattern in enrichment["query_patterns"]:
            lines.append(f"- {pattern}")
        lines.append("")

    # Category-Specific Rules
    if enrichment.get("rules"):
        lines.append("## Category-Specific Rules")
        for rule in enrichment["rules"]:
            lines.append(f"- {rule}")
        lines.append("")

    # Known Pitfalls
    if enrichment.get("pitfalls"):
        lines.append("## Known Pitfalls")
        for pitfall in enrichment["pitfalls"]:
            lines.append(f"- {pitfall}")
        lines.append("")

    # Dominant Explanation Style
    if enrichment.get("dominant_style"):
        lines += ["## Dominant Explanation Style", enrichment["dominant_style"], ""]

    return before + "\n".join(lines) + "\n"


def _build_knowledge_placeholder() -> str:
    """Build placeholder knowledge sections for a brand-new category file."""
    return """\n## Metadata
- **Source subjects:** *(TBD \u2014 run --rebuild-brain --enrich to populate)*
- **Subcategories:** *(TBD)*
- **Confidence:** Draft

## Source Priority
1. *(TBD \u2014 run --rebuild-brain --enrich to populate)*

**Rationale:** *(TBD)*

## Terminology Map
| Consumer Term | Medical Term | Notes |
|--------------|-------------|-------|
| *(TBD)* | *(TBD)* | *(TBD)* |

## Common Query Patterns
- *(TBD \u2014 run --rebuild-brain --enrich to populate)*

## Category-Specific Rules
- *(TBD \u2014 run --rebuild-brain --enrich to populate)*

## Known Pitfalls
- *(TBD \u2014 run --rebuild-brain --enrich to populate)*

## Dominant Explanation Style
*(TBD \u2014 run --rebuild-brain --enrich to populate)*
"""


def write_category_files(
    stats: dict,
    results: list[dict],
    output_dir: Path,
    links: dict | None = None,
    enrichment: dict | None = None,
) -> None:
    """
    Write per-category markdown files using a merge strategy.

    - If file exists: only the AUTO-GENERATED block is replaced.
      All human/AI-authored knowledge sections are left untouched.
    - If file does not exist: a full template is written (auto block + placeholders).
    - If enrichment is provided: knowledge sections are also replaced with
      Claude-generated content.
    """
    for cat in CATEGORIES:
        label = CATEGORY_LABELS.get(cat, cat)
        auto_block = _build_auto_block(cat, stats, results, links)
        filepath = output_dir / f"{cat}.md"

        if filepath.exists():
            existing = filepath.read_text(encoding="utf-8")
            new_content = _replace_auto_block(existing, auto_block)
        else:
            # First-time: full template
            knowledge = _build_knowledge_placeholder()
            new_content = (
                f"<!-- STATUS: DRAFT -- awaiting human review -->\n\n"
                f"# {label}\n\n"
                f"{AUTO_START}\n{auto_block}\n{AUTO_END}\n"
                f"{knowledge}"
            )

        if enrichment and cat in enrichment:
            new_content = _replace_knowledge_sections(new_content, enrichment[cat])

        filepath.write_text(new_content, encoding="utf-8")

    print(f"Wrote {len(CATEGORIES)} category files to {output_dir}")


def write_review_files(results: list[dict], review_dir: Path) -> None:
    """Write review queue files."""
    no_exp = [r for r in results if not r["has_explanation"] and r["dataset"] == "medmcqa"]
    ambiguous = [r for r in results if r["secondary_category"]]

    # flagged_no_explanation.md
    lines = [
        "<!-- STATUS: DRAFT -- awaiting human review -->",
        "",
        "# Questions Missing Explanations",
        "",
        f"**Total in sample**: {len(no_exp):,}",
        "",
        "## By Category",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    cat_counts = Counter(r["primary_category"] for r in no_exp)
    for cat, count in cat_counts.most_common():
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"| {label} | {count:,} |")

    lines += [
        "",
        "## Sample (first 20)",
        "",
    ]
    for r in no_exp[:20]:
        lines.append(f"- `{r['id']}` [{r['primary_category']}] {r['question'][:120]}...")

    with open(review_dir / "flagged_no_explanation.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # flagged_ambiguous.md (questions with secondary categories)
    lines = [
        "<!-- STATUS: DRAFT -- awaiting human review -->",
        "",
        "# Questions With Multiple Category Assignments",
        "",
        f"**Total in sample**: {len(ambiguous):,}",
        "",
        "These questions were assigned both a primary and secondary category.",
        "Human review should confirm the primary assignment.",
        "",
        "## Top Cross-Category Pairs",
        "",
        "| Primary | Secondary | Count |",
        "|---------|-----------|-------|",
    ]
    pair_counts = Counter((r["primary_category"], r["secondary_category"]) for r in ambiguous)
    for (p, s), count in pair_counts.most_common(20):
        pl = CATEGORY_LABELS.get(p, p)
        sl = CATEGORY_LABELS.get(s, s)
        lines.append(f"| {pl} | {sl} | {count:,} |")

    with open(review_dir / "flagged_ambiguous.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # human_review_queue.md
    lines = [
        "<!-- STATUS: DRAFT -- awaiting human review -->",
        "",
        "# Human Review Queue",
        "",
        "## Actions Required",
        "",
        "- [ ] Review and approve/modify the 20 consumer-facing categories",
        "- [ ] Review flagged questions with no explanations (especially Dental)",
        "- [ ] Review multi-category assignments and confirm primary category",
        "- [ ] Review source priority rankings per category",
        "- [ ] Add consumer term -> medical term mappings per category",
        "- [ ] Add category-specific verification rules",
        "- [ ] Review MeSH-to-category mapping for accuracy",
        "- [ ] Identify categories needing external datasets (Dental, etc.)",
        "",
        "## Category Approval Status",
        "",
        "| # | Category | Status |",
        "|---|----------|--------|",
    ]
    for i, cat in enumerate(CATEGORIES, 1):
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"| {i} | {label} | DRAFT |")

    with open(review_dir / "human_review_queue.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote review files to {review_dir}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Categorize medical QA datasets")
    parser.add_argument(
        "--source",
        choices=["medmcqa", "pubmedqa", "both"],
        default="both",
        help="Which dataset(s) to process",
    )
    parser.add_argument(
        "--batches",
        type=int,
        default=50,
        help="Number of batches to fetch per dataset (100 rows each)",
    )
    parser.add_argument(
        "--pubmedqa-batches",
        type=int,
        default=20,
        help="Number of PubMedQA batches (if different from --batches)",
    )
    args = parser.parse_args()

    os.makedirs(BRAIN_DIR / "categories", exist_ok=True)
    os.makedirs(BRAIN_DIR / "review", exist_ok=True)

    all_results = []
    mesh_map = {}

    if args.source in ("medmcqa", "both"):
        med_results = process_medmcqa(num_batches=args.batches)
        all_results.extend(med_results)

    if args.source in ("pubmedqa", "both"):
        pub_batches = args.pubmedqa_batches or args.batches
        pub_results, mesh_map = process_pubmedqa(num_batches=pub_batches)
        all_results.extend(pub_results)

    if not all_results:
        print("No results to process.")
        return

    print(f"\nTotal categorized: {len(all_results)}")

    # Write outputs
    write_category_mapping(all_results, BRAIN_DIR / "category_mapping.csv")

    if mesh_map:
        write_mesh_mapping(mesh_map, BRAIN_DIR / "mesh_to_category.csv")

    stats = compute_stats(all_results)
    write_stats_md(stats, BRAIN_DIR / "stats.md")
    write_directory_md(stats, BRAIN_DIR / "directory.md")
    write_general_rules(BRAIN_DIR / "general_rules.md")
    write_category_files(stats, all_results, BRAIN_DIR / "categories")
    write_review_files(all_results, BRAIN_DIR / "review")

    print("\nDone! Brain files written to:", BRAIN_DIR)
    print("All files marked as DRAFT -- awaiting human review.")


if __name__ == "__main__":
    main()
