import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the .env file in the backend root directory (one level up from app/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load variables from .env if present
load_dotenv(dotenv_path=ENV_PATH)

# Database settings
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/insightiq",
)

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# CORS allowed frontend origins
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
