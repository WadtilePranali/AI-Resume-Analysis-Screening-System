import time
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from app.config import (
    APP_TITLE, APP_VERSION, APP_DESCRIPTION,
    BASE_DIR, GEMINI_API_KEY, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
)
from app.models.schemas import (
    ExtractedResume, JobDescriptionAnalysis, SingleAnalysisResult,
    BatchScreeningResponse, BatchCandidateItem, ScoreBreakdown
)
from app.services.parser import parse_document, segment_resume_sections
from app.services.extractor import (
    extract_contact_info, extract_education_level,
    extract_experience_years, audit_ats_compatibility
)
from app.services.skill_taxonomy import extract_skills, SKILL_TAXONOMY
from app.services.matcher import (
    calculate_tfidf_similarity, calculate_skill_match,
    calculate_experience_score, calculate_education_score,
    compute_composite_score
)
from app.services.advisor import (
    generate_local_recommendations, generate_local_interview_questions,
    get_ai_enhanced_advisory
)
from app.samples.sample_data import SAMPLE_JOB_DESCRIPTIONS, SAMPLE_RESUMES

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_single_audit(
    resume_text: str,
    jd_text: str,
    filename: str = "Uploaded Resume"
) -> SingleAnalysisResult:
    # 1. Resume extraction
    contact = extract_contact_info(resume_text)
    sections = segment_resume_sections(resume_text)
    res_skills, res_skills_by_cat = extract_skills(resume_text)
    res_exp = extract_experience_years(resume_text)
    res_edu = extract_education_level(resume_text)
    ats_score, ats_checks = audit_ats_compatibility(resume_text, sections, contact)

    extracted_resume = ExtractedResume(
        filename=filename,
        raw_text=resume_text,
        contact=contact,
        sections_detected=list(sections.keys()),
        skills=res_skills,
        skills_by_category=res_skills_by_cat,
        experience_years=res_exp,
        education_level=res_edu,
        word_count=len(resume_text.split()),
        ats_score=ats_score,
        ats_checks=ats_checks
    )

    # 2. Job Description extraction
    jd_skills, jd_skills_by_cat = extract_skills(jd_text)
    jd_exp = extract_experience_years(jd_text)
    jd_edu = extract_education_level(jd_text)
    
    jd_lines = [l.strip() for l in jd_text.splitlines() if l.strip()]
    role_title = jd_lines[0].replace("Job Title:", "").strip() if jd_lines else "Target Role"

    extracted_jd = JobDescriptionAnalysis(
        role_title=role_title,
        raw_text=jd_text,
        required_skills=jd_skills,
        skills_by_category=jd_skills_by_cat,
        required_experience_years=jd_exp,
        min_education=jd_edu
    )

    # 3. Match calculations
    skill_score, matched_skills, missing_skills, additional_skills = calculate_skill_match(res_skills, jd_skills)
    semantic_score = calculate_tfidf_similarity(resume_text, jd_text)
    exp_score = calculate_experience_score(res_exp, jd_exp)
    edu_score = calculate_education_score(res_edu or "Not Specified", jd_edu or "Not Specified")

    composite_score, verdict, badge, breakdown = compute_composite_score(
        skill_score=skill_score,
        semantic_score=semantic_score,
        exp_score=exp_score,
        edu_score=edu_score
    )

    # 4. Actionable Advisory & Questions
    exp_gap = max(0.0, jd_exp - res_exp)
    recs, questions, ai_enhanced = get_ai_enhanced_advisory(
        resume_text=resume_text,
        jd_text=jd_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        ats_checks=ats_checks,
        exp_gap=exp_gap,
        role_title=role_title
    )

    return SingleAnalysisResult(
        overall_match_score=composite_score,
        verdict=verdict,
        verdict_badge=badge,
        score_breakdown=breakdown,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        additional_skills=additional_skills,
        resume_extracted=extracted_resume,
        job_extracted=extracted_jd,
        ats_score=ats_score,
        ats_checks=ats_checks,
        recommendations=recs,
        interview_questions=questions,
        ai_enhanced=ai_enhanced
    )

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "ai_engine": "Gemini 1.5 Flash" if GEMINI_API_KEY else "Local ML & NLP Engine (Offline Mode)",
        "gemini_enabled": bool(GEMINI_API_KEY)
    }

