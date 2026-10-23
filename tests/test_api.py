import pytest
from app.main import (
    health_check, get_sample_data, get_taxonomy,
    process_single_audit, screen_batch_sample
)

def test_api_health():
    data = health_check()
    assert data["status"] == "online"
    assert "version" in data
    assert "app" in data

def test_api_samples():
    data = get_sample_data()
    assert "data_scientist" in data["job_descriptions"]
    assert "strong_candidate" in data["resumes"]

def test_api_skills_taxonomy():
    data = get_taxonomy()
    assert data["total_skills_tracked"] > 30
    assert "Data Science & Machine Learning" in data["categories"]

def test_process_single_audit():
    jd = """Job Title: Data Scientist
    Required Skills: Python, Scikit-Learn, PyTorch, SQL, Docker.
    2 years experience required. Bachelor's degree required."""

    resume = """Candidate Name: John Doe
    Email: john.doe@example.com | Phone: +91 9876543210
    WORK EXPERIENCE
    2 years experience building ML models using Python, Scikit-Learn, and SQL.
    EDUCATION
    Bachelor of Technology in Computer Science
    SKILLS
    Python, Scikit-Learn, SQL, PyTorch"""

    result = process_single_audit(resume, jd, "Candidate_Resume.txt")
    assert result.overall_match_score > 60.0
    assert "Python" in result.matched_skills
    assert len(result.recommendations) > 0
    assert result.ats_score > 50.0

def test_screen_batch_sample():
    data = screen_batch_sample()
    assert data.processed_count == 3
    assert len(data.candidates) == 3
    assert data.candidates[0].rank == 1
    assert data.candidates[0].overall_match_score >= data.candidates[1].overall_match_score
