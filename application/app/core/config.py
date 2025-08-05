import os
from typing import Optional
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
except ImportError:
    print("python-dotenv not installed, skipping .env file loading")

def get_required_env(var_name: str) -> str:
    """Get a required environment variable or raise ValueError."""
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"{var_name} environment variable is required")
    return value

def get_optional_env(var_name: str, default: str = "") -> str:
    """Get an optional environment variable with default."""
    return os.environ.get(var_name, default)

# Server Configuration
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Daily.co Configuration (Optional - only for Daily.co mode)
DAILY_API_KEY = get_optional_env("DAILY_API_KEY")
DAILY_API_URL = get_optional_env("DAILY_API_URL", "https://api.daily.co/v1")

# Azure OpenAI Configuration (Optional - only for Daily.co mode)
AZURE_OPENAI_API_KEY = get_optional_env("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = get_optional_env("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = get_optional_env("AZURE_OPENAI_MODEL", "gpt-4")

# Google Cloud Configuration (Optional - only for Daily.co mode)
GOOGLE_CREDENTIALS_JSON = get_optional_env("GOOGLE_CREDENTIALS_JSON")

# Gemini Configuration (Required for Gemini Live)
GEMINI_API_KEY = get_required_env("GEMINI_API_KEY") if get_optional_env("GEMINI_API_KEY") else None
GEMINI_MODEL = get_optional_env("GEMINI_MODEL", "gemini-2.0-flash-exp")

# TTS Configuration (Optional - defaults to Google TTS)
ELEVENLABS_API_KEY = get_optional_env("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = get_optional_env("ELEVENLABS_VOICE_ID", "bQQWtYx9EodAqMdkrNAc")
ELEVENLABS_MODEL_ID = get_optional_env("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")

# Voice Activity Detection
VAD_CONFIDENCE = float(get_optional_env("VAD_CONFIDENCE", "0.85"))
VAD_MIN_VOLUME = float(get_optional_env("VAD_MIN_VOLUME", "0.75"))

# Audio Processing
ENABLE_NOISE_REDUCE_FILTER = get_optional_env("ENABLE_NOISE_REDUCE_FILTER", "true").lower() == "true"
SAMPLE_RATE = 16000

# Logging
LOG_LEVEL = get_optional_env("LOG_LEVEL", "DEBUG")

print(f"Configuration loaded for environment: {ENVIRONMENT}")
print(f"Server will run on {HOST}:{PORT}")