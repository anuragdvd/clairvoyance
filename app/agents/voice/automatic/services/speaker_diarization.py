"""
Speaker Diarization Service using pyannote.audio

Provides real-time speaker identification and diarization capabilities
for voice locking functionality with Google STT.
"""

import asyncio
import numpy as np
import torch
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Lazy imports for pyannote.audio (heavy dependencies)
try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
    from pyannote.core import Segment
    import torchaudio
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False

from app.core.logger import logger
from app.agents.voice.automatic.processors.audio_buffer_processor import AudioChunk


@dataclass
class SpeakerSegment:
    """Speaker segment with timestamp and confidence"""
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float


@dataclass
class SpeakerProfile:
    """Speaker profile with embedding and metadata"""
    speaker_id: str
    embedding: np.ndarray
    enrollment_audio: Optional[np.ndarray] = None
    confidence_threshold: float = 0.8


class SpeakerDiarizationService:
    """
    Real-time speaker diarization and identification service.
    
    Uses pyannote.audio for speaker segmentation and verification.
    Supports voice enrollment and speaker filtering for voice locking.
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.8,
                 min_segment_duration: float = 0.5,
                 sample_rate: int = 16000):
        self.similarity_threshold = similarity_threshold
        self.min_segment_duration = min_segment_duration
        self.sample_rate = sample_rate
        
        # Speaker models and pipeline
        self.diarization_pipeline = None
        self.speaker_embedding_model = None
        self.enrolled_speakers: Dict[str, SpeakerProfile] = {}
        self.target_speaker_id: Optional[str] = None
        
        # Processing state
        self.is_initialized = False
        self.processing_lock = asyncio.Lock()
        
        logger.info(f"🔊 SpeakerDiarizationService created with threshold={similarity_threshold}")
        logger.info(f"🔊 Service configuration: min_segment={min_segment_duration}s, sample_rate={sample_rate}Hz")
    
    async def initialize(self):
        """Initialize pyannote.audio models (async to avoid blocking)"""
        if not PYANNOTE_AVAILABLE:
            logger.error("pyannote.audio not available. Install with: pip install pyannote.audio")
            raise ImportError("pyannote.audio required for speaker diarization")
        
        try:
            logger.info("🔊 Initializing speaker diarization models...")
            
            # Initialize speaker diarization pipeline
            from app.core import config
            
            logger.info("🔊 Loading pyannote speaker diarization pipeline...")
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                use_auth_token=config.HUGGINGFACE_HUB_TOKEN
            )
            logger.info("✅ Speaker diarization pipeline loaded successfully")
            
            # Initialize speaker embedding model for verification
            logger.info("🔊 Loading speaker embedding model...")
            self.speaker_embedding_model = PretrainedSpeakerEmbedding(
                "speechbrain/spkrec-ecapa-voxceleb",
                device=torch.device("cpu")  # Use CPU for now
            )
            logger.info("✅ Speaker embedding model loaded successfully")
            
            self.is_initialized = True
            logger.info("🎯 Speaker diarization service fully initialized and ready!")
            
        except Exception as e:
            logger.error(f"Failed to initialize speaker diarization: {e}")
            # Fallback: disable diarization but don't crash
            self.is_initialized = False
            raise
    
    async def enroll_speaker(self, 
                           audio_chunk: AudioChunk, 
                           speaker_id: str = "target") -> bool:
        """
        Enroll a target speaker from audio chunk.
        This creates the voice fingerprint for locking.
        """
        if not self.is_initialized:
            logger.warning("Speaker diarization not initialized, cannot enroll speaker")
            return False
        
        async with self.processing_lock:
            try:
                logger.info(f"🎙️ Enrolling speaker '{speaker_id}' from {audio_chunk.duration}s audio")
                logger.info(f"🎙️ Audio data: {len(audio_chunk.audio_data)} samples at {audio_chunk.sample_rate}Hz")
                
                # Convert audio to tensor for pyannote
                audio_tensor = torch.from_numpy(audio_chunk.audio_data.astype(np.float32))
                audio_tensor = audio_tensor / 32768.0  # Normalize from int16 to float32
                
                # Generate speaker embedding
                embedding = self.speaker_embedding_model(audio_tensor.unsqueeze(0))
                embedding_np = embedding.detach().cpu().numpy().flatten()
                
                # Create speaker profile
                profile = SpeakerProfile(
                    speaker_id=speaker_id,
                    embedding=embedding_np,
                    enrollment_audio=audio_chunk.audio_data,
                    confidence_threshold=self.similarity_threshold
                )
                
                # Store enrolled speaker
                self.enrolled_speakers[speaker_id] = profile
                self.target_speaker_id = speaker_id
                
                logger.info(f"✅ Speaker '{speaker_id}' enrolled successfully!")
                logger.info(f"🎙️ Speaker embedding shape: {embedding_np.shape}")
                logger.info(f"🎙️ Confidence threshold: {self.similarity_threshold}")
                return True
                
            except Exception as e:
                logger.error(f"Error enrolling speaker: {e}")
                return False
    
    async def identify_speakers(self, audio_chunk: AudioChunk) -> List[SpeakerSegment]:
        """
        Identify speakers in audio chunk and return segments.
        Returns list of speaker segments with timestamps and confidence.
        """
        if not self.is_initialized:
            return []
        
        async with self.processing_lock:
            try:
                # Convert audio chunk to temporary file for pyannote
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    # Convert numpy array to audio file
                    audio_tensor = torch.from_numpy(audio_chunk.audio_data.astype(np.float32))
                    audio_tensor = audio_tensor / 32768.0  # Normalize
                    audio_tensor = audio_tensor.unsqueeze(0)  # Add channel dimension
                    
                    torchaudio.save(
                        temp_file.name,
                        audio_tensor,
                        sample_rate=audio_chunk.sample_rate
                    )
                
                # Run diarization pipeline
                diarization = self.diarization_pipeline(temp_file.name)
                
                # Convert to speaker segments
                segments = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if turn.duration >= self.min_segment_duration:
                        segment = SpeakerSegment(
                            speaker_id=speaker,
                            start_time=audio_chunk.timestamp + turn.start,
                            end_time=audio_chunk.timestamp + turn.end,
                            confidence=1.0  # pyannote doesn't provide confidence directly
                        )
                        segments.append(segment)
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                logger.info(f"🔊 Identified {len(segments)} speaker segments in {audio_chunk.duration}s audio")
                for segment in segments:
                    logger.info(f"🔊 Segment: speaker={segment.speaker_id}, time={segment.start_time:.2f}-{segment.end_time:.2f}s")
                return segments
                
            except Exception as e:
                logger.error(f"Error identifying speakers: {e}")
                return []
    
    async def is_target_speaker(self, audio_chunk: AudioChunk) -> Tuple[bool, float]:
        """
        Check if audio chunk contains the target speaker.
        Returns (is_target, confidence_score)
        """
        if not self.is_initialized or not self.target_speaker_id:
            return True, 1.0  # Default to allowing audio if no enrollment
        
        target_profile = self.enrolled_speakers.get(self.target_speaker_id)
        if not target_profile:
            return True, 1.0
        
        try:
            # Generate embedding for current audio
            audio_tensor = torch.from_numpy(audio_chunk.audio_data.astype(np.float32))
            audio_tensor = audio_tensor / 32768.0
            
            current_embedding = self.speaker_embedding_model(audio_tensor.unsqueeze(0))
            current_embedding_np = current_embedding.detach().cpu().numpy().flatten()
            
            # Calculate similarity with target speaker
            similarity = self._cosine_similarity(target_profile.embedding, current_embedding_np)
            
            is_target = similarity >= target_profile.confidence_threshold
            
            logger.info(f"🎯 Speaker similarity check: {similarity:.3f}, is_target: {is_target}")
            if is_target:
                logger.info(f"✅ TARGET SPEAKER DETECTED (confidence: {similarity:.3f})")
            else:
                logger.info(f"🚫 Non-target speaker detected (confidence: {similarity:.3f})")
            return is_target, similarity
            
        except Exception as e:
            logger.error(f"Error checking target speaker: {e}")
            return True, 1.0  # Default to allowing on error
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def get_enrolled_speakers(self) -> List[str]:
        """Get list of enrolled speaker IDs"""
        return list(self.enrolled_speakers.keys())
    
    def clear_enrollment(self):
        """Clear all enrolled speakers"""
        self.enrolled_speakers.clear()
        self.target_speaker_id = None
        logger.info("All speaker enrollments cleared")
    
    def set_target_speaker(self, speaker_id: str) -> bool:
        """Set the target speaker for voice locking"""
        if speaker_id in self.enrolled_speakers:
            self.target_speaker_id = speaker_id
            logger.info(f"Target speaker set to: {speaker_id}")
            return True
        else:
            logger.warning(f"Speaker '{speaker_id}' not enrolled")
            return False
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.clear_enrollment()
        self.is_initialized = False
        logger.info("SpeakerDiarizationService cleanup completed")