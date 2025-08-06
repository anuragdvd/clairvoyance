"""
Speaker Filter Processor for Voice Locking

Synchronizes STT transcriptions with speaker diarization results and filters
out transcriptions from non-target speakers for voice locking functionality.
"""

import asyncio
import time
from typing import AsyncIterator, Optional, Dict, List
from dataclasses import dataclass
from collections import deque

from pipecat.frames.frames import (
    Frame, 
    TranscriptionFrame, 
    InterimTranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.core.logger import logger
from app.agents.voice.automatic.services.speaker_diarization import SpeakerDiarizationService, SpeakerSegment
from app.agents.voice.automatic.processors.audio_buffer_processor import AudioBufferProcessor, AudioChunk


@dataclass
class TranscriptionEvent:
    """Transcription event with timing information"""
    text: str
    timestamp: float
    is_interim: bool
    frame: Frame


@dataclass
class SpeakerDecision:
    """Decision about whether to allow transcription"""
    allow: bool
    confidence: float
    speaker_id: Optional[str]
    reason: str


class SpeakerFilterProcessor(FrameProcessor):
    """
    Processor that filters transcriptions based on speaker identification.
    
    This processor:
    1. Receives transcription frames from STT
    2. Correlates them with speaker diarization results using timestamps
    3. Filters out transcriptions from non-target speakers
    4. Maintains synchronization between audio and transcription timing
    """
    
    def __init__(self, 
                 diarization_service: SpeakerDiarizationService,
                 audio_buffer: AudioBufferProcessor,
                 sync_tolerance: float = 1.0,
                 enable_voice_locking: bool = True,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.diarization_service = diarization_service
        self.audio_buffer = audio_buffer
        self.sync_tolerance = sync_tolerance  # seconds
        self.enable_voice_locking = enable_voice_locking
        
        # Transcription timing state
        self.current_speech_start = None
        self.pending_transcriptions = deque(maxlen=20)
        self.speaker_segments: List[SpeakerSegment] = []
        
        # Voice locking state
        self.enrollment_active = False
        self.enrollment_start_time = None
        self.enrollment_duration = 5.0  # seconds
        self.target_speaker_enrolled = False
        
        # Processing lock for thread safety
        self.processing_lock = asyncio.Lock()
        
        logger.info(f"🎤 SpeakerFilterProcessor initialized: voice_locking={enable_voice_locking}, sync_tolerance={sync_tolerance}s")
        logger.info(f"🎤 Enrollment duration: {enrollment_duration}s")
        if enable_voice_locking:
            logger.info("🎤 Voice locking is ENABLED - will filter non-target speakers")
        else:
            logger.info("🎤 Voice locking is DISABLED - all speakers allowed")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> AsyncIterator[Frame]:
        """Process transcription frames and filter based on speaker identification"""
        
        # Handle user speech timing events
        if isinstance(frame, UserStartedSpeakingFrame):
            await self._on_user_started_speaking()
        elif isinstance(frame, UserStoppedSpeakingFrame):
            await self._on_user_stopped_speaking()
        
        # Process transcription frames
        elif isinstance(frame, (TranscriptionFrame, InterimTranscriptionFrame)):
            if self.enable_voice_locking:
                # Apply speaker filtering
                should_allow = await self._should_allow_transcription(frame)
                if should_allow.allow:
                    logger.info(f"✅ ALLOWING transcription: '{frame.text}' (reason: {should_allow.reason}, confidence: {should_allow.confidence:.2f})")
                    yield frame
                else:
                    logger.info(f"🚫 FILTERING transcription: '{frame.text}' (reason: {should_allow.reason}, confidence: {should_allow.confidence:.2f})")
                    # Don't yield the frame - it gets filtered out
                    return
            else:
                # Voice locking disabled, pass through all transcriptions
                logger.debug(f"🎤 Voice locking disabled - allowing: '{frame.text}'")
                yield frame
        else:
            # Pass through all other frames unchanged
            yield frame
    
    async def _on_user_started_speaking(self):
        """Handle user started speaking event"""
        self.current_speech_start = time.time()
        
        logger.info(f"🎤 User started speaking at {time.strftime('%H:%M:%S.%f')[:-3]}")
        
        # Check if we need to start enrollment
        if (self.enable_voice_locking and 
            not self.target_speaker_enrolled and 
            not self.enrollment_active):
            logger.info("🎙️ No speaker enrolled yet - starting enrollment process")
            await self._start_speaker_enrollment()
        elif self.target_speaker_enrolled:
            logger.info("🎯 Target speaker already enrolled - voice locking active")
    
    async def _on_user_stopped_speaking(self):
        """Handle user stopped speaking event"""
        if self.current_speech_start:
            speech_duration = time.time() - self.current_speech_start
            logger.info(f"🎤 User stopped speaking after {speech_duration:.2f}s")
            
            # Check if enrollment should complete
            if self.enrollment_active and speech_duration >= self.enrollment_duration:
                logger.info(f"🎙️ Enrollment duration reached ({speech_duration:.2f}s >= {self.enrollment_duration}s) - completing enrollment")
                await self._complete_speaker_enrollment()
            elif self.enrollment_active:
                logger.info(f"🎙️ Enrollment in progress - need {self.enrollment_duration - speech_duration:.2f}s more")
        
        self.current_speech_start = None
    
    async def _start_speaker_enrollment(self):
        """Start speaker enrollment process"""
        self.enrollment_active = True
        self.enrollment_start_time = time.time()
        
        logger.info("🎙️ ===== STARTING SPEAKER ENROLLMENT =====")
        logger.info(f"🎙️ Please speak continuously for {self.enrollment_duration} seconds")
        logger.info(f"🎙️ Enrollment started at {time.strftime('%H:%M:%S.%f')[:-3]}")
        
        # TODO: Send TTS message to user about enrollment
        # This would require access to TTS service or event system
    
    async def _complete_speaker_enrollment(self):
        """Complete speaker enrollment using buffered audio"""
        logger.info("🎙️ ===== COMPLETING SPEAKER ENROLLMENT =====")
        try:
            # Get audio chunk from the enrollment period
            logger.info("🎙️ Retrieving enrollment audio from buffer...")
            enrollment_chunk = await self._get_enrollment_audio()
            
            if enrollment_chunk:
                logger.info(f"🎙️ Found enrollment audio: {len(enrollment_chunk.audio_data)} samples, {enrollment_chunk.duration}s")
                logger.info("🎙️ Enrolling speaker with diarization service...")
                
                success = await self.diarization_service.enroll_speaker(
                    enrollment_chunk, 
                    speaker_id="target"
                )
                
                if success:
                    self.target_speaker_enrolled = True
                    logger.info("✅ ===== SPEAKER ENROLLMENT COMPLETED SUCCESSFULLY =====")
                    logger.info("🎯 Voice locking is now ACTIVE - only target speaker will be processed")
                else:
                    logger.error("❌ ===== SPEAKER ENROLLMENT FAILED =====")
            else:
                logger.error("❌ No audio available for speaker enrollment")
        
        except Exception as e:
            logger.error(f"❌ Error completing speaker enrollment: {e}")
        
        finally:
            self.enrollment_active = False
            self.enrollment_start_time = None
    
    async def _get_enrollment_audio(self) -> Optional[AudioChunk]:
        """Get audio chunk from enrollment period"""
        if not self.enrollment_start_time:
            return None
        
        # Look for audio chunk that matches enrollment timing
        recent_chunks = self.audio_buffer.get_recent_chunks(count=5)
        
        for chunk in reversed(recent_chunks):  # Start with most recent
            chunk_end_time = chunk.timestamp + chunk.duration
            
            # Check if chunk overlaps with enrollment period
            if (chunk.timestamp <= self.enrollment_start_time <= chunk_end_time or
                self.enrollment_start_time <= chunk.timestamp <= time.time()):
                logger.debug(f"Found enrollment audio chunk: {chunk.duration}s at {chunk.timestamp}")
                return chunk
        
        logger.warning("No suitable audio chunk found for enrollment")
        return None
    
    async def _should_allow_transcription(self, frame: Frame) -> SpeakerDecision:
        """Determine whether to allow transcription based on speaker filtering"""
        
        # During enrollment, allow all transcriptions
        if self.enrollment_active:
            return SpeakerDecision(
                allow=True,
                confidence=1.0,
                speaker_id="enrollment",
                reason="enrollment_phase"
            )
        
        # If no target speaker enrolled yet, allow all transcriptions
        if not self.target_speaker_enrolled:
            return SpeakerDecision(
                allow=True,
                confidence=1.0,
                speaker_id="unknown",
                reason="no_enrollment"
            )
        
        # Try to correlate transcription with speaker data
        current_time = time.time()
        
        # Get recent audio chunk for speaker identification
        audio_chunk = self.audio_buffer.get_chunk_at_timestamp(
            current_time, 
            tolerance=self.sync_tolerance
        )
        
        if not audio_chunk:
            # No audio data available, default to allowing
            return SpeakerDecision(
                allow=True,
                confidence=0.5,
                speaker_id="unknown",
                reason="no_audio_data"
            )
        
        # Check if audio contains target speaker
        try:
            is_target, confidence = await self.diarization_service.is_target_speaker(audio_chunk)
            
            if is_target:
                return SpeakerDecision(
                    allow=True,
                    confidence=confidence,
                    speaker_id="target",
                    reason=f"target_speaker_confidence_{confidence:.2f}"
                )
            else:
                return SpeakerDecision(
                    allow=False,
                    confidence=confidence,
                    speaker_id="other",
                    reason=f"non_target_speaker_confidence_{confidence:.2f}"
                )
        
        except Exception as e:
            logger.error(f"Error checking speaker identity: {e}")
            # Default to allowing on error
            return SpeakerDecision(
                allow=True,
                confidence=0.0,
                speaker_id="error",
                reason="speaker_check_error"
            )
    
    async def enable_voice_locking(self, enable: bool = True):
        """Enable or disable voice locking functionality"""
        async with self.processing_lock:
            self.enable_voice_locking = enable
            if not enable:
                # Reset enrollment state
                self.enrollment_active = False
                self.target_speaker_enrolled = False
                self.diarization_service.clear_enrollment()
            
            logger.info(f"Voice locking {'enabled' if enable else 'disabled'}")
    
    async def reset_enrollment(self):
        """Reset speaker enrollment to start fresh"""
        async with self.processing_lock:
            self.enrollment_active = False
            self.target_speaker_enrolled = False
            self.enrollment_start_time = None
            self.diarization_service.clear_enrollment()
            
            logger.info("Speaker enrollment reset")
    
    def get_status(self) -> Dict:
        """Get current status of speaker filtering"""
        return {
            "voice_locking_enabled": self.enable_voice_locking,
            "enrollment_active": self.enrollment_active,
            "target_speaker_enrolled": self.target_speaker_enrolled,
            "enrolled_speakers": self.diarization_service.get_enrolled_speakers(),
            "current_target": self.diarization_service.target_speaker_id
        }
    
    async def cleanup(self):
        """Cleanup processor resources"""
        await self.reset_enrollment()
        logger.info("SpeakerFilterProcessor cleanup completed")