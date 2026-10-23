import pytest
from app.services.skill_taxonomy import extract_skills
from app.services.matcher import (
    calculate_tfidf_similarity, calculate_skill_match,
    calculate_experience_score, calculate_education_score,
    compute_composite_score
)

def test_extract_skills():
    text = "Proficient in Python, sklearn, PyTorch, Docker, and AWS EC2. Also familiar with FastAPI."
    skills, categories = extract_skills(text)
    
    assert "Python" in skills
    assert "Scikit-Learn" in skills  # Normalized from sklearn!
    assert "PyTorch" in skills
    assert "Docker" in skills
    assert "AWS" in skills
    assert "FastAPI" in skills

def test_calculate_tfidf_similarity():
    jd = "Looking for an experienced Data Scientist with Machine Learning, Python, and SQL experience to build predictive models and analyze large datasets."
    res_high = "Data Scientist experienced in Machine Learning, Python programming, and SQL databases building predictive models."
    res_low = "Senior Executive Chef specializing in Italian pastry, baking techniques, culinary menu design, and kitchen hospitality."

    sim_high = calculate_tfidf_similarity(res_high, jd)
    sim_low = calculate_tfidf_similarity(res_low, jd)

    assert sim_high > 30.0
    assert sim_low < 10.0

def test_calculate_skill_match():
    res_skills = ["Python", "PyTorch", "SQL", "Docker"]
    jd_skills = ["Python", "PyTorch", "AWS", "Kubernetes"]

    score, matched, missing, additional = calculate_skill_match(res_skills, jd_skills)
    assert score == 50.0
    assert set(matched) == {"Python", "PyTorch"}
    assert set(missing) == {"AWS", "Kubernetes"}
    assert set(additional) == {"SQL", "Docker"}

def test_composite_score():
    score, verdict, badge, breakdown = compute_composite_score(
        skill_score=85.0,
        semantic_score=80.0,
        exp_score=100.0,
        edu_score=100.0
    )
    assert score >= 80.0
    assert verdict == "Strong Fit"
    assert badge == "success"
    assert breakdown.skill_score == 85.0
