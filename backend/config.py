import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

LLM_MODE = os.getenv("LLM_MODE", "mock")  # mock | gemini | claude
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-flash-latest")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'app.db'}")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

DISCLAIMER = (
    "Este contenido es informativo, no constituye asesoria financiera personalizada "
    "y no garantiza resultados. Verifica siempre con tus propias fuentes antes de decidir."
)
