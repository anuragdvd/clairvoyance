from enum import Enum
from typing import Optional

class TTSProvider(Enum):
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"

def decode_tts_provider(provider: Optional[str]) -> TTSProvider:
    """Decode TTS provider string to enum."""
    if not provider:
        return TTSProvider.GOOGLE
    
    provider_lower = provider.lower()
    if provider_lower == "elevenlabs":
        return TTSProvider.ELEVENLABS
    elif provider_lower == "google":
        return TTSProvider.GOOGLE
    else:
        return TTSProvider.GOOGLE  # Default fallback