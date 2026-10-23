import os
from typing import List, Dict, Any, Optional, Tuple
import httpx
from app.config import GEMINI_API_KEY
from app.models.schemas import ATSCheckItem

# Curated domain interview questions bank for local deterministic generation
SKILL_INTERVIEW_MAP = {
    "Machine Learning": [
        "How do you handle severe class imbalance in tabular datasets? Compare SMOTE vs. class weighting.",
        "Explain the bias-variance tradeoff and how L1 vs L2 regularization impacts model weights."
    ],
    "Deep Learning": [
        "Explain the mechanics of self-attention in Transformers versus recurrent architectures (LSTMs).",
        "What strategies do you use to diagnose and fix vanishing or exploding gradients in deep neural networks?"
    ],
    "Natural Language Processing": [
        "How would you build and evaluate a Retrieval-Augmented Generation (RAG) pipeline for domain-specific documents?",
        "Compare subword tokenization (Byte-Pair Encoding, WordPiece) with traditional word tokenization."
    ],
    "Computer Vision": [
        "How does transfer learning with a pre-trained Vision Transformer or ResNet work when training data is limited?",
        "Explain the difference between Object Detection (YOLO/Faster R-CNN) and Semantic Segmentation."
    ],
    "Python": [
        "How does Python's GIL (Global Interpreter Lock) affect multi-threading vs. multi-processing in compute-heavy tasks?",
        "Explain Python generators and memory-efficient streaming of large datasets."
    ],
    "SQL": [
        "How do database indexes (B-Tree vs Hash) improve query execution plans, and what are their write trade-offs?",
        "Write and explain a window function query (e.g. ROW_NUMBER() or DENSE_RANK() OVER partition)."
    ],
    "Docker": [
        "What are multi-stage Docker builds and how do they optimize container image sizes for production ML serving?",
        "How do you configure volume mounts and GPU acceleration flags inside a Docker container?"
    ],
    "AWS": [
        "Describe your architecture for deploying an auto-scaling ML inference endpoint using AWS Lambda/ECS or SageMaker.",
        "How do you manage IAM role least-privilege permissions and S3 bucket security policies in production?"
    ],
    "FastAPI": [
        "How does FastAPI leverage Python type hints and Pydantic for high-throughput request handling?",
        "How would you implement background tasks and rate limiting in a FastAPI microservice?"
    ]
}

def generate_local_recommendations(
    matched_skills: List[str],
    missing_skills: List[str],
    ats_score: float,
    ats_checks: List[ATSCheckItem],
    exp_gap: float
) -> List[str]:
    """
    Produces deterministic, actionable suggestions to increase match rate and ATS score.
    """
    recs: List[str] = []

    # Missing Skills Advice
    if missing_skills:
        top_missing = missing_skills[:5]
        recs.append(
            f"Target Skill Gap: Integrate key required competencies ({', '.join(top_missing)}) into your project descriptions and core skills section."
        )

    # ATS Checks Advice
    for check in ats_checks:
        if check.status in ("WARNING", "FAIL"):
            recs.append(f"ATS Optimization ({check.check}): {check.message}")

    # Experience alignment advice
    if exp_gap > 0:
        recs.append(
            f"Experience Alignment: The role requires approx. {exp_gap} more years of industry experience. Highlight high-impact open-source contributions, research publications, or complex end-to-end capstone projects to offset this delta."
        )

    # General best practice
    if len(recs) < 3:
        recs.append(
            "Impact Framing: Emphasize business outcomes using the STAR method (Situation, Task, Action, Result) with explicit efficiency gains or cost metrics."
        )

    return recs[:6]

def generate_local_interview_questions(matched_skills: List[str], role_title: str) -> List[str]:
    """
    Generates tailored interview questions based on candidate's matched skills.
    """
    questions: List[str] = []
    
    for skill in matched_skills:
        if skill in SKILL_INTERVIEW_MAP:
            questions.extend(SKILL_INTERVIEW_MAP[skill])
            if len(questions) >= 5:
                break

    if len(questions) < 4:
        questions.append(
            f"Walk us through the end-to-end architecture of the most technically challenging project on your resume for a {role_title or 'Data Science'} position."
        )
        questions.append(
            "How do you monitor for data drift and concept drift after deploying an ML model or software service to production?"
        )
        questions.append(
            "Describe a situation where a model or system failed to meet expectations in production. How did you identify the root cause and remediate it?"
        )

    return questions[:6]

def get_ai_enhanced_advisory(
    resume_text: str,
    jd_text: str,
    matched_skills: List[str],
    missing_skills: List[str],
    ats_checks: List[ATSCheckItem],
    exp_gap: float,
    role_title: str
) -> Tuple[List[str], List[str], bool]:
    """
    Attempts to call Gemini API if key is present; otherwise falls back gracefully to local engine.
    """
    local_recs = generate_local_recommendations(matched_skills, missing_skills, 80.0, ats_checks, exp_gap)
    local_questions = generate_local_interview_questions(matched_skills, role_title)

    if not GEMINI_API_KEY:
        return local_recs, local_questions, False

    prompt = f"""
You are an expert technical hiring manager and ATS optimization specialist.
Analyze this resume vs job description summary:
- Target Role: {role_title}
- Matched Skills: {', '.join(matched_skills)}
- Missing Skills: {', '.join(missing_skills)}

Provide:
1. Exactly 4 concise, high-impact recommendations to improve the resume for this position.
2. Exactly 4 rigorous, technical interview questions testing their matched competencies.

Format as:
RECOMMENDATIONS:
- [rec 1]
- [rec 2]
- [rec 3]
- [rec 4]
QUESTIONS:
- [q 1]
- [q 2]
- [q 3]
- [q 4]
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                ai_recs = []
                ai_questions = []
                current_mode = None
                for line in text.splitlines():
                    clean = line.strip()
                    if "RECOMMENDATIONS:" in clean.upper():
                        current_mode = "recs"
                        continue
                    elif "QUESTIONS:" in clean.upper():
                        current_mode = "questions"
                        continue
                    if clean.startswith("-") or clean.startswith("*") or (len(clean) > 2 and clean[0].isdigit() and clean[1] in [".", ")"]):
                        item = clean.lstrip("-*1234567890. )").strip()
                        if current_mode == "recs" and item:
                            ai_recs.append(item)
                        elif current_mode == "questions" and item:
                            ai_questions.append(item)

                if ai_recs and ai_questions:
                    return ai_recs[:5], ai_questions[:5], True
    except Exception:
        pass

    return local_recs, local_questions, False