@app.get("/api/samples")
def get_sample_data():
    return {
        "job_descriptions": SAMPLE_JOB_DESCRIPTIONS,
        "resumes": SAMPLE_RESUMES
    }

@app.get("/api/skills/taxonomy")
def get_taxonomy():
    total_skills = sum(len(skills) for skills in SKILL_TAXONOMY.values())
    return {
        "total_skills_tracked": total_skills,
        "categories": SKILL_TAXONOMY
    }

@app.post("/api/analyze/text", response_model=SingleAnalysisResult)
def analyze_text_input(
    resume_text: str = Form(..., min_length=20),
    job_description: str = Form(..., min_length=20)
):
    try:
        return process_single_audit(resume_text, job_description, "Pasted Resume Text")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/analyze/upload", response_model=SingleAnalysisResult)
def analyze_file_upload(
    resume_file: UploadFile = File(...),
    job_description: str = Form(..., min_length=20)
):
    ext = Path(resume_file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Please upload a .pdf, .docx, or .txt file."
        )

    content = resume_file.file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size limit of {MAX_FILE_SIZE_MB}MB."
        )

    try:
        extracted_text = parse_document(content, resume_file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract readable text from '{resume_file.filename}': {str(e)}"
        )

    if len(extracted_text.strip()) < 30:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The document contains insufficient readable text. Check if the PDF is scanned or image-only."
        )

    return process_single_audit(extracted_text, job_description, resume_file.filename)

