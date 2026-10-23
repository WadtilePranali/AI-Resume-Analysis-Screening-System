import pytest
from app.services.extractor import (
    extract_contact_info, extract_education_level,
    extract_experience_years, audit_ats_compatibility
)

def test_extract_contact_info():
    text = """
    Pranali Wadtile
    pranali.wadtile@example.com
    +91 9876543210
    https://linkedin.com/in/pranali-wadtile
    https://github.com/WadtilePranali
    Experienced Data Scientist
    """
    contact = extract_contact_info(text)
    assert contact.name == "Pranali Wadtile"
    assert contact.email == "pranali.wadtile@example.com"
    assert "9876543210" in contact.phone
    assert "pranali-wadtile" in contact.linkedin
    assert "WadtilePranali" in contact.github

def test_extract_education_level():
    btech_text = "Graduated with B.Tech in Data Science Engineering from Pune University."
    mtech_text = "Completed M.Tech in Artificial Intelligence in 2023."
    phd_text = "Ph.D. in Computer Science with thesis on deep generative models."
    
    assert extract_education_level(btech_text) == "Bachelor's Degree"
    assert extract_education_level(mtech_text) == "Master's Degree"
    assert extract_education_level(phd_text) == "Doctorate / Ph.D."
    assert extract_education_level("No degree mentioned") == "Not Specified"

def test_extract_experience_years():
    explicit_text = "Results-driven engineer with 4.5 years of experience in AI."
    assert extract_experience_years(explicit_text) == 4.5

    date_range_text = "Machine Learning Engineer (2021 - 2024)"
    assert extract_experience_years(date_range_text) == 3.0

def test_audit_ats_compatibility():
    text = """
    Jane Smith | jane@example.com | +91 9876543210
    PROFESSIONAL SUMMARY
    Results-driven Software Engineer with 3 years of experience.
    
    WORK EXPERIENCE
    Software Engineer | TechCorp | 2021 - Present
    - Engineered real-time data pipelines improving throughput by 35%.
    - Deployed machine learning models reducing inference cost by 20%.
    - Optimized database queries in PostgreSQL boosting query speed by 50%.
    - Implemented REST APIs and automated unit test suites with 95% coverage.
    - Led cross-functional team to deliver scalable microservices.
    
    EDUCATION
    Bachelor of Technology in Computer Science | 2017 - 2021
    
    SKILLS
    Python, SQL, Docker, Scikit-Learn, PyTorch, FastAPI, Git, Linux
    """
    contact = extract_contact_info(text)
    sections = {"summary": "...", "experience": "...", "education": "...", "skills": "..."}
    
    score, checks = audit_ats_compatibility(text, sections, contact)
    assert score >= 70.0
    assert any(c.check == "Contact Information" and c.status == "PASS" for c in checks)
    assert any(c.check == "Standard Section Headers" and c.status == "PASS" for c in checks)
