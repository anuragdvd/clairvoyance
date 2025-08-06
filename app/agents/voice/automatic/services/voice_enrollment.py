"""
Voice Enrollment System for Speaker Identification

Manages speaker enrollment process, voice fingerprinting, and speaker profiles
for the voice locking functionality.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

from app.core.logger import logger
from app.agents.voice.automatic.services.speaker_diarization import SpeakerDiarizationService, SpeakerProfile
from app.agents.voice.automatic.processors.audio_buffer_processor import AudioChunk


@dataclass
class EnrollmentSession:
    """Speaker enrollment session metadata"""
    session_id: str
    speaker_id: str
    start_time: float
    target_duration: float
    status: str  # "active", "completed", "failed"
    audio_chunks: List[AudioChunk]
    quality_score: float = 0.0


@dataclass
class EnrollmentResult:
    """Result of speaker enrollment process"""
    success: bool
    speaker_id: str
    confidence: float
    quality_score: float
    message: str
    embedding_size: int = 0


class VoiceEnrollmentSystem:
    """
    System for managing speaker enrollment and voice fingerprinting.
    
    Handles the complete enrollment workflow:
    1. Initiate enrollment session
    2. Collect and validate audio samples
    3. Generate speaker embeddings
    4. Store speaker profiles
    5. Manage enrollment quality and validation
    """
    
    def __init__(self, 
                 diarization_service: SpeakerDiarizationService,
                 min_enrollment_duration: float = 3.0,
                 max_enrollment_duration: float = 10.0,
                 quality_threshold: float = 0.7):
        self.diarization_service = diarization_service
        self.min_enrollment_duration = min_enrollment_duration
        self.max_enrollment_duration = max_enrollment_duration
        self.quality_threshold = quality_threshold
        
        # Active enrollment sessions
        self.active_sessions: Dict[str, EnrollmentSession] = {}
        
        # Enrollment statistics
        self.enrollment_stats = {
            "total_attempts": 0,
            "successful_enrollments": 0,
            "failed_enrollments": 0,
            "average_quality": 0.0
        }
        
        logger.info(f"VoiceEnrollmentSystem initialized: min_duration={min_enrollment_duration}s, max_duration={max_enrollment_duration}s")
    
    async def start_enrollment(self, 
                             session_id: str,
                             speaker_id: str = "target",
                             duration: float = 5.0) -> bool:
        """
        Start a new speaker enrollment session.
        
        Args:
            session_id: Unique session identifier
            speaker_id: ID for the speaker being enrolled
            duration: Target enrollment duration in seconds
        
        Returns:
            bool: True if enrollment session started successfully
        """
        try:
            # Validate parameters
            if duration < self.min_enrollment_duration:
                duration = self.min_enrollment_duration
            elif duration > self.max_enrollment_duration:
                duration = self.max_enrollment_duration
            
            # Check if session already exists
            if session_id in self.active_sessions:
                logger.warning(f"Enrollment session {session_id} already active")
                return False
            
            # Create new enrollment session
            session = EnrollmentSession(
                session_id=session_id,
                speaker_id=speaker_id,
                start_time=time.time(),
                target_duration=duration,
                status="active",
                audio_chunks=[]
            )
            
            self.active_sessions[session_id] = session
            self.enrollment_stats["total_attempts"] += 1
            
            logger.info(f"🎙️  Started enrollment session {session_id} for speaker '{speaker_id}' ({duration}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error starting enrollment session: {e}")
            return False
    
    async def add_audio_sample(self, 
                             session_id: str, 
                             audio_chunk: AudioChunk) -> bool:
        """
        Add audio sample to active enrollment session.
        
        Args:
            session_id: Session identifier
            audio_chunk: Audio data chunk
        
        Returns:
            bool: True if audio was added successfully
        """
        session = self.active_sessions.get(session_id)
        if not session or session.status != "active":
            logger.warning(f"No active enrollment session found: {session_id}")
            return False
        
        try:
            # Validate audio quality
            quality_score = self._assess_audio_quality(audio_chunk)
            
            if quality_score >= self.quality_threshold:
                session.audio_chunks.append(audio_chunk)
                session.quality_score = max(session.quality_score, quality_score)
                
                logger.debug(f"Added audio sample to session {session_id}: quality={quality_score:.2f}")
                
                # Check if we have enough audio for enrollment
                total_duration = sum(chunk.duration for chunk in session.audio_chunks)
                if total_duration >= session.target_duration:
                    await self._complete_enrollment(session_id)
                
                return True
            else:
                logger.debug(f"Audio sample quality too low: {quality_score:.2f} < {self.quality_threshold}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding audio sample: {e}")
            return False
    
    async def complete_enrollment(self, session_id: str) -> EnrollmentResult:
        """
        Manually complete an enrollment session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            EnrollmentResult: Result of the enrollment process
        """
        return await self._complete_enrollment(session_id)
    
    async def _complete_enrollment(self, session_id: str) -> EnrollmentResult:
        """Internal method to complete enrollment"""
        session = self.active_sessions.get(session_id)
        if not session:
            return EnrollmentResult(
                success=False,
                speaker_id="",
                confidence=0.0,
                quality_score=0.0,
                message=f"Session {session_id} not found"
            )
        
        try:
            # Check if we have sufficient audio
            total_duration = sum(chunk.duration for chunk in session.audio_chunks)
            
            if total_duration < self.min_enrollment_duration:
                session.status = "failed"
                self.enrollment_stats["failed_enrollments"] += 1
                
                return EnrollmentResult(
                    success=False,
                    speaker_id=session.speaker_id,
                    confidence=0.0,
                    quality_score=session.quality_score,
                    message=f"Insufficient audio: {total_duration:.1f}s < {self.min_enrollment_duration}s"
                )
            
            # Combine audio chunks for enrollment
            combined_audio = await self._combine_audio_chunks(session.audio_chunks)
            
            # Perform speaker enrollment
            success = await self.diarization_service.enroll_speaker(
                combined_audio, 
                session.speaker_id
            )
            
            if success:
                session.status = "completed"
                self.enrollment_stats["successful_enrollments"] += 1
                
                # Update average quality
                total_quality = (self.enrollment_stats["average_quality"] * 
                               (self.enrollment_stats["successful_enrollments"] - 1) + 
                               session.quality_score)
                self.enrollment_stats["average_quality"] = total_quality / self.enrollment_stats["successful_enrollments"]
                
                logger.info(f"✅ Enrollment completed for speaker '{session.speaker_id}' in session {session_id}")
                
                return EnrollmentResult(
                    success=True,
                    speaker_id=session.speaker_id,
                    confidence=session.quality_score,
                    quality_score=session.quality_score,
                    message=f"Speaker '{session.speaker_id}' enrolled successfully",
                    embedding_size=len(combined_audio.audio_data)
                )
            else:
                session.status = "failed"
                self.enrollment_stats["failed_enrollments"] += 1
                
                return EnrollmentResult(
                    success=False,
                    speaker_id=session.speaker_id,
                    confidence=0.0,
                    quality_score=session.quality_score,
                    message="Failed to generate speaker embedding"
                )
                
        except Exception as e:
            session.status = "failed"
            self.enrollment_stats["failed_enrollments"] += 1
            
            logger.error(f"Error completing enrollment: {e}")
            return EnrollmentResult(
                success=False,
                speaker_id=session.speaker_id,
                confidence=0.0,
                quality_score=session.quality_score,
                message=f"Enrollment error: {str(e)}"
            )
        
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    async def cancel_enrollment(self, session_id: str) -> bool:
        """
        Cancel an active enrollment session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            bool: True if session was cancelled successfully
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        session.status = "cancelled"
        del self.active_sessions[session_id]
        
        logger.info(f"Enrollment session {session_id} cancelled")
        return True
    
    def _assess_audio_quality(self, audio_chunk: AudioChunk) -> float:
        """
        Assess the quality of audio chunk for enrollment.
        
        Returns quality score between 0.0 and 1.0
        """
        try:
            audio_data = audio_chunk.audio_data
            
            # Calculate basic audio metrics
            rms_energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            max_amplitude = np.max(np.abs(audio_data))
            
            # Normalize to 0-1 range
            energy_score = min(rms_energy / 5000, 1.0)  # Reasonable threshold for 16-bit audio
            amplitude_score = min(max_amplitude / 32767, 1.0)  # Max value for int16
            
            # Check for silence or clipping
            silence_threshold = 100
            clipping_threshold = 30000
            
            if rms_energy < silence_threshold:
                return 0.0  # Too quiet
            
            if max_amplitude > clipping_threshold:
                return 0.5  # Clipped audio
            
            # Combined quality score
            quality_score = (energy_score + amplitude_score) / 2
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error assessing audio quality: {e}")
            return 0.0
    
    async def _combine_audio_chunks(self, chunks: List[AudioChunk]) -> AudioChunk:
        """Combine multiple audio chunks into a single chunk"""
        if not chunks:
            raise ValueError("No audio chunks to combine")
        
        # Concatenate audio data
        combined_audio = np.concatenate([chunk.audio_data for chunk in chunks])
        
        # Calculate combined duration
        total_duration = sum(chunk.duration for chunk in chunks)
        
        # Use first chunk's metadata as base
        first_chunk = chunks[0]
        
        return AudioChunk(
            audio_data=combined_audio,
            timestamp=first_chunk.timestamp,
            duration=total_duration,
            sample_rate=first_chunk.sample_rate
        )
    
    def get_enrollment_status(self, session_id: str) -> Optional[Dict]:
        """Get status of enrollment session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        total_duration = sum(chunk.duration for chunk in session.audio_chunks)
        progress = min(total_duration / session.target_duration, 1.0)
        
        return {
            "session_id": session_id,
            "speaker_id": session.speaker_id,
            "status": session.status,
            "progress": progress,
            "collected_duration": total_duration,
            "target_duration": session.target_duration,
            "quality_score": session.quality_score,
            "samples_count": len(session.audio_chunks)
        }
    
    def get_statistics(self) -> Dict:
        """Get enrollment statistics"""
        success_rate = (
            self.enrollment_stats["successful_enrollments"] / 
            max(self.enrollment_stats["total_attempts"], 1)
        )
        
        return {
            **self.enrollment_stats,
            "success_rate": success_rate,
            "active_sessions": len(self.active_sessions)
        }
    
    async def cleanup(self):
        """Cleanup enrollment system resources"""
        # Cancel all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.cancel_enrollment(session_id)
        
        logger.info("VoiceEnrollmentSystem cleanup completed")