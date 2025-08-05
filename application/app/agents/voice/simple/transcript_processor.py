"""
Frame processor to capture and send transcript messages.
"""
import asyncio
from typing import Any, Awaitable

from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    TextFrame
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from app.transcript_client import TranscriptClient

class TranscriptProcessor(FrameProcessor):
    """Processor to capture transcript events and send them to the server."""
    
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self.transcript_client = TranscriptClient(session_id)
    
    async def start(self):
        """Start the transcript client."""
        await self.transcript_client.start()
    
    async def stop(self):
        """Stop the transcript client."""
        await self.transcript_client.stop()
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames and extract transcript information."""
        await super().process_frame(frame, direction)
        
        # Debug: Log all frame types
        frame_type = type(frame).__name__
        print(f"🔍 Frame: {frame_type} | Direction: {direction}")
        
        try:
            # Capture user speech (transcription)
            if isinstance(frame, TranscriptionFrame):
                print(f"🎯 Found TranscriptionFrame: {frame}")
                if hasattr(frame, 'text') and frame.text and frame.text.strip():
                    user_text = frame.text.strip()
                    await self.transcript_client.send_message("user", user_text)
                    print(f"📝 User: {user_text}")
                else:
                    print(f"⚠️ TranscriptionFrame has no text: {frame}")
            
            # Capture bot speech (TTS text)
            elif isinstance(frame, TextFrame):
                print(f"🎯 Found TextFrame: {frame}")
                if hasattr(frame, 'text') and frame.text and frame.text.strip():
                    bot_text = frame.text.strip()
                    await self.transcript_client.send_message("assistant", bot_text)
                    print(f"📝 Bot: {bot_text}")
                else:
                    print(f"⚠️ TextFrame has no text: {frame}")
                    
        except Exception as e:
            print(f"❌ Transcript error: {e}")