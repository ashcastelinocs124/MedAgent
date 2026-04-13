# src/personalization/condition_registry.py
"""Condition checklist, medication keywords, and free-text matching.

Deterministic mapping layer — no LLM, no DB.
"""
from __future__ import annotations

import re
from src.personalization.models import Condition, Medication

# ── Condition Checklist ──────────────────────────────────────────────────────
# Each item maps a user-facing checkbox to a Condition object.
# key: unique identifier sent from the frontend
# name: display label the user sees
# group: visual grouping in the wizard UI
# category_id / subcategory_id: map into the brain graph

CONDITION_CHECKLIST: list[dict] = [
    # Heart & Blood Vessels
    {"key": "hypertension", "name": "High blood pressure", "group": "Heart & Blood Vessels",
     "category_id": "heart_blood_vessels", "subcategory_id": "hypertension_blood_pressure"},
    {"key": "heart_failure", "name": "Heart failure", "group": "Heart & Blood Vessels",
     "category_id": "heart_blood_vessels", "subcategory_id": "heart_failure_fluid_retention"},
    {"key": "high_cholesterol", "name": "High cholesterol", "group": "Heart & Blood Vessels",
     "category_id": "heart_blood_vessels", "subcategory_id": "cholesterol_atherosclerosis"},
    {"key": "arrhythmia", "name": "Heart rhythm problems", "group": "Heart & Blood Vessels",
     "category_id": "heart_blood_vessels", "subcategory_id": "heart_rhythm_palpitations"},

    # Diabetes & Metabolism
    {"key": "type2_diabetes", "name": "Type 2 diabetes", "group": "Diabetes & Metabolism",
     "category_id": "hormones_metabolism_nutrition", "subcategory_id": "diabetes_type_1_type_2_gestational"},
    {"key": "type1_diabetes", "name": "Type 1 diabetes", "group": "Diabetes & Metabolism",
     "category_id": "hormones_metabolism_nutrition", "subcategory_id": "diabetes_type_1_type_2_gestational"},
    {"key": "thyroid", "name": "Thyroid disorder", "group": "Diabetes & Metabolism",
     "category_id": "hormones_metabolism_nutrition", "subcategory_id": "thyroid_disorders"},
    {"key": "obesity", "name": "Obesity", "group": "Diabetes & Metabolism",
     "category_id": "hormones_metabolism_nutrition", "subcategory_id": "nutrition_dietary_guidelines"},

    # Mental Health
    {"key": "depression", "name": "Depression", "group": "Mental Health",
     "category_id": "mental_health", "subcategory_id": "depression_mood_disorders"},
    {"key": "anxiety", "name": "Anxiety", "group": "Mental Health",
     "category_id": "mental_health", "subcategory_id": "anxiety_ocd"},
    {"key": "bipolar", "name": "Bipolar disorder", "group": "Mental Health",
     "category_id": "mental_health", "subcategory_id": "schizophrenia_psychosis"},
    {"key": "ptsd", "name": "PTSD", "group": "Mental Health",
     "category_id": "mental_health", "subcategory_id": "anxiety_ocd"},
    {"key": "insomnia", "name": "Insomnia", "group": "Mental Health",
     "category_id": "mental_health", "subcategory_id": "sleep_disorders"},

    # Breathing & Lungs
    {"key": "asthma", "name": "Asthma", "group": "Breathing & Lungs",
     "category_id": "breathing_lungs", "subcategory_id": "asthma"},
    {"key": "copd", "name": "COPD", "group": "Breathing & Lungs",
     "category_id": "breathing_lungs", "subcategory_id": "copd"},
    {"key": "sleep_apnea", "name": "Sleep apnea", "group": "Breathing & Lungs",
     "category_id": "breathing_lungs", "subcategory_id": "copd"},

    # Digestive
    {"key": "gerd", "name": "Acid reflux / GERD", "group": "Digestive",
     "category_id": "digestive_liver", "subcategory_id": "stomach_peptic_ulcers"},
    {"key": "ibs", "name": "IBS", "group": "Digestive",
     "category_id": "digestive_liver", "subcategory_id": "inflammatory_bowel_disease"},
    {"key": "crohns_colitis", "name": "Crohn's / Colitis", "group": "Digestive",
     "category_id": "digestive_liver", "subcategory_id": "inflammatory_bowel_disease"},
    {"key": "liver_disease", "name": "Liver disease", "group": "Digestive",
     "category_id": "digestive_liver", "subcategory_id": "liver_disease_hepatitis"},

    # Bones & Joints
    {"key": "arthritis", "name": "Arthritis", "group": "Bones & Joints",
     "category_id": "bones_joints_muscles", "subcategory_id": "arthritis_oa_ra"},
    {"key": "osteoporosis", "name": "Osteoporosis", "group": "Bones & Joints",
     "category_id": "bones_joints_muscles", "subcategory_id": "metabolic_bone_disease_osteoporosis"},
    {"key": "back_pain", "name": "Back pain", "group": "Bones & Joints",
     "category_id": "bones_joints_muscles", "subcategory_id": "spinal_disorders"},
    {"key": "fibromyalgia", "name": "Fibromyalgia", "group": "Bones & Joints",
     "category_id": "bones_joints_muscles", "subcategory_id": "soft_tissue_injuries"},

    # Kidney & Urinary
    {"key": "ckd", "name": "Chronic kidney disease", "group": "Kidney & Urinary",
     "category_id": "kidney_urinary", "subcategory_id": "chronic_kidney_disease"},
    {"key": "kidney_stones", "name": "Kidney stones", "group": "Kidney & Urinary",
     "category_id": "kidney_urinary", "subcategory_id": "kidney_stones"},
    {"key": "enlarged_prostate", "name": "Enlarged prostate", "group": "Kidney & Urinary",
     "category_id": "kidney_urinary", "subcategory_id": "prostate_disorders"},

    # Cancer
    {"key": "breast_cancer", "name": "Breast cancer", "group": "Cancer",
     "category_id": "cancer", "subcategory_id": "breast_cancer"},
    {"key": "lung_cancer", "name": "Lung cancer", "group": "Cancer",
     "category_id": "cancer", "subcategory_id": "lung_cancer"},
    {"key": "colon_cancer", "name": "Colon cancer", "group": "Cancer",
     "category_id": "cancer", "subcategory_id": "gi_cancers"},
    {"key": "prostate_cancer", "name": "Prostate cancer", "group": "Cancer",
     "category_id": "cancer", "subcategory_id": "prostate_cancer"},
    {"key": "skin_cancer", "name": "Skin cancer", "group": "Cancer",
     "category_id": "cancer", "subcategory_id": "skin_cancer"},

    # Blood & Immune
    {"key": "anemia", "name": "Anemia", "group": "Blood & Immune",
     "category_id": "blood_immune", "subcategory_id": "anemia_iron_deficiency_sickle_cell_thalassemia"},
    {"key": "autoimmune", "name": "Autoimmune condition (lupus, RA)", "group": "Blood & Immune",
     "category_id": "blood_immune", "subcategory_id": "autoimmune_conditions"},
    {"key": "clotting_disorder", "name": "Blood clotting disorder", "group": "Blood & Immune",
     "category_id": "blood_immune", "subcategory_id": "bleeding_disorders"},

    # Brain & Nervous System
    {"key": "migraines", "name": "Migraines", "group": "Brain & Nervous System",
     "category_id": "brain_nervous_system", "subcategory_id": "headache_migraine"},
    {"key": "epilepsy", "name": "Epilepsy", "group": "Brain & Nervous System",
     "category_id": "brain_nervous_system", "subcategory_id": "seizures_epilepsy"},
    {"key": "parkinsons", "name": "Parkinson's", "group": "Brain & Nervous System",
     "category_id": "brain_nervous_system", "subcategory_id": "neurodegenerative_diseases"},
    {"key": "neuropathy", "name": "Neuropathy", "group": "Brain & Nervous System",
     "category_id": "brain_nervous_system", "subcategory_id": "peripheral_neuropathy"},

    # Women's Health
    {"key": "endometriosis", "name": "Endometriosis", "group": "Women's Health",
     "category_id": "womens_reproductive", "subcategory_id": "menstrual_disorders"},
    {"key": "pcos", "name": "PCOS", "group": "Women's Health",
     "category_id": "womens_reproductive", "subcategory_id": "infertility"},
    {"key": "menopause", "name": "Menopause symptoms", "group": "Women's Health",
     "category_id": "womens_reproductive", "subcategory_id": "menopause"},

    # Skin
    {"key": "eczema", "name": "Eczema", "group": "Skin",
     "category_id": "skin_dermatology", "subcategory_id": "eczema_dermatitis"},
    {"key": "psoriasis", "name": "Psoriasis", "group": "Skin",
     "category_id": "skin_dermatology", "subcategory_id": "psoriasis"},

    # Infections
    {"key": "hiv", "name": "HIV", "group": "Infections",
     "category_id": "infections", "subcategory_id": "viral_infections_hiv_hepatitis_influenza"},
    {"key": "hepatitis", "name": "Hepatitis B/C", "group": "Infections",
     "category_id": "infections", "subcategory_id": "viral_infections_hiv_hepatitis_influenza"},

    # Eyes
    {"key": "glaucoma", "name": "Glaucoma", "group": "Eyes",
     "category_id": "eye_health", "subcategory_id": "glaucoma"},
    {"key": "macular_degeneration", "name": "Macular degeneration", "group": "Eyes",
     "category_id": "eye_health", "subcategory_id": "retinal_diseases"},
]

