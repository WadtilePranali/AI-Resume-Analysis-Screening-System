import pytest
from app.services.parser import parse_document, segment_resume_sections

def test_parse_txt_document():
    sample_text = "Jane Doe\nSoftware Engineer\nPython, Docker, FastAPI"
    raw_bytes = sample_text.encode("utf-8")
    extracted = parse_document(raw_bytes, "resume.txt")
    assert "Jane Doe" in extracted
    assert "Software Engineer" in extracted

def test_parse_invalid_extension():
    raw_bytes = b"sample content"
    with pytest.raises(ValueError) as exc:
        parse_document(raw_bytes, "resume.exe")
    assert "Unsupported file format" in str(exc.value)

def test_segment_resume_sections():
    resume_content = """John Doe
john.doe@example.com

PROFESSIONAL SUMMARY
Experienced machine learning practitioner with 3 years background.

TECHNICAL SKILLS
Python, PyTorch, Docker, SQL, FastAPI

WORK EXPERIENCE
ML Engineer at TechCorp
Developed computer vision models.

EDUCATION
B.Tech in Computer Science
"""
    sections = segment_resume_sections(resume_content)
    assert "summary" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections
    assert "Python, PyTorch" in sections["skills"]
