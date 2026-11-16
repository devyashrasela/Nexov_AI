"""Application configuration loaded from environment variables."""

from datetime import datetime
from zoneinfo import ZoneInfo
import os

from dotenv import load_dotenv

load_dotenv()

CLINIC_TIMEZONE = os.getenv("CLINIC_TIMEZONE", "Asia/Kolkata")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_SSL_CA = os.getenv("DB_SSL_CA", "").strip()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL").strip() or "EXAVITQu4vr4xnSDxMaL"
ELEVENLABS_TTS_MODEL = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_turbo_v2_5").strip() or "eleven_turbo_v2_5"

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower().strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip() or "openai/gpt-oss-20b"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"

# LiteLLM Proxy (optional)
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000/v1").strip()
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-local").strip() or "sk-local"
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "medivoice").strip() or "medivoice"


def clinic_now() -> datetime:
    """Return the current time in the clinic timezone."""
    return datetime.now(ZoneInfo(CLINIC_TIMEZONE))


def database_backend() -> str:
    """Return a safe database label for health checks and logs."""
    return "mysql" if DATABASE_URL else "sqlite"
