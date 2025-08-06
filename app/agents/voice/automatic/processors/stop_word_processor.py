"""
Stop Word Processor for immediate voice interruption
"""

import asyncio
from typing import AsyncIterator

from pipecat.frames.frames import (
    Frame, 
    TranscriptionFrame, 
    InterimTranscriptionFrame,
    BotInterruptionFrame,
    UserStartedSpeakingFrame,
    AudioRawFrame
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.core.logger import logger


class StopWordProcessor(FrameProcessor):
    """
    Processor that detects stop words in user speech and immediately interrupts the bot.
    
    This processor monitors transcription frames and sends interruption signals
    when stop words are detected at the beginning of user speech.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Stop words that trigger immediate interruption
        self.stop_words = {
            "stop", "halt", "cancel", "enough", "quit", 
            "silence", "pause", "wait", "hold on"
        }
        
        # Track if we're currently in a user speech segment
        self.user_speaking = False
        self.last_transcript = ""
        
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> AsyncIterator[Frame]:
        """Process frames and detect stop words for interruption"""
        
        # Track user speaking state
        if isinstance(frame, UserStartedSpeakingFrame):
            self.user_speaking = True
            self.last_transcript = ""
            logger.debug("User started speaking - monitoring for stop words")
        
        # Process transcription frames for stop word detection
        elif isinstance(frame, (TranscriptionFrame, InterimTranscriptionFrame)):
            if self.user_speaking and hasattr(frame, 'text') and frame.text:
                await self._check_for_stop_words(frame.text)
        
        # Reset when user stops speaking
        elif hasattr(frame, '__class__') and "UserStopped" in frame.__class__.__name__:
            self.user_speaking = False
            self.last_transcript = ""
        
        # Always yield the original frame
        yield frame
    
    async def _check_for_stop_words(self, text: str):
        """Check transcript text for stop words and trigger interruption if found"""
        if not text or not self.user_speaking:
            return
            
        text_lower = text.lower().strip()
        
        # Only check if this is new text (avoid duplicate processing)
        if text_lower == self.last_transcript:
            return
            
        self.last_transcript = text_lower
        
        # Check for stop words at the beginning of speech
        words = text_lower.split()
        if not words:
            return
            
        first_word = words[0]
        
        # Immediate interruption for stop words
        if first_word in self.stop_words:
            logger.info(f"🛑 Stop word '{first_word}' detected in: '{text}' - Interrupting bot")
            
            # Send interruption frame to stop current bot speech/processing
            interrupt_frame = BotInterruptionFrame()
            await self.push_frame(interrupt_frame)
            
            # Reset state
            self.user_speaking = False
            return True
            
        # Also check for stop phrases in the middle of speech
        for stop_word in self.stop_words:
            if f" {stop_word} " in f" {text_lower} ":
                logger.info(f"🛑 Stop phrase '{stop_word}' detected in: '{text}' - Interrupting bot")
                
                interrupt_frame = BotInterruptionFrame()
                await self.push_frame(interrupt_frame)
                
                self.user_speaking = False
                return True
        
        return False