@app.post("/api/screen-batch", response_model=BatchScreeningResponse)
def screen_batch_resumes(
    job_description: str = Form(..., min_length=20),
    resumes: List[UploadFile] = File(...)
):
    start_time = time.time()
    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one resume file to screen."
        )

    jd_skills, _ = extract_skills(job_description)
    jd_exp = extract_experience_years(job_description)
    jd_edu = extract_education_level(job_description)
    jd_lines = [l.strip() for l in job_description.splitlines() if l.strip()]
    job_title = jd_lines[0].replace("Job Title:", "").strip() if jd_lines else "Target Role"

    candidate_results: List[BatchCandidateItem] = []
    missing_skill_counter: dict = {}
    error_count = 0

    for file in resumes:
        try:
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                error_count += 1
                continue

            content = file.file.read()
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                error_count += 1
                continue

            resume_text = parse_document(content, file.filename)
            if len(resume_text.strip()) < 30:
                error_count += 1
                continue

            contact = extract_contact_info(resume_text)
            sections = segment_resume_sections(resume_text)
            res_skills, _ = extract_skills(resume_text)
            res_exp = extract_experience_years(resume_text)
            res_edu = extract_education_level(resume_text)
            ats_score, _ = audit_ats_compatibility(resume_text, sections, contact)

            skill_score, matched_skills, missing_skills, _ = calculate_skill_match(res_skills, jd_skills)
            semantic_score = calculate_tfidf_similarity(resume_text, job_description)
            exp_score = calculate_experience_score(res_exp, jd_exp)
            edu_score = calculate_education_score(res_edu or "Not Specified", jd_edu or "Not Specified")

            composite_score, verdict, badge, _ = compute_composite_score(
                skill_score=skill_score,
                semantic_score=semantic_score,
                exp_score=exp_score,
                edu_score=edu_score
            )

            for m in missing_skills:
                missing_skill_counter[m] = missing_skill_counter.get(m, 0) + 1

            candidate_results.append(BatchCandidateItem(
                rank=0,
                filename=file.filename,
                candidate_name=contact.name or Path(file.filename).stem.replace("_", " ").title(),
                email=contact.email,
                overall_match_score=composite_score,
                skill_score=skill_score,
                semantic_score=semantic_score,
                experience_years=res_exp,
                matched_skills_count=len(matched_skills),
                missing_skills_count=len(missing_skills),
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                verdict=verdict,
                verdict_badge=badge,
                ats_score=ats_score
            ))
        except Exception:
            error_count += 1

    candidate_results.sort(key=lambda c: c.overall_match_score, reverse=True)
    for i, cand in enumerate(candidate_results, 1):
        cand.rank = i

    top_missing = [
        {"skill": skill, "missing_in_candidates_count": count}
        for skill, count in sorted(missing_skill_counter.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    duration = round(time.time() - start_time, 2)

    return BatchScreeningResponse(
        job_title=job_title,
        total_resumes_processed=len(resumes),
        processed_count=len(candidate_results),
        error_count=error_count,
        candidates=candidate_results,
        top_missing_skills_across_pool=top_missing,
        processing_time_seconds=duration
    )

@app.post("/api/screen-batch/sample", response_model=BatchScreeningResponse)
def screen_batch_sample():
    start_time = time.time()
    jd_info = SAMPLE_JOB_DESCRIPTIONS["data_scientist"]
    job_description = jd_info["text"]

    jd_skills, _ = extract_skills(job_description)
    jd_exp = jd_info["experience_years"]
    jd_edu = jd_info["education"]

    candidate_results: List[BatchCandidateItem] = []
    missing_skill_counter: dict = {}

    for sample_key, res_data in SAMPLE_RESUMES.items():
        resume_text = res_data["text"]
        filename = res_data["filename"]

        contact = extract_contact_info(resume_text)
        sections = segment_resume_sections(resume_text)
        res_skills, _ = extract_skills(resume_text)
        res_exp = extract_experience_years(resume_text)
        res_edu = extract_education_level(resume_text)
        ats_score, _ = audit_ats_compatibility(resume_text, sections, contact)

        skill_score, matched_skills, missing_skills, _ = calculate_skill_match(res_skills, jd_skills)
        semantic_score = calculate_tfidf_similarity(resume_text, job_description)
        exp_score = calculate_experience_score(res_exp, jd_exp)
        edu_score = calculate_education_score(res_edu or "Not Specified", jd_edu or "Not Specified")

        composite_score, verdict, badge, _ = compute_composite_score(
            skill_score=skill_score,
            semantic_score=semantic_score,
            exp_score=exp_score,
            edu_score=edu_score
        )

        for m in missing_skills:
            missing_skill_counter[m] = missing_skill_counter.get(m, 0) + 1

        candidate_results.append(BatchCandidateItem(
            rank=0,
            filename=filename,
            candidate_name=contact.name or filename,
            email=contact.email,
            overall_match_score=composite_score,
            skill_score=skill_score,
            semantic_score=semantic_score,
            experience_years=res_exp,
            matched_skills_count=len(matched_skills),
            missing_skills_count=len(missing_skills),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            verdict=verdict,
            verdict_badge=badge,
            ats_score=ats_score
        ))

    candidate_results.sort(key=lambda c: c.overall_match_score, reverse=True)
    for i, cand in enumerate(candidate_results, 1):
        cand.rank = i

    top_missing = [
        {"skill": skill, "missing_in_candidates_count": count}
        for skill, count in sorted(missing_skill_counter.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    duration = round(time.time() - start_time, 2)

    return BatchScreeningResponse(
        job_title=jd_info["title"],
        total_resumes_processed=len(SAMPLE_RESUMES),
        processed_count=len(candidate_results),
        error_count=0,
        candidates=candidate_results,
        top_missing_skills_across_pool=top_missing,
        processing_time_seconds=duration
    )

# Static files mounting
static_dir = BASE_DIR / "app" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(content={"message": "AI Resume Analysis & Screening System API is active. Access docs at /docs"})
