from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

class ATSCheckItem(BaseModel):
    check: str
    status: str  # "PASS", "WARNING", "FAIL"
    impact: str  # "High", "Medium", "Low"
    message: str

class ExtractedResume(BaseModel):
    filename: Optional[str] = "Uploaded Document"
    raw_text: str
    contact: ContactInfo
    sections_detected: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    skills_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    experience_years: float = 0.0
    education_level: Optional[str] = None
    word_count: int = 0
    ats_score: float = 0.0
    ats_checks: List[ATSCheckItem] = Field(default_factory=list)

class JobDescriptionAnalysis(BaseModel):
    role_title: Optional[str] = "Target Position"
    raw_text: str
    required_skills: List[str] = Field(default_factory=list)
    skills_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    required_experience_years: float = 0.0
    min_education: Optional[str] = None

class ScoreBreakdown(BaseModel):
    skill_score: float = Field(..., description="Skill match coverage score (0-100)")
    semantic_score: float = Field(..., description="TF-IDF Cosine semantic similarity (0-100)")
    experience_score: float = Field(..., description="Experience alignment score (0-100)")
    education_score: float = Field(..., description="Education alignment score (0-100)")
    weights_applied: Dict[str, float]

class SingleAnalysisResult(BaseModel):
    overall_match_score: float
    verdict: str  # "Strong Fit", "Moderate Fit", "Potential Fit", "Low Match"
    verdict_badge: str  # "success", "info", "warning", "danger"
    score_breakdown: ScoreBreakdown
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    resume_extracted: ExtractedResume
    job_extracted: JobDescriptionAnalysis
    ats_score: float
    ats_checks: List[ATSCheckItem]
    recommendations: List[str]
    interview_questions: List[str]
    ai_enhanced: bool = False

class BatchCandidateItem(BaseModel):
    rank: int
    filename: str
    candidate_name: str
    email: Optional[str] = None
    overall_match_score: float
    skill_score: float
    semantic_score: float
    experience_years: float
    matched_skills_count: int
    missing_skills_count: int
    matched_skills: List[str]
    missing_skills: List[str]
    verdict: str
    verdict_badge: str
    ats_score: float

class BatchScreeningResponse(BaseModel):
    job_title: str
    total_resumes_processed: int
    processed_count: int
    error_count: int
    candidates: List[BatchCandidateItem]
    top_missing_skills_across_pool: List[Dict[str, Any]]
    processing_time_seconds: float
