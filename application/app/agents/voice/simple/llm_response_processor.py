"""
LLM Response Processor for Clean Speech + Separate Visualization Data
"""

import json
import re
import asyncio
from typing import Optional, Tuple, Dict, Any
from pipecat.frames.frames import (
    Frame, 
    LLMFullResponseEndFrame,
    TTSSpeakFrame,
    SystemFrame
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

from .prompts import process_llm_visualization_response
from app.core.logger import logger

class LLMResponseProcessor(FrameProcessor):
    """
    Processes LLM responses to:
    1. Extract visualization JSON data
    2. Clean speech text by removing JSON blocks
    3. Send clean text to TTS
    4. Send visualization data separately to client
    """
    
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self._accumulated_response = ""
        self._processing_response = False
        
    async def start(self, frame: Frame):
        """Start the processor with proper initialization."""
        await super().start(frame)
        
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process LLM response frames to extract and clean data."""
        
        # Call parent process_frame first for proper initialization
        await super().process_frame(frame, direction)
        
        # Only process LLM-related frames, pass through everything else
        from pipecat.frames.frames import LLMTextFrame, LLMFullResponseStartFrame
        
        # Accumulate LLM response text from appropriate frames
        if isinstance(frame, (LLMTextFrame, LLMFullResponseStartFrame)) and hasattr(frame, 'text') and frame.text:
            self._accumulated_response += frame.text
            logger.debug(f"📝 Accumulated LLM text: {len(self._accumulated_response)} chars")
            
            # Don't forward these frames yet - we need to process them first
            return
        
        # Process complete LLM response
        if isinstance(frame, LLMFullResponseEndFrame):
            if self._accumulated_response.strip():
                logger.info(f"🧠 Processing complete LLM response: {len(self._accumulated_response)} chars")
                await self._process_complete_response()
            self._accumulated_response = ""
            return
        
        # For all other frames (audio, system, etc.), just pass them through
        await self.push_frame(frame, direction)
    
    async def _process_complete_response(self):
        """Process the complete LLM response and create clean outputs."""
        
        try:
            logger.info(f"🧠 Processing LLM response: {self._accumulated_response[:100]}...")
            
            # Extract visualization data and clean speech text
            visualization_data, clean_speech = self._extract_and_clean_response(self._accumulated_response)
            
            # Send visualization data to client if present
            if visualization_data:
                logger.info(f"📊 Extracted visualization data with {len(visualization_data.get('visualizations', []))} charts")
                await self._send_visualization_data(visualization_data)
            
            # Send clean speech text to TTS
            if clean_speech.strip():
                logger.info(f"🎤 Sending clean speech to TTS: {clean_speech[:100]}...")
                clean_tts_frame = TTSSpeakFrame(clean_speech)
                await self.push_frame(clean_tts_frame, FrameDirection.DOWNSTREAM)
                
                # Note: Transcript will be captured by TranscriptProcessor from TextFrame
            else:
                logger.warning("No clean speech text found after processing")
                
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            # Fallback: send original response to TTS
            fallback_frame = TTSSpeakFrame(self._accumulated_response)
            await self.push_frame(fallback_frame, FrameDirection.DOWNSTREAM)
    
    def _extract_and_clean_response(self, response: str) -> Tuple[Optional[Dict], str]:
        """
        Extract visualization JSON and return clean speech text.
        
        Returns:
            Tuple of (visualization_data, clean_speech_text)
        """
        
        visualization_data = None
        clean_speech = response
        
        # Method 1: Extract JSON code blocks
        json_block_pattern = r'```json\s*(.*?)\s*```'
        json_matches = re.findall(json_block_pattern, response, re.DOTALL)
        
        if json_matches:
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    if self._is_valid_visualization_data(data):
                        visualization_data = data
                        # Remove the JSON block from speech
                        clean_speech = re.sub(json_block_pattern, '', clean_speech, flags=re.DOTALL)
                        logger.info("✅ Extracted visualization from JSON code block")
                        break
                except json.JSONDecodeError:
                    continue
        
        # Method 2: Extract direct JSON objects if no code blocks found
        if not visualization_data:
            json_object_pattern = r'\{\s*"speechText".*?"visualizations".*?\}'
            json_match = re.search(json_object_pattern, response, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if self._is_valid_visualization_data(data):
                        visualization_data = data
                        # Remove the JSON object from speech
                        clean_speech = response.replace(json_match.group(0), '')
                        logger.info("✅ Extracted visualization from direct JSON")
                except json.JSONDecodeError:
                    pass
        
        # Method 3: Use the speechText from extracted visualization data if available
        if visualization_data and 'speechText' in visualization_data:
            clean_speech = visualization_data['speechText']
            logger.info("✅ Using speechText from visualization data")
        
        # Clean up the speech text
        clean_speech = self._clean_speech_text(clean_speech)
        
        return visualization_data, clean_speech
    
    def _is_valid_visualization_data(self, data: Dict) -> bool:
        """Check if data contains valid visualization structure."""
        return (
            isinstance(data, dict) and
            'visualizations' in data and
            isinstance(data['visualizations'], list) and
            len(data['visualizations']) > 0
        )
    
    def _clean_speech_text(self, text: str) -> str:
        """Clean speech text by removing any remaining JSON artifacts."""
        
        # Remove common JSON artifacts
        text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'\{[^}]*"speechText"[^}]*\}', '', text)
        text = re.sub(r'\{[^}]*"visualizations"[^}]*\}', '', text)
        
        # Remove multiple whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Add natural ending if text seems incomplete
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    async def _send_visualization_data(self, viz_data: Dict):
        """Send visualization data to client via HTTP."""
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8000/api/visualization/{self.session_id}"
                async with session.post(url, json=viz_data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Sent visualization data to client for session {self.session_id}")
                    else:
                        logger.warning(f"Failed to send visualization data: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending visualization data: {e}")
    
    async def _send_transcript(self, clean_text: str):
        """Send clean transcript to client."""
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8000/api/transcript/{self.session_id}"
                transcript_data = {
                    "speaker": "assistant",
                    "message": clean_text
                }
                async with session.post(url, json=transcript_data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Sent clean transcript for session {self.session_id}")
                    else:
                        logger.warning(f"Failed to send transcript: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending transcript: {e}")

class TTSBlocker(FrameProcessor):
    """
    Blocks original LLM text from reaching TTS when LLMResponseProcessor is active.
    This prevents double audio output.
    """
    
    def __init__(self):
        super().__init__()
        self._block_tts = True
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Block TTSSpeakFrame from LLM responses."""
        
        # Block TTSSpeakFrame that come from LLM (not from our processor)
        if isinstance(frame, TTSSpeakFrame) and self._block_tts:
            # Check if this is from our processor (clean text) or raw LLM
            if hasattr(frame, '_from_processor'):
                # This is clean text from our processor, allow it
                await self.push_frame(frame, direction)
            else:
                # This is raw LLM text, block it
                logger.debug("🚫 Blocked raw LLM text from reaching TTS")
                return
        else:
            # Forward all other frames
            await self.push_frame(frame, direction)

# Helper function to create a clean TTSSpeakFrame
def create_clean_tts_frame(text: str) -> TTSSpeakFrame:
    """Create a TTSSpeakFrame marked as processed."""
    frame = TTSSpeakFrame(text)
    frame._from_processor = True  # Mark as processed
    return frame