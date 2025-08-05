from pydantic import BaseModel
from typing import Optional
from enum import Enum

class TTSProvider(str, Enum):
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"

class VoiceConnectRequest(BaseModel):
    """Request model for creating a voice session."""
    user_name: Optional[str] = None
    tts_provider: Optional[TTSProvider] = TTSProvider.GOOGLE
    voice_name: Optional[str] = None
    session_timeout: Optional[int] = 1800  # 30 minutes default

class VoiceSessionResponse(BaseModel):
    """Response model for voice session creation."""
    room_url: str
    token: str
    session_id: str