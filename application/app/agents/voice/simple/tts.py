from typing import Optional
from pipecat.services.google.tts import GoogleTTSService
from app.core import config
from app.core.logger import logger

def get_tts_service(provider: str = "google", voice_name: Optional[str] = None):
    """Get TTS service based on provider."""
    
    if provider.lower() == "elevenlabs" and config.ELEVENLABS_API_KEY:
        try:
            from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
            
            voice_id = config.ELEVENLABS_VOICE_ID
            if voice_name and voice_name.lower() == "rhea":
                voice_id = config.ELEVENLABS_RHEA_VOICE_ID or config.ELEVENLABS_VOICE_ID
            
            logger.info(f"Using ElevenLabs TTS with voice ID: {voice_id}")
            return ElevenLabsTTSService(
                api_key=config.ELEVENLABS_API_KEY,
                voice_id=voice_id,
                model_id=config.ELEVENLABS_MODEL_ID,
            )
        except ImportError:
            logger.warning("ElevenLabs TTS service not available, falling back to Google TTS")
        except Exception as e:
            logger.error(f"Error initializing ElevenLabs TTS: {e}, falling back to Google TTS")
    
    # Default to Google TTS
    google_voice = "en-US-Neural2-D"  # Default Google voice
    if voice_name:
        # You can add voice name mapping here if needed
        pass
    
    logger.info(f"Using Google TTS with voice: {google_voice}")
    
    # Add explicit parameters to ensure audio generation
    from pipecat.services.google.tts import GoogleTTSService
    
    return GoogleTTSService(
        credentials=config.GOOGLE_CREDENTIALS_JSON,
        voice_name=google_voice,
        sample_rate=16000,  # Explicit sample rate
        audio_encoding="LINEAR16"  # Explicit audio encoding
    )