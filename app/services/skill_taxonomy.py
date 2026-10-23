import re
from typing import Dict, List, Set, Tuple

# Comprehensive taxonomy categorized by domain
SKILL_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    "Data Science & Machine Learning": {
        "Machine Learning": ["ml", "machine learning", "supervised learning", "unsupervised learning", "reinforcement learning"],
        "Deep Learning": ["dl", "deep learning", "neural networks", "cnn", "rnn", "lstm", "transformers"],
        "Natural Language Processing": ["nlp", "natural language processing", "text mining", "spacy", "nltk", "huggingface", "bert", "tokenization"],
        "Computer Vision": ["computer vision", "cv", "opencv", "image processing", "yolo", "object detection"],
        "Large Language Models": ["llm", "llms", "large language models", "prompt engineering", "langchain", "llamaindex", "rag", "retrieval augmented generation", "fine-tuning"],
        "Scikit-Learn": ["scikit-learn", "sklearn", "scikitlearn"],
        "TensorFlow": ["tensorflow", "tf", "keras"],
        "PyTorch": ["pytorch", "torch"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "Exploratory Data Analysis": ["eda", "exploratory data analysis", "data preprocessing", "feature engineering", "data cleaning"],
        "Data Visualization": ["matplotlib", "seaborn", "plotly", "tableau", "power bi", "powerbi"],
        "Statistical Modeling": ["statistics", "statistical modeling", "hypothesis testing", "a/b testing", "regression", "time series"],
        "MLOps": ["mlops", "model deployment", "mlflow", "dvc", "wandb", "weights & biases", "bentoml", "triton"]
    },
    "Programming Languages": {
        "Python": ["python", "python3", "py"],
        "R": ["r programming", "r-project"],
        "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite", "pl/sql", "t-sql", "mariadb"],
        "JavaScript": ["javascript", "js", "ecmascript"],
        "TypeScript": ["typescript", "ts"],
        "Java": ["java", "core java", "j2ee"],
        "C++": ["c++", "cpp"],
        "C": ["c programming", "c language"],
        "C#": ["c#", "csharp", ".net"],
        "Go": ["golang", "go language"],
        "Rust": ["rust", "rustlang"],
        "Scala": ["scala"],
        "Bash/Shell": ["bash", "shell scripting", "powershell", "zsh"]
    },
    "Big Data & Databases": {
        "MongoDB": ["mongodb", "mongo", "nosql"],
        "Redis": ["redis"],
        "Apache Spark": ["spark", "pyspark", "apache spark"],
        "Apache Kafka": ["kafka", "apache kafka"],
        "Hadoop": ["hadoop", "hdfs", "mapreduce"],
        "Data Warehousing": ["data warehouse", "snowflake", "bigquery", "redshift"],
        "Elasticsearch": ["elasticsearch", "elastic search", "kibana"],
        "Database Design": ["normalization", "database schema", "indexing", "etl", "data pipeline"]
    },
    "Cloud & DevOps": {
        "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "rds", "sagemaker", "cloudwatch"],
        "Google Cloud Platform": ["gcp", "google cloud", "google cloud platform", "vertex ai", "gcs"],
        "Microsoft Azure": ["azure", "azure ml", "azure devops"],
        "Docker": ["docker", "containerization", "docker-compose"],
        "Kubernetes": ["k8s", "kubernetes"],
        "CI/CD": ["ci/cd", "ci-cd", "github actions", "gitlab ci", "jenkins"],
        "Terraform": ["terraform", "infrastructure as code", "iac"],
        "Linux": ["linux", "ubuntu", "centos", "unix"]
    },
    "Web & API Frameworks": {
        "FastAPI": ["fastapi"],
        "Flask": ["flask"],
        "Django": ["django", "django rest framework", "drf"],
        "React": ["react", "react.js", "reactjs"],
        "Node.js": ["node", "node.js", "nodejs", "express", "express.js"],
        "REST APIs": ["rest api", "restful api", "restful", "api development", "postman", "swagger"],
        "GraphQL": ["graphql"],
        "HTML/CSS": ["html", "html5", "css", "css3", "tailwind", "bootstrap"]
    },
    "Software Engineering & Tools": {
        "Git": ["git", "github", "gitlab", "version control"],
        "Agile/Scrum": ["agile", "scrum", "jira", "sprint planning", "kanban"],
        "Unit Testing": ["pytest", "unittest", "test driven development", "tdd", "unit testing"],
        "Object Oriented Programming": ["oop", "object oriented programming", "design patterns"],
        "Microservices": ["microservices", "distributed systems", "event-driven architecture"],
        "Algorithms & Data Structures": ["data structures", "algorithms", "dsa", "complexity analysis"]
    },
    "Soft Skills & Communication": {
        "Problem Solving": ["problem solving", "analytical thinking", "critical thinking"],
        "Team Leadership": ["leadership", "mentoring", "team lead", "project management"],
        "Cross-functional Collaboration": ["collaboration", "cross-functional", "stakeholder management"],
        "Communication": ["presentation skills", "technical documentation", "client communication", "written communication"]
    }
}

# Build flat reverse mapping: alias -> (Canonical Name, Category)
ALIAS_MAP: Dict[str, Tuple[str, str]] = {}
for category, skills in SKILL_TAXONOMY.items():
    for canonical_name, aliases in skills.items():
        # Map canonical itself
        ALIAS_MAP[canonical_name.lower()] = (canonical_name, category)
        for alias in aliases:
            ALIAS_MAP[alias.lower()] = (canonical_name, category)

# Precompile regex boundaries for accurate extraction
# Match word boundaries but allow symbols like ++, #, .js
SKILL_PATTERNS: List[Tuple[re.Pattern, str, str]] = []
for alias, (canonical, category) in ALIAS_MAP.items():
    # Escape special regex chars except spaces
    escaped = re.escape(alias)
    # If the alias starts/ends with alphanumeric, enforce word boundary
    pattern_str = r'(?<![a-zA-Z0-9_])' + escaped + r'(?![a-zA-Z0-9_])'
    compiled = re.compile(pattern_str, re.IGNORECASE)
    SKILL_PATTERNS.append((compiled, canonical, category))

def extract_skills(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Extracts canonical skills and categorizes them from raw text.
    Handles synonyms and prevents duplicate aliases.
    """
    if not text:
        return [], {}

    found_skills: Set[str] = set()
    category_map: Dict[str, Set[str]] = {}

    for pattern, canonical, category in SKILL_PATTERNS:
        if pattern.search(text):
            found_skills.add(canonical)
            if category not in category_map:
                category_map[category] = set()
            category_map[category].add(canonical)

    sorted_skills = sorted(list(found_skills))
    sorted_category_map = {
        cat: sorted(list(skills))
        for cat, skills in category_map.items()
    }

    return sorted_skills, sorted_category_map
