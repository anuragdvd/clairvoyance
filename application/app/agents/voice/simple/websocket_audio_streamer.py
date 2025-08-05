"""
WebSocket Audio Streamer - captures TTS frames and streams them via WebSocket
"""
import aiohttp
import asyncio
from pipecat.frames.frames import AudioRawFrame, TTSAudioRawFrame, StartFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.core.logger import logger


class WebSocketAudioStreamer(FrameProcessor):
    """Captures TTS audio frames and streams them to WebSocket clients via API."""
    
    def __init__(self, session_id: str, base_url: str = "http://localhost:8000"):
        super().__init__()
        self._session_id = session_id
        self._base_url = base_url
        self._audio_url = f"{base_url}/api/audio/{session_id}"
        
    async def process_frame(self, frame, direction: FrameDirection):
        """Process frames and capture TTS audio frames."""
        
        # Look for TTS audio frames going downstream (from TTS to output)
        # Only capture TTS frames, not user audio frames
        if direction == FrameDirection.DOWNSTREAM and isinstance(frame, TTSAudioRawFrame):
            try:
                # Convert audio frame to bytes
                audio_data = frame.audio
                
                # Convert numpy array to bytes if needed
                if hasattr(audio_data, 'tobytes'):
                    audio_bytes = audio_data.tobytes()
                else:
                    audio_bytes = bytes(audio_data)
                
                logger.info(f"🎵 Captured TTS audio frame: {len(audio_bytes)} bytes for session {self._session_id}")
                
                # Send to WebSocket clients via API (non-blocking)
                asyncio.create_task(self._send_audio_async(audio_bytes))
                
            except Exception as e:
                logger.error(f"Error capturing TTS audio frame: {e}")
        
        # Always pass ALL frames through (including UserAudioRawFrame, StartFrame, etc.)
        await self.push_frame(frame, direction)
    
    async def _send_audio_async(self, audio_data: bytes):
        """Send audio data to WebSocket clients via HTTP API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._audio_url,
                    data=audio_data,
                    headers={'Content-Type': 'application/octet-stream'},
                    timeout=aiohttp.ClientTimeout(total=1.0)  # Quick timeout
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ Sent {len(audio_data)} bytes to WebSocket clients")
                    else:
                        logger.warning(f"Audio API returned status {response.status}")
        except asyncio.TimeoutError:
            logger.warning("Audio send timeout - WebSocket clients may be slow")
        except Exception as e:
            logger.error(f"Failed to send audio to WebSocket: {e}")