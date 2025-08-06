"""
Audio Buffer Processor for Voice Locking System

Captures and buffers raw audio frames for parallel processing with speaker diarization.
Maintains sliding window buffer for real-time speaker identification.
"""

import asyncio
import time
import numpy as np
from collections import deque
from typing import AsyncIterator, Optional, Callable
from dataclasses import dataclass

from pipecat.frames.frames import Frame, AudioRawFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.core.logger import logger


@dataclass
class AudioChunk:
    """Audio chunk with metadata for speaker diarization"""
    audio_data: np.ndarray
    timestamp: float
    duration: float
    sample_rate: int


class AudioBufferProcessor(FrameProcessor):
    """
    Processor that buffers raw audio frames for speaker diarization processing.
    
    This processor:
    1. Captures raw audio frames before they reach STT
    2. Maintains a sliding window buffer for diarization
    3. Calls speaker diarization service on buffered chunks
    4. Forwards original frames unchanged to maintain pipeline flow
    """
    
    def __init__(self, 
                 chunk_duration: float = 2.0,
                 buffer_size: int = 10,
                 sample_rate: int = 16000,
                 diarization_callback: Optional[Callable] = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.chunk_duration = chunk_duration  # seconds
        self.buffer_size = buffer_size  # number of chunks to keep
        self.sample_rate = sample_rate
        self.diarization_callback = diarization_callback
        
        # Audio buffer for accumulating frames
        self.audio_buffer = []
        self.buffer_start_time = None
        
        # Sliding window of processed chunks
        self.chunk_buffer = deque(maxlen=buffer_size)
        
        # Processing state
        self.bytes_per_chunk = int(sample_rate * chunk_duration * 2)  # 16-bit PCM
        self.processing_task = None
        
        logger.info(f"🎵 AudioBufferProcessor initialized: chunk_duration={chunk_duration}s, buffer_size={buffer_size}")
        logger.info(f"🎵 Audio buffer will process {bytes_per_chunk} bytes per chunk")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> AsyncIterator[Frame]:
        """Process audio frames and buffer for speaker diarization"""
        
        # Only process audio frames from input direction
        if isinstance(frame, AudioRawFrame) and direction == FrameDirection.DOWNSTREAM:
            logger.debug(f"🎵 Processing audio frame: {len(frame.audio) if hasattr(frame, 'audio') else 0} bytes")
            await self._buffer_audio_frame(frame)
        
        # Always yield the original frame to maintain pipeline flow
        yield frame
    
    async def _buffer_audio_frame(self, frame: AudioRawFrame):
        """Buffer audio frame and trigger processing when chunk is ready"""
        try:
            # Initialize buffer start time on first frame
            if self.buffer_start_time is None:
                self.buffer_start_time = time.time()
            
            # Add audio data to buffer
            if hasattr(frame, 'audio') and frame.audio:
                self.audio_buffer.extend(frame.audio)
            
            # Check if we have enough data for a chunk
            if len(self.audio_buffer) >= self.bytes_per_chunk:
                logger.info(f"🎵 Audio chunk ready: {len(self.audio_buffer)} bytes accumulated")
                await self._process_audio_chunk()
                
        except Exception as e:
            logger.error(f"Error buffering audio frame: {e}")
    
    async def _process_audio_chunk(self):
        """Process accumulated audio data as a chunk for speaker diarization"""
        try:
            # Extract chunk from buffer
            chunk_data = self.audio_buffer[:self.bytes_per_chunk]
            self.audio_buffer = self.audio_buffer[self.bytes_per_chunk:]
            
            # Convert bytes to numpy array (16-bit PCM)
            audio_array = np.frombuffer(bytes(chunk_data), dtype=np.int16)
            
            # Create audio chunk metadata
            current_time = time.time()
            chunk = AudioChunk(
                audio_data=audio_array,
                timestamp=self.buffer_start_time,
                duration=self.chunk_duration,
                sample_rate=self.sample_rate
            )
            
            # Add to sliding window buffer
            self.chunk_buffer.append(chunk)
            
            # Update buffer start time for next chunk
            self.buffer_start_time = current_time
            
            # Trigger speaker diarization processing (non-blocking)
            if self.diarization_callback:
                asyncio.create_task(self._call_diarization_service(chunk))
            
            logger.info(f"🎵 Audio chunk processed: {len(audio_array)} samples, {self.chunk_duration}s duration")
            logger.info(f"🎵 Buffer now contains {len(self.chunk_buffer)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    async def _call_diarization_service(self, chunk: AudioChunk):
        """Call speaker diarization service on audio chunk (non-blocking)"""
        try:
            if self.diarization_callback:
                logger.info(f"🎵 Calling speaker diarization for chunk at {chunk.timestamp}")
                await self.diarization_callback(chunk)
                logger.info(f"🎵 Speaker diarization completed for chunk")
        except Exception as e:
            logger.error(f"❌ Error in diarization callback: {e}")
    
    def get_recent_chunks(self, count: int = None) -> list[AudioChunk]:
        """Get recent audio chunks from buffer"""
        if count is None:
            return list(self.chunk_buffer)
        return list(self.chunk_buffer)[-count:]
    
    def get_chunk_at_timestamp(self, timestamp: float, tolerance: float = 0.5) -> Optional[AudioChunk]:
        """Find audio chunk that contains the given timestamp"""
        for chunk in self.chunk_buffer:
            if abs(chunk.timestamp - timestamp) <= tolerance:
                return chunk
        return None
    
    def clear_buffer(self):
        """Clear all buffered audio data"""
        self.audio_buffer.clear()
        self.chunk_buffer.clear()
        self.buffer_start_time = None
        logger.debug("Audio buffer cleared")
    
    async def cleanup(self):
        """Cleanup processor resources"""
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        self.clear_buffer()
        logger.info("AudioBufferProcessor cleanup completed")