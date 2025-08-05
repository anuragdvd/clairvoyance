"""
Server-side audio player to play TTS audio frames directly on server speakers.
"""
import asyncio
import wave
import tempfile
import os
import subprocess
from typing import Optional
from app.core.logger import logger

class ServerAudioPlayer:
    """Play audio frames directly on the server speakers using system audio."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.audio_queue = []
        self.is_playing = False
        
    async def play_audio_frame(self, audio_data: bytes):
        """Play a single audio frame using system audio player."""
        try:
            # Create temporary wav file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Convert raw audio to wav
            self._write_wav_file(temp_path, audio_data)
            
            # Play using system audio player
            await self._play_audio_file(temp_path)
            
            # Cleanup
            os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Error playing audio frame: {e}")
    
    def _write_wav_file(self, filepath: str, audio_data: bytes):
        """Write raw audio data to a WAV file."""
        try:
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
        except Exception as e:
            logger.error(f"Error writing WAV file: {e}")
            raise
    
    async def _play_audio_file(self, filepath: str):
        """Play audio file using system audio player."""
        try:
            # Use afplay on macOS for direct audio playback
            if subprocess.run(['which', 'afplay'], capture_output=True).returncode == 0:
                # macOS - afplay is available
                process = await asyncio.create_subprocess_exec(
                    'afplay', filepath,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                logger.info(f"🔊 Played audio via afplay: {os.path.basename(filepath)}")
                
            elif subprocess.run(['which', 'aplay'], capture_output=True).returncode == 0:
                # Linux ALSA
                process = await asyncio.create_subprocess_exec(
                    'aplay', filepath,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                logger.info(f"🔊 Played audio via aplay: {os.path.basename(filepath)}")
                
            elif subprocess.run(['which', 'paplay'], capture_output=True).returncode == 0:
                # Linux PulseAudio
                process = await asyncio.create_subprocess_exec(
                    'paplay', filepath,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                logger.info(f"🔊 Played audio via paplay: {os.path.basename(filepath)}")
                
            else:
                logger.warning("No suitable audio player found (afplay, aplay, paplay)")
                
        except Exception as e:
            logger.error(f"Error playing audio file: {e}")
    
    def stop(self):
        """Stop current audio playback."""
        # For system audio players, we can't easily stop them
        # But they're short-lived anyway
        pass

# Global audio player instance
server_audio_player: Optional[ServerAudioPlayer] = None

def get_server_audio_player() -> ServerAudioPlayer:
    """Get or create the server audio player."""
    global server_audio_player
    if not server_audio_player:
        server_audio_player = ServerAudioPlayer()
    return server_audio_player