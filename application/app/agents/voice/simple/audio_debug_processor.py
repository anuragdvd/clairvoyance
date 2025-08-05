"""
Debug processor to monitor audio frames in the pipeline.
"""
from pipecat.frames.frames import Frame, AudioRawFrame, TTSAudioRawFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from app.core.logger import logger
from .server_audio_player import get_server_audio_player

class AudioDebugProcessor(FrameProcessor):
    """Processor to debug audio frames flowing through pipeline."""
    
    def __init__(self, play_on_server: bool = False):
        super().__init__()
        self.audio_frame_count = 0
        self.play_on_server = play_on_server
        self.server_player = get_server_audio_player() if play_on_server else None
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames and log audio frame information."""
        await super().process_frame(frame, direction)
        
        # Debug audio frames
        if isinstance(frame, (AudioRawFrame, TTSAudioRawFrame)):
            self.audio_frame_count += 1
            audio_len = len(frame.audio) if hasattr(frame, 'audio') else 0
            # logger.info(f"🎵 Audio Frame #{self.audio_frame_count}: {type(frame).__name__} - {audio_len} bytes | Direction: {direction}")
            
            # Play TTS audio on server if enabled
            if self.play_on_server and isinstance(frame, TTSAudioRawFrame) and hasattr(frame, 'audio'):
                try:
                    await self.server_player.play_audio_frame(frame.audio)
                    logger.info(f"🔊 Playing TTS audio on server: {audio_len} bytes")
                except Exception as e:
                    logger.error(f"Error playing audio on server: {e}")
        
        # Debug any frame with "audio" in the name
        elif "audio" in type(frame).__name__.lower():
            logger.info(f"🎧 Audio-related Frame: {type(frame).__name__} | Direction: {direction}")