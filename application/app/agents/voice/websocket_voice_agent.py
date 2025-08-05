"""
WebSocket-based voice agent similar to original Clairvoyance project.
Handles both audio and text through WebSocket connections.
"""
import asyncio
import json
import time
import numpy as np
from typing import Dict, Any, Optional
import tempfile
import os

from fastapi import WebSocket, WebSocketDisconnect
from app.core.logger import logger
from app.core import config

# Import TTS/STT services
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.tts import GoogleTTSService
from pipecat.services.azure.llm import AzureLLMService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.transcriptions.language import Language

from app.agents.voice.simple.tools import initialize_tools
from app.agents.voice.simple.prompts import get_system_prompt

class WebSocketVoiceAgent:
    """WebSocket-based voice agent for real-time audio processing."""
    
    def __init__(self, websocket: WebSocket, user_name: Optional[str] = None):
        self.websocket = websocket
        self.user_name = user_name
        self.is_connected = False
        self.current_speaker = None
        
        # Audio settings
        self.input_sample_rate = 16000
        self.output_sample_rate = 24000
        self.frame_duration = 30  # ms
        
        # Services
        self.stt: Optional[GoogleSTTService] = None
        self.tts: Optional[GoogleTTSService] = None
        self.llm: Optional[AzureLLMService] = None
        self.context: Optional[OpenAILLMContext] = None
        
        # Audio queue for playback
        self.audio_queue = []
        
    async def initialize_services(self):
        """Initialize AI services."""
        try:
            # For now, let's skip the heavy service initialization to test connection
            logger.info("✅ WebSocket voice agent services initialized (simplified)")
            
        except Exception as e:
            logger.error(f"❌ Error initializing services: {e}")
            raise
    
    async def handle_connection(self):
        """Main connection handler."""
        try:
            await self.websocket.accept()
            self.is_connected = True
            logger.info("🔌 WebSocket voice agent connected")
            
            # Initialize services
            await self.initialize_services()
            
            # Send initialization done
            await self.send_message({"type": "initialization_done"})
            
            # Start processing messages
            while self.is_connected:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.websocket.receive(),
                        timeout=30.0
                    )
                    
                    if message["type"] == "websocket.receive":
                        if "bytes" in message:
                            # Audio data
                            await self.handle_audio_data(message["bytes"])
                        elif "text" in message:
                            # Text message
                            await self.handle_text_message(message["text"])
                            
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.send_message({"type": "ping"})
                    
        except WebSocketDisconnect:
            logger.info("🔌 WebSocket disconnected")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            self.is_connected = False
    
    async def handle_audio_data(self, audio_data: bytes):
        """Handle incoming audio data from browser."""
        try:
            # Convert to numpy array (16-bit PCM)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float32 for processing
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Process with STT (simplified - in reality you'd need proper streaming)
            # For now, let's just log the audio reception
            logger.info(f"🎤 Received audio: {len(audio_data)} bytes")
            
            # TODO: Implement proper STT streaming
            # This is where you'd process the audio with Google STT
            
        except Exception as e:
            logger.error(f"❌ Error processing audio: {e}")
    
    async def handle_text_message(self, text_data: str):
        """Handle incoming text messages."""
        try:
            message = json.loads(text_data)
            
            if message["type"] == "ping":
                await self.send_message({"type": "pong"})
                
            elif message["type"] == "user_text":
                # Handle user text input
                await self.process_user_text(message["text"])
                
        except Exception as e:
            logger.error(f"❌ Error handling text message: {e}")
    
    async def process_user_text(self, user_text: str):
        """Process user text input and generate response."""
        try:
            logger.info(f"📝 User: {user_text}")
            
            # Add user message to context
            self.context.add_message({"role": "user", "content": user_text})
            
            # Send transcript
            await self.send_message({
                "type": "input_transcript",
                "text": user_text
            })
            
            # For now, let's use a simple echo response
            # TODO: Implement proper LLM processing
            response = f"I heard you say: {user_text}"
            
            logger.info(f"🤖 Assistant: {response}")
            
            # Send LLM transcript
            await self.send_message({
                "type": "llm_transcript",
                "text": response
            })
            
            # Generate TTS audio
            await self.generate_tts_audio(response)
                
        except Exception as e:
            logger.error(f"❌ Error processing user text: {e}")
    
    async def generate_tts_audio(self, text: str):
        """Generate TTS audio and send to browser."""
        try:
            # For now, let's use a simple TTS call
            # TODO: Implement proper TTS streaming
            logger.info(f"🔊 Would generate TTS for: {text}")
            
            # Placeholder: Send a test audio message
            await self.send_message({
                "type": "audio_transcript", 
                "text": text
            })
                
        except Exception as e:
            logger.error(f"❌ Error generating TTS: {e}")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send JSON message to browser."""
        try:
            if self.is_connected:
                await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
    
    async def send_audio_data(self, audio_data: bytes):
        """Send audio data to browser."""
        try:
            if self.is_connected:
                # Prepend with audio marker byte
                audio_message = b'\x01' + audio_data
                await self.websocket.send_bytes(audio_message)
        except Exception as e:
            logger.error(f"❌ Error sending audio: {e}")

# Global connections
active_connections: Dict[str, WebSocketVoiceAgent] = {}

async def handle_websocket_connection(websocket: WebSocket, token: str):
    """Handle new WebSocket connection like original Clairvoyance."""
    session_id = f"session_{len(active_connections) + 1}_{int(time.time())}"
    
    await websocket.accept()
    logger.info(f"[{session_id}] WebSocket connection established. Token: {token}")
    active_connections[token] = websocket
    
    try:
        # Send initialization done (like original)
        await websocket.send_text(json.dumps({"type": "initialization_done"}))
        logger.info(f"[{session_id}] Sent initialization_done event.")
        
        # Main message loop (simplified version of original)
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=30.0)
                
                if message.get("type") == "websocket.receive":
                    if "text" in message:
                        # Handle text messages
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "ping":
                            await websocket.send_text(json.dumps({"type": "pong"}))
                            logger.debug(f"[{session_id}] Received ping, sent pong")
                            
                        elif data.get("type") == "user_text":
                            # Handle user text input (for testing)
                            user_text = data.get("text", "")
                            logger.info(f"[{session_id}] User text: {user_text}")
                            
                            # Echo response (like we did before)
                            response = f"I heard you say: {user_text}"
                            
                            # Send input transcript
                            await websocket.send_text(json.dumps({
                                "type": "input_transcript", 
                                "text": user_text
                            }))
                            
                            # Send LLM response
                            await websocket.send_text(json.dumps({
                                "type": "llm_transcript", 
                                "text": response
                            }))
                            
                    elif "bytes" in message:
                        # Handle audio data (simplified)
                        audio_data = message["bytes"]
                        logger.info(f"[{session_id}] Received audio: {len(audio_data)} bytes")
                        # TODO: Process audio with STT → LLM → TTS
                        
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        logger.info(f"[{session_id}] WebSocket disconnected")
    except Exception as e:
        logger.error(f"[{session_id}] WebSocket error: {e}")
    finally:
        if token in active_connections:
            del active_connections[token]
        logger.info(f"[{session_id}] WebSocket connection closed")