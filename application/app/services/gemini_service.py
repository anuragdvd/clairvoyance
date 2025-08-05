"""
Gemini Live service for voice conversation.
Simplified version adapted from original Clairvoyance.
"""
import asyncio
import json
import traceback
from typing import Optional
from google import genai
from google.genai import types

from app.core.logger import logger
from app.core import config

# Simple system instruction for voice assistant
SYSTEM_INSTRUCTION = (
    "You are a helpful voice assistant. You can have natural conversations with users "
    "and help them with various tasks. Keep your responses conversational and concise "
    "since you're speaking to users. Be friendly and helpful."
)

# Initialize GenAI client
genai_client = None

def get_gemini_client():
    """Get or initialize Gemini client."""
    global genai_client
    if not genai_client:
        api_key = getattr(config, 'GEMINI_API_KEY', None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in config")
        genai_client = genai.Client(api_key=api_key)
    return genai_client

def get_live_connect_config():
    """Create Gemini Live configuration."""
    system_instr = types.Content(parts=[types.Part(text=SYSTEM_INSTRUCTION)])
    
    return types.LiveConnectConfig(
        system_instruction=system_instr,
        response_modalities=["AUDIO"],  # Audio responses
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
                prefix_padding_ms=100,
                silence_duration_ms=150,
            ),
            activity_handling="START_OF_ACTIVITY_INTERRUPTS"
        ),
        speech_config=types.SpeechConfig(
            language_code="en-US",
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Aoede"  # You can change this voice
                )
            ),
        ),
        output_audio_transcription={},  # Enable output transcription
        input_audio_transcription={},   # Enable input transcription
        tools=None  # No tools for now, just conversation
    )

async def create_gemini_session():
    """Create a new Gemini Live session."""
    try:
        client = get_gemini_client()
        config = get_live_connect_config()
        
        from app.core.config import GEMINI_MODEL
        model = GEMINI_MODEL
        logger.info(f"Attempting to connect to Gemini model: {model}")
        
        session_cm = client.aio.live.connect(model=model, config=config)
        session = await session_cm.__aenter__()
        
        logger.info(f"✅ Gemini Live session established with model {model}")
        return session, session_cm
        
    except Exception as e:
        logger.error(f"❌ Failed to establish Gemini session: {e}")
        logger.debug(traceback.format_exc())
        raise

async def close_gemini_session(session_cm):
    """Close Gemini Live session."""
    if session_cm:
        logger.info("🔌 Closing Gemini session")
        try:
            await asyncio.wait_for(session_cm.__aexit__(None, None, None), timeout=2.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️ Gemini session cleanup timed out")
        except Exception as e:
            logger.error(f"❌ Error during session cleanup: {e}")
            logger.debug(traceback.format_exc())