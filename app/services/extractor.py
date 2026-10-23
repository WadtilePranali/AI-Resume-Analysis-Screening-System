import re
from typing import Dict, List, Optional, Tuple, Any
from app.models.schemas import ContactInfo, ATSCheckItem

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5}')
LINKEDIN_REGEX = re.compile(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', re.IGNORECASE)
GITHUB_REGEX = re.compile(r'github\.com/([a-zA-Z0-9_-]+)', re.IGNORECASE)
URL_REGEX = re.compile(r'https?://[^\s,]+')

EDUCATION_TIERS = [
    ("Doctorate / Ph.D.", [r'\bph\.?d\b', r'\bdoctorate\b', r'\bdoctor of philosophy\b']),
    ("Master's Degree", [r'\bm\.?tech\b', r'\bm\.?s\b', r'\bm\.?sc\b', r'\bmba\b', r'\bmca\b', r'\bmaster(?:[\'\’]s)?(?:\s+of)?\b']),
    ("Bachelor's Degree", [r'\bb\.?tech\b', r'\bb\.?e\b', r'\bb\.?s\b', r'\bb\.?sc\b', r'\bbca\b', r'\bbachelor(?:[\'\’]s)?(?:\s+of)?\b']),
    ("Diploma / Associate", [r'\bdiploma\b', r'\bassociate(?:[\'\’]s)?\b'])
]

ACTION_VERBS = {
    "developed", "engineered", "implemented", "designed", "architected", "built",
    "optimized", "deployed", "spearheaded", "accelerated", "reduced", "increased",
    "automated", "created", "analyzed", "trained", "integrated", "led", "managed",
    "researched", "orchestrated", "transformed", "fine-tuned", "evaluated"
}

def extract_contact_info(text: str) -> ContactInfo:
    """
    Extracts candidate contact details including name heuristics, email, phone, and links.
    """
    contact = ContactInfo()

    # Email
    email_match = EMAIL_REGEX.search(text)
    if email_match:
        contact.email = email_match.group(0).lower()

    # Phone
    phone_candidates = PHONE_REGEX.findall(text)
    for p in phone_candidates:
        clean_p = re.sub(r'[^\d+]', '', p)
        if len(clean_p) >= 10:
            contact.phone = p.strip()
            break

    # LinkedIn
    li_match = LINKEDIN_REGEX.search(text)
    if li_match:
        contact.linkedin = f"https://linkedin.com/in/{li_match.group(1)}"

    # GitHub
    gh_match = GITHUB_REGEX.search(text)
    if gh_match:
        contact.github = f"https://github.com/{gh_match.group(1)}"

    # Candidate Name heuristic from top lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:5]:
        # Skip if contains email, links, or section headings
        if "@" in line or "http" in line or "github" in line or "linkedin" in line:
            continue
        if len(line.split()) in [2, 3, 4] and not re.search(r'\d', line):
            # Clean non-alphabetical chars
            clean_name = re.sub(r'[^a-zA-Z\s\.]', '', line).strip()
            if clean_name and len(clean_name) > 3:
                contact.name = clean_name.title()
                break

    if not contact.name:
        contact.name = "Candidate"

    return contact

def extract_education_level(text: str) -> Optional[str]:
    """
    Detects highest formal education degree mentioned in the resume or JD.
    """
    lower_text = text.lower()
    for tier_name, patterns in EDUCATION_TIERS:
        for pat in patterns:
            if re.search(pat, lower_text):
                return tier_name
    return "Not Specified"

def extract_experience_years(text: str) -> float:
    """
    Calculates estimated years of experience using explicit mentions and date interval heuristics.
    """
    lower_text = text.lower()
    # 1. Explicit mentions (e.g., "5+ years of experience", "3 years experience")
    exp_pattern = re.compile(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|hands-on|industry)', re.IGNORECASE)
    matches = exp_pattern.findall(lower_text)
    if matches:
        try:
            return max(float(m) for m in matches)
        except ValueError:
            pass

    # 2. Date ranges (e.g. 2020 - 2024, 2021 to Present)
    date_range_pattern = re.compile(r'\b(20\d\d|19\d\d)\s*[-–—to]+\s*(20\d\d|present|current|now)\b', re.IGNORECASE)
    date_matches = date_range_pattern.findall(lower_text)
    
    total_months = 0
    current_year = 2026 # Context reference year

    for start_yr_str, end_yr_str in date_matches:
        try:
            start_yr = int(start_yr_str)
            if end_yr_str.lower() in ("present", "current", "now"):
                end_yr = current_year
            else:
                end_yr = int(end_yr_str)
            if 1980 <= start_yr <= current_year and start_yr <= end_yr <= current_year:
                diff = end_yr - start_yr
                # Cap individual intervals to realistic job duration
                if 0 <= diff <= 15:
                    total_months += diff * 12
        except ValueError:
            continue

    if total_months > 0:
        years = round(total_months / 12.0, 1)
        return min(years, 30.0)

    return 0.0

def audit_ats_compatibility(text: str, sections: Dict[str, str], contact: ContactInfo) -> Tuple[float, List[ATSCheckItem]]:
    """
    Evaluates ATS compliance across structure, completeness, readability, action verbs, and contact info.
    Returns an ATS score (0-100) and actionable checklist items.
    """
    checks: List[ATSCheckItem] = []
    score = 100.0

    # Check 1: Contact Details
    if contact.email and contact.phone:
        checks.append(ATSCheckItem(
            check="Contact Information",
            status="PASS",
            impact="High",
            message="Valid email address and phone number found."
        ))
    elif contact.email or contact.phone:
        score -= 10
        checks.append(ATSCheckItem(
            check="Contact Information",
            status="WARNING",
            impact="High",
            message="Only partial contact details found. Ensure both email and phone are clearly visible."
        ))
    else:
        score -= 20
        checks.append(ATSCheckItem(
            check="Contact Information",
            status="FAIL",
            impact="High",
            message="No valid contact email or phone detected in the header."
        ))

    # Check 2: Core Sections Presence
    required_secs = ["experience", "education", "skills"]
    missing_secs = [s for s in required_secs if s not in sections]
    if not missing_secs:
        checks.append(ATSCheckItem(
            check="Standard Section Headers",
            status="PASS",
            impact="High",
            message="All standard sections (Experience, Education, Skills) are present and recognized."
        ))
    else:
        deduction = len(missing_secs) * 10
        score -= deduction
        checks.append(ATSCheckItem(
            check="Standard Section Headers",
            status="WARNING",
            impact="High",
            message=f"Missing standard section headings: {', '.join([s.title() for s in missing_secs])}. ATS scanners rely on these labels."
        ))

    # Check 3: Word Count & Content Length
    word_count = len(text.split())
    if 350 <= word_count <= 1100:
        checks.append(ATSCheckItem(
            check="Resume Length",
            status="PASS",
            impact="Medium",
            message=f"Word count is well-calibrated for ATS ({word_count} words, approx. 1-2 pages)."
        ))
    elif word_count < 350:
        score -= 15
        checks.append(ATSCheckItem(
            check="Resume Length",
            status="WARNING",
            impact="Medium",
            message=f"Resume is brief ({word_count} words). Elaborate on project deliverables, methodologies, and metrics."
        ))
    else:
        score -= 10
        checks.append(ATSCheckItem(
            check="Resume Length",
            status="WARNING",
            impact="Medium",
            message=f"Resume is extensive ({word_count} words). Consider condensing to keep focus on recent, relevant achievements."
        ))

    # Check 4: Action Verbs Density
    lower_text = text.lower()
    words_set = set(re.findall(r'\b[a-zA-Z]{3,}\b', lower_text))
    matched_verbs = words_set.intersection(ACTION_VERBS)
    if len(matched_verbs) >= 6:
        checks.append(ATSCheckItem(
            check="Impactful Action Verbs",
            status="PASS",
            impact="Medium",
            message=f"Strong action verb presence detected ({len(matched_verbs)} distinct strong verbs, e.g., {', '.join(list(matched_verbs)[:4])})."
        ))
    elif len(matched_verbs) >= 3:
        score -= 8
        checks.append(ATSCheckItem(
            check="Impactful Action Verbs",
            status="WARNING",
            impact="Medium",
            message=f"Moderate action verb usage ({len(matched_verbs)} found). Strengthen bullet points using verbs like 'Engineered', 'Optimized', 'Deployed'."
        ))
    else:
        score -= 15
        checks.append(ATSCheckItem(
            check="Impactful Action Verbs",
            status="FAIL",
            impact="Medium",
            message="Few strong action verbs identified. Replace passive phrases with direct impact verbs."
        ))

    # Check 5: Quantifiable Achievements (Percentages, metrics, numbers)
    quant_matches = re.findall(r'\b\d+(?:\.\d+)?%\b|\b\d+\s*(?:x|times|k|m|million|users|candidates|accuracy)\b', lower_text)
    if len(quant_matches) >= 3:
        checks.append(ATSCheckItem(
            check="Quantified Metrics & Results",
            status="PASS",
            impact="Medium",
            message=f"Good usage of quantifiable results and metrics ({len(quant_matches)} metrics found)."
        ))
    else:
        score -= 10
        checks.append(ATSCheckItem(
            check="Quantified Metrics & Results",
            status="WARNING",
            impact="Medium",
            message="Limited numerical achievements detected. Include quantifiable metrics (e.g. 'improved latency by 35%', 'processed 10k+ records')."
        ))

    final_score = max(min(round(score, 1), 100.0), 10.0)
    return final_score, checks