_CHECKLIST_BY_KEY: dict[str, dict] = {item["key"]: item for item in CONDITION_CHECKLIST}


# ── Medication Keywords ──────────────────────────────────────────────────────
# Maps lowercase drug name substring → category_id.

MEDICATION_KEYWORDS: dict[str, str] = {
    # Heart & Blood Vessels
    "lisinopril": "heart_blood_vessels", "enalapril": "heart_blood_vessels",
    "losartan": "heart_blood_vessels", "valsartan": "heart_blood_vessels",
    "amlodipine": "heart_blood_vessels", "metoprolol": "heart_blood_vessels",
    "atenolol": "heart_blood_vessels", "propranolol": "heart_blood_vessels",
    "atorvastatin": "heart_blood_vessels", "rosuvastatin": "heart_blood_vessels",
    "simvastatin": "heart_blood_vessels", "clopidogrel": "heart_blood_vessels",
    "aspirin": "heart_blood_vessels", "warfarin": "heart_blood_vessels",
    "apixaban": "heart_blood_vessels", "rivaroxaban": "heart_blood_vessels",
    "digoxin": "heart_blood_vessels", "diltiazem": "heart_blood_vessels",
    "furosemide": "heart_blood_vessels", "hydrochlorothiazide": "heart_blood_vessels",
    "spironolactone": "heart_blood_vessels",
    # Hormones & Metabolism
    "metformin": "hormones_metabolism_nutrition", "insulin": "hormones_metabolism_nutrition",
    "glipizide": "hormones_metabolism_nutrition", "glyburide": "hormones_metabolism_nutrition",
    "sitagliptin": "hormones_metabolism_nutrition", "empagliflozin": "hormones_metabolism_nutrition",
    "semaglutide": "hormones_metabolism_nutrition", "liraglutide": "hormones_metabolism_nutrition",
    "levothyroxine": "hormones_metabolism_nutrition", "synthroid": "hormones_metabolism_nutrition",
    "pioglitazone": "hormones_metabolism_nutrition",
    # Mental Health
    "sertraline": "mental_health", "fluoxetine": "mental_health",
    "escitalopram": "mental_health", "citalopram": "mental_health",
    "venlafaxine": "mental_health", "duloxetine": "mental_health",
    "bupropion": "mental_health", "mirtazapine": "mental_health",
    "lithium": "mental_health", "quetiapine": "mental_health",
    "aripiprazole": "mental_health", "olanzapine": "mental_health",
    "alprazolam": "mental_health", "lorazepam": "mental_health",
    "diazepam": "mental_health", "clonazepam": "mental_health",
    "trazodone": "mental_health", "zolpidem": "mental_health",
    # Breathing & Lungs
    "albuterol": "breathing_lungs", "fluticasone": "breathing_lungs",
    "budesonide": "breathing_lungs", "montelukast": "breathing_lungs",
    "tiotropium": "breathing_lungs", "ipratropium": "breathing_lungs",
    # Digestive
    "omeprazole": "digestive_liver", "pantoprazole": "digestive_liver",
    "esomeprazole": "digestive_liver", "famotidine": "digestive_liver",
    "mesalamine": "digestive_liver",
    # Pain & Inflammation
    "ibuprofen": "medications_drug_safety", "naproxen": "medications_drug_safety",
    "acetaminophen": "medications_drug_safety", "gabapentin": "brain_nervous_system",
    "pregabalin": "brain_nervous_system", "tramadol": "medications_drug_safety",
    "oxycodone": "medications_drug_safety", "hydrocodone": "medications_drug_safety",
    # Bones & Joints
    "alendronate": "bones_joints_muscles", "methotrexate": "bones_joints_muscles",
    "adalimumab": "blood_immune", "etanercept": "blood_immune",
    # Infections
    "amoxicillin": "infections", "azithromycin": "infections",
    "doxycycline": "infections", "ciprofloxacin": "infections",
    # Seizures
    "phenytoin": "brain_nervous_system", "carbamazepine": "brain_nervous_system",
    "valproic acid": "brain_nervous_system", "levetiracetam": "brain_nervous_system",
    "lamotrigine": "brain_nervous_system",
    # Eye
    "latanoprost": "eye_health", "timolol": "eye_health",
    # Skin
    "hydrocortisone": "skin_dermatology", "tacrolimus": "skin_dermatology",
    # Cancer
    "tamoxifen": "cancer", "letrozole": "cancer",
}


