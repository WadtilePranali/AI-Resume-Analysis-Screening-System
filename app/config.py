import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Application settings
APP_TITLE = "AI Resume Analysis & Screening System"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Intelligent ATS Resume Screening, Keyword Gap Analysis, and Recruiter Pipeline Ranking"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Optional AI Key (Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# File upload limits
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Scoring weights (must sum to 1.0)
WEIGHT_SKILLS = 0.40
WEIGHT_SEMANTIC = 0.35
WEIGHT_EXPERIENCE = 0.15
WEIGHT_EDUCATION = 0.10
