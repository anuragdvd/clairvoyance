"""
Gemini Live WebSocket session handler.
Adapted from original Clairvoyance project.
"""
import asyncio
import json
import time
import traceback
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from google.genai import types

from app.core.logger import logger
from app.core.config import SAMPLE_RATE
from app.services.gemini_service import create_gemini_session, close_gemini_session

# Frame size for audio (30ms at 16kHz = 480 samples = 960 bytes for 16-bit PCM)
FRAME_SIZE = 960
PING_INTERVAL = 30  # seconds

active_connections = set()
shutdown_event = asyncio.Event()

async def handle_gemini_websocket_session(websocket: WebSocket):
    """Handle WebSocket session with Gemini Live."""
    session_id = f"gemini_session_{len(active_connections) + 1}_{int(time.time())}"
    token = websocket.query_params.get("token", "testmode")
    
    await websocket.accept()
    logger.info(f"[{session_id}] Gemini WebSocket connection established. Token: {token}")
    active_connections.add(websocket)
    
    last_heartbeat = time.time()
    gemini_session = None
    gemini_session_cm = None
    websocket_active = True
    user_turn_started = False
    model_turn_started = False
    
    async def keepalive():
        """Send periodic pings to keep connection alive."""
        nonlocal last_heartbeat
        while websocket_active and not shutdown_event.is_set():
            try:
                if time.time() - last_heartbeat > PING_INTERVAL:
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                        last_heartbeat = time.time()
                    except Exception:
                        break
                await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"[{session_id}] Keepalive ping failed: {e}")
                break
    
    try:
        # Create Gemini session
        logger.info(f"[{session_id}] Creating Gemini Live session...")
        gemini_session, gemini_session_cm = await create_gemini_session()
        
        # Check for disconnection after session creation
        if websocket.client_state != WebSocketState.CONNECTED:
            logger.warning(f"[{session_id}] Client disconnected during Gemini session creation")
            await close_gemini_session(gemini_session_cm)
            return
        
        logger.info(f"[{session_id}] Gemini session created successfully")
        await websocket.send_text(json.dumps({"type": "initialization_done"}))
        
    except (WebSocketDisconnect, RuntimeError) as e:
        if isinstance(e, RuntimeError) and "close message has been sent" in str(e).lower():
            logger.warning(f"[{session_id}] Attempted to operate on closed websocket during initialization")
        else:
            logger.info(f"[{session_id}] Client disconnected during initialization")
        return
    except Exception as e:
        logger.error(f"[{session_id}] Critical error during session initialization: {e}", exc_info=True)
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps({"type": "error", "message": "Failed to initialize session"}))
        except (WebSocketDisconnect, RuntimeError):
            logger.warning(f"[{session_id}] Client disconnected before error could be sent")
        return
    
    async def receive_from_client():
        """Receive messages from WebSocket client."""
        nonlocal last_heartbeat, websocket_active, user_turn_started
        try:
            while websocket_active and not shutdown_event.is_set():
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                    last_heartbeat = time.time()
                    
                    logger.info(f"[{session_id}] Received message type: {message.get('type')}, keys: {list(message.keys())}")
                    
                    if message.get("type") == "websocket.receive":
                        if "text" in message:
                            # Handle text messages (ping/pong)
                            data = json.loads(message["text"])
                            if data.get("type") == "pong":
                                logger.debug(f"[{session_id}] Received pong")
                                continue
                            elif data.get("type") == "ping":
                                await websocket.send_text(json.dumps({"type": "pong"}))
                                logger.debug(f"[{session_id}] Received ping, sent pong")
                                continue
                        
                        if "bytes" in message:
                            # Handle audio data
                            audio_data = message["bytes"]
                            logger.info(f"[{session_id}] Received audio data: {len(audio_data)} bytes")
                            
                            if len(audio_data) != FRAME_SIZE:
                                logger.warning(f"[{session_id}] Received audio with unexpected size: {len(audio_data)} bytes (expected {FRAME_SIZE})")
                                continue
                            
                            if gemini_session and not shutdown_event.is_set():
                                try:
                                    # Send audio to Gemini Live
                                    await gemini_session.send_realtime_input(
                                        audio=types.Blob(data=audio_data, mime_type=f"audio/pcm;rate={SAMPLE_RATE}")
                                    )
                                    logger.info(f"[{session_id}] ✅ Sent {len(audio_data)} bytes to Gemini")
                                except Exception as e:
                                    logger.error(f"[{session_id}] Error sending audio to Gemini: {e}")
                                    if "closed" in str(e).lower():
                                        websocket_active = False
                                        break
                        
                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    logger.info(f"[{session_id}] WebSocket disconnected in receive_from_client")
                    websocket_active = False
                    break
                except Exception as e:
                    if "disconnect message has been received" in str(e):
                        logger.info(f"[{session_id}] WebSocket disconnect detected")
                        websocket_active = False
                        break
                    else:
                        logger.error(f"[{session_id}] Error processing client message: {e}")
        except Exception as e:
            logger.error(f"[{session_id}] Error in receive_from_client: {e}")
            websocket_active = False
    
    async def forward_from_gemini():
        """Forward responses from Gemini to WebSocket client."""
        nonlocal websocket_active, model_turn_started, user_turn_started
        try:
            while not shutdown_event.is_set() and websocket_active and gemini_session:
                try:
                    async for resp in gemini_session.receive():
                        if not websocket_active or shutdown_event.is_set():
                            break
                        
                        logger.info(f"[{session_id}] 📨 Received response from Gemini: {type(resp)}")
                        
                        try:
                            # Handle automatic VAD events
                            if hasattr(resp, 'server_content') and hasattr(resp.server_content, 'activity_detected'):
                                activity = resp.server_content.activity_detected
                                if activity and not user_turn_started:
                                    logger.info(f"[{session_id}] User speech activity detected")
                                    user_turn_started = True
                                    model_turn_started = False
                                    await websocket.send_text(json.dumps({"type": "turn_start", "role": "user"}))
                            
                            # Handle turn determination
                            if hasattr(resp, 'server_content') and hasattr(resp.server_content, 'model_turn'):
                                if resp.server_content.model_turn and not model_turn_started:
                                    logger.info(f"[{session_id}] Model turn detected")
                                    model_turn_started = True
                                    user_turn_started = False
                                    await websocket.send_text(json.dumps({"type": "turn_start", "role": "model"}))
                            
                            # Handle text content
                            text_content = ""
                            if hasattr(resp, 'parts'):
                                for part in resp.parts:
                                    if hasattr(part, 'text') and part.text:
                                        text_content += part.text
                                if text_content:
                                    logger.info(f"[{session_id}] Gemini text response: {text_content[:50]}...")
                                    await websocket.send_text(json.dumps({
                                        "type": "llm_transcript", 
                                        "text": text_content
                                    }))
                            
                            # Handle input transcription
                            if hasattr(resp, 'server_content') and hasattr(resp.server_content, 'input_transcription'):
                                input_transcription = resp.server_content.input_transcription
                                if hasattr(input_transcription, 'text') and input_transcription.text:
                                    logger.debug(f"[{session_id}] Input transcription: {input_transcription.text[:30]}...")
                                    await websocket.send_text(json.dumps({
                                        "type": "input_transcript", 
                                        "text": input_transcription.text
                                    }))
                                    if not user_turn_started:
                                        user_turn_started = True
                                        model_turn_started = False
                                        await websocket.send_text(json.dumps({"type": "turn_start", "role": "user"}))
                            
                            # Handle output transcription
                            if hasattr(resp, 'server_content') and hasattr(resp.server_content, 'output_transcription'):
                                output_transcription = resp.server_content.output_transcription
                                if hasattr(output_transcription, 'text') and output_transcription.text:
                                    logger.debug(f"[{session_id}] Output transcription: {output_transcription.text[:30]}...")
                                    await websocket.send_text(json.dumps({
                                        "type": "audio_transcript", 
                                        "text": output_transcription.text
                                    }))
                                    if not model_turn_started:
                                        model_turn_started = True
                                        user_turn_started = False
                                        await websocket.send_text(json.dumps({"type": "turn_start", "role": "model"}))
                            
                            # Handle interruption
                            if hasattr(resp, 'server_content') and hasattr(resp.server_content, 'interrupted'):
                                if resp.server_content.interrupted:
                                    logger.info(f"[{session_id}] Model was interrupted by user")
                                    await websocket.send_text(json.dumps({"type": "interrupted"}))
                            
                            # Handle audio content
                            if hasattr(resp, 'parts'):
                                for part in resp.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.mime_type.startswith('audio/'):
                                        audio_data = part.inline_data.data
                                        logger.debug(f"[{session_id}] Sending {len(audio_data)} bytes of audio to client")
                                        await websocket.send_bytes(b"\x01" + audio_data)  # Marker byte for client
                            
                            elif hasattr(resp, 'data') and resp.data:  # Fallback for direct audio
                                logger.debug(f"[{session_id}] Sending {len(resp.data)} bytes of audio (fallback)")
                                await websocket.send_bytes(b"\x01" + resp.data)
                        
                        except WebSocketDisconnect:
                            logger.info(f"[{session_id}] WebSocket disconnected in forward_from_gemini")
                            websocket_active = False
                            break
                        except Exception as e:
                            if "disconnect message has been received" in str(e) or "Connection closed" in str(e):
                                logger.info(f"[{session_id}] WebSocket connection closed: {e}")
                                websocket_active = False
                                break
                            else:
                                logger.error(f"[{session_id}] Error sending response to client: {e}")
                
                except asyncio.CancelledError:
                    logger.info(f"[{session_id}] Forward task cancelled")
                    break
                except Exception as e:
                    if "closed session" in str(e).lower():
                        logger.info(f"[{session_id}] Gemini session closed")
                        break
                    else:
                        logger.error(f"[{session_id}] Error in Gemini response handling: {e}")
                        await asyncio.sleep(0.1)  # Avoid tight loop
        
        except Exception as e:
            logger.error(f"[{session_id}] Error in forward_from_gemini: {e}")
            websocket_active = False
    
    # Run all tasks concurrently
    tasks = []
    try:
        tasks = [
            asyncio.create_task(keepalive()),
            asyncio.create_task(receive_from_client()),
            asyncio.create_task(forward_from_gemini())
        ]
        
        # Wait for first task to complete (usually means error or disconnect)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        
    finally:
        # Ensure all tasks are cancelled
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Clean up Gemini session
        await close_gemini_session(gemini_session_cm)
        
        # Remove from active connections
        if websocket in active_connections:
            active_connections.remove(websocket)
        
        # Close WebSocket if still open
        try:
            if websocket.client_state != WebSocketDisconnect:
                await websocket.close()
        except Exception:
            pass  # Ignore errors during close
        
        logger.info(f"[{session_id}] WebSocket connection closed and resources cleaned up")

# Functions for app lifecycle management
def get_active_connections():
    return active_connections

def get_shutdown_event():
    return shutdown_event