# ── Free-text Condition Keywords ─────────────────────────────────────────────
# Maps keyword substrings found in free-text to (category_id, subcategory_id).

_FREETEXT_MAP: list[tuple[list[str], str, str]] = [
    (["celiac", "coeliac"], "digestive_liver", "inflammatory_bowel_disease"),
    (["rosacea"], "skin_dermatology", "eczema_dermatitis"),
    (["lupus"], "blood_immune", "autoimmune_conditions"),
    (["fibromyalgia"], "bones_joints_muscles", "soft_tissue_injuries"),
    (["gout"], "bones_joints_muscles", "arthritis_oa_ra"),
    (["scoliosis"], "bones_joints_muscles", "spinal_disorders"),
    (["vertigo"], "ear_nose_throat", "vertigo_balance"),
    (["tinnitus"], "ear_nose_throat", "hearing_loss_ear_infections"),
    (["raynaud"], "heart_blood_vessels", "peripheral_artery_vein_disease"),
    (["diverticulit"], "digestive_liver", "inflammatory_bowel_disease"),
    (["gallstone"], "digestive_liver", "gallbladder_bile_ducts"),
    (["hemorrhoid"], "digestive_liver", "stomach_peptic_ulcers"),
    (["hernia"], "digestive_liver", "stomach_peptic_ulcers"),
    (["sciatica"], "bones_joints_muscles", "spinal_disorders"),
    (["carpal tunnel"], "bones_joints_muscles", "soft_tissue_injuries"),
    (["plantar fasciitis"], "bones_joints_muscles", "soft_tissue_injuries"),
    (["interstitial cystitis"], "kidney_urinary", "chronic_kidney_disease"),
    (["polycythemia"], "blood_immune", "anemia_iron_deficiency_sickle_cell_thalassemia"),
    (["sickle cell"], "blood_immune", "anemia_iron_deficiency_sickle_cell_thalassemia"),
    (["multiple sclerosis", " ms "], "brain_nervous_system", "neurodegenerative_diseases"),
    (["als", "amyotrophic"], "brain_nervous_system", "neurodegenerative_diseases"),
    (["alzheimer"], "brain_nervous_system", "neurodegenerative_diseases"),
    (["dementia"], "brain_nervous_system", "neurodegenerative_diseases"),
    (["restless leg"], "brain_nervous_system", "peripheral_neuropathy"),
    (["chronic fatigue"], "blood_immune", "autoimmune_conditions"),
    (["shingles"], "infections", "viral_infections_hiv_hepatitis_influenza"),
    (["lyme"], "infections", "bacterial_infections"),
]


