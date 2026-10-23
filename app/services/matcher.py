import re
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import WEIGHT_SKILLS, WEIGHT_SEMANTIC, WEIGHT_EXPERIENCE, WEIGHT_EDUCATION
from app.models.schemas import ScoreBreakdown

TIER_RANKS = {
    "Doctorate / Ph.D.": 4,
    "Master's Degree": 3,
    "Bachelor's Degree": 2,
    "Diploma / Associate": 1,
    "Not Specified": 1
}

def clean_text_for_nlp(text: str) -> str:
    """
    Standardizes whitespace and removes unwanted punctuation while preserving tech keywords.
    """
    text = text.lower()
    # Normalize slashes and hyphens between words
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Remove excessive symbols but keep letters, numbers, +, #, ., _
    text = re.sub(r'[^\w\s\+\#\.\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_tfidf_similarity(text_a: str, text_b: str) -> float:
    """
    Computes TF-IDF Cosine Similarity using Unigrams and Bigrams with sublinear TF scaling.
    """
    clean_a = clean_text_for_nlp(text_a)
    clean_b = clean_text_for_nlp(text_b)

    if not clean_a or not clean_b:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform([clean_a, clean_b])
        cos_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        # Return percentage rounded to 1 decimal place
        return round(float(np.clip(cos_sim * 100.0, 0.0, 100.0)), 1)
    except Exception:
        return 0.0

def calculate_skill_match(resume_skills: List[str], jd_skills: List[str]) -> Tuple[float, List[str], List[str], List[str]]:
    """
    Calculates overlap between resume skills and JD skills.
    Returns: (score, matched_skills, missing_skills, additional_skills)
    """
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    if not jd_set:
        # If no explicit skills detected in JD, evaluate based on resume's skill breadth
        score = min(len(resume_set) * 10.0, 100.0)
        return round(score, 1), sorted(list(resume_set)), [], []

    matched = sorted(list(resume_set.intersection(jd_set)))
    missing = sorted(list(jd_set - resume_set))
    additional = sorted(list(resume_set - jd_set))

    score = (len(matched) / len(jd_set)) * 100.0
    return round(score, 1), matched, missing, additional

def calculate_experience_score(resume_exp: float, required_exp: float) -> float:
    """
    Calculates experience alignment score.
    """
    if required_exp <= 0:
        return 100.0
    if resume_exp >= required_exp:
        return 100.0
    ratio = resume_exp / required_exp
    score = max(ratio * 100.0, 20.0 if resume_exp > 0 else 10.0)
    return round(min(score, 100.0), 1)

def calculate_education_score(resume_edu: str, required_edu: str) -> float:
    """
    Compares candidate education tier against JD requirement.
    """
    if not required_edu or required_edu == "Not Specified":
        return 100.0

    res_rank = TIER_RANKS.get(resume_edu, 1)
    req_rank = TIER_RANKS.get(required_edu, 1)

    if res_rank >= req_rank:
        return 100.0
    elif res_rank == req_rank - 1:
        return 75.0
    else:
        return 50.0

def compute_composite_score(
    skill_score: float,
    semantic_score: float,
    exp_score: float,
    edu_score: float
) -> Tuple[float, str, str, ScoreBreakdown]:
    """
    Computes overall weighted composite score and determines verdict badge.
    """
    composite = (
        (skill_score * WEIGHT_SKILLS) +
        (semantic_score * WEIGHT_SEMANTIC) +
        (exp_score * WEIGHT_EXPERIENCE) +
        (edu_score * WEIGHT_EDUCATION)
    )
    final_score = round(composite, 1)

    if final_score >= 80.0:
        verdict = "Strong Fit"
        badge = "success"
    elif final_score >= 65.0:
        verdict = "Moderate Fit"
        badge = "info"
    elif final_score >= 50.0:
        verdict = "Potential Fit"
        badge = "warning"
    else:
        verdict = "Low Match"
        badge = "danger"

    breakdown = ScoreBreakdown(
        skill_score=skill_score,
        semantic_score=semantic_score,
        experience_score=exp_score,
        education_score=edu_score,
        weights_applied={
            "skills": WEIGHT_SKILLS,
            "semantic_similarity": WEIGHT_SEMANTIC,
            "experience": WEIGHT_EXPERIENCE,
            "education": WEIGHT_EDUCATION
        }
    )

    return final_score, verdict, badge, breakdown