# ── Public Functions ─────────────────────────────────────────────────────────

def resolve_conditions(selected_keys: list[str]) -> list[Condition]:
    """Map selected checklist keys to Condition objects."""
    result = []
    for key in selected_keys:
        item = _CHECKLIST_BY_KEY.get(key)
        if item:
            result.append(Condition(
                name=item["name"],
                category_id=item["category_id"],
                subcategory_id=item["subcategory_id"],
                active=True,
            ))
    return result


def resolve_medications(med_names: list[str]) -> list[Medication]:
    """Map medication names to Medication objects via keyword matching."""
    result = []
    for name in med_names:
        name_stripped = name.strip()
        if not name_stripped:
            continue
        name_lower = name_stripped.lower()
        matched_cat = None
        for keyword, cat_id in MEDICATION_KEYWORDS.items():
            if keyword in name_lower:
                matched_cat = cat_id
                break
        result.append(Medication(
            name=name_stripped,
            category_id=matched_cat or "medications_drug_safety",
        ))
    return result


def match_freetext_conditions(text: str) -> list[Condition]:
    """Match free-text input against known condition keywords."""
    if not text or not text.strip():
        return []
    text_lower = f" {text.lower()} "
    result = []
    seen_cats: set[tuple[str, str]] = set()
    for keywords, cat_id, subcat_id in _FREETEXT_MAP:
        for kw in keywords:
            if kw.lower() in text_lower:
                key = (cat_id, subcat_id)
                if key not in seen_cats:
                    seen_cats.add(key)
                    result.append(Condition(
                        name=kw.strip().title(),
                        category_id=cat_id,
                        subcategory_id=subcat_id,
                        active=True,
                    ))
                break
    return result
