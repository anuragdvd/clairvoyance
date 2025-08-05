import uvicorn
import subprocess
import uuid
import time
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

import aiohttp
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pipecat.transports.services.helpers.daily_rest import (
    DailyRESTHelper, 
    DailyRoomParams, 
    DailyRoomProperties
)

from app.core.logger import logger
from app.core.config import DAILY_API_KEY, DAILY_API_URL, PORT, HOST
from app import __version__
from app.schemas import VoiceConnectRequest, VoiceSessionResponse
from app.ws.gemini_live_session import handle_gemini_websocket_session

# Dictionary to track bot processes: {pid: (process, room_url)}
bot_processes = {}

# Store Daily API helpers
daily_helpers = {}

# WebSocket connections for transcript streaming: {session_id: [websockets]}
transcript_connections = {}

# WebSocket connections for audio streaming: {session_id: [websockets]}
audio_connections = {}

# WebSocket connections for visualization streaming: {session_id: [websockets]}
visualization_connections = {}

class TranscriptManager:
    """Manages WebSocket connections for transcript streaming."""
    
    @staticmethod
    def add_connection(session_id: str, websocket: WebSocket):
        """Add a WebSocket connection for a session."""
        if session_id not in transcript_connections:
            transcript_connections[session_id] = []
        transcript_connections[session_id].append(websocket)
        logger.info(f"Added transcript connection for session {session_id}")
    
    @staticmethod
    def remove_connection(session_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if session_id in transcript_connections:
            if websocket in transcript_connections[session_id]:
                transcript_connections[session_id].remove(websocket)
            if not transcript_connections[session_id]:
                del transcript_connections[session_id]
        logger.info(f"Removed transcript connection for session {session_id}")
    
    @staticmethod
    async def broadcast_message(session_id: str, speaker: str, message: str):
        """Broadcast a transcript message to all connected clients for a session."""
        if session_id in transcript_connections:
            dead_connections = []
            for websocket in transcript_connections[session_id]:
                try:
                    await websocket.send_json({
                        "type": "transcript",
                        "speaker": speaker,
                        "message": message,
                        "timestamp": time.time()
                    })
                except:
                    dead_connections.append(websocket)
            
            # Remove dead connections
            for dead_ws in dead_connections:
                TranscriptManager.remove_connection(session_id, dead_ws)

class AudioStreamManager:
    """Manages WebSocket connections for audio streaming."""
    
    @staticmethod
    async def send_audio(session_id: str, audio_data: bytes):
        """Send audio data to all connected audio WebSocket clients for a session."""
        if session_id in audio_connections:
            dead_connections = []
            for websocket in audio_connections[session_id]:
                try:
                    await websocket.send_bytes(audio_data)
                    logger.debug(f"🔊 Sent {len(audio_data)} bytes to audio WebSocket for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to send audio to WebSocket: {e}")
                    dead_connections.append(websocket)
            
            # Remove dead connections
            for dead_ws in dead_connections:
                if session_id in audio_connections and dead_ws in audio_connections[session_id]:
                    audio_connections[session_id].remove(dead_ws)

class VisualizationStreamManager:
    """Manages WebSocket connections for visualization streaming."""
    
    @staticmethod
    async def send_visualization(session_id: str, viz_data: dict):
        """Send visualization data to all connected visualization WebSocket clients for a session."""
        if session_id in visualization_connections:
            dead_connections = []
            for websocket in visualization_connections[session_id]:
                try:
                    await websocket.send_json({
                        "type": "visualization",
                        "data": viz_data,
                        "timestamp": time.time()
                    })
                    logger.debug(f"📊 Sent visualization data to WebSocket for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to send visualization to WebSocket: {e}")
                    dead_connections.append(websocket)
            
            # Remove dead connections
            for dead_ws in dead_connections:
                if session_id in visualization_connections and dead_ws in visualization_connections[session_id]:
                    visualization_connections[session_id].remove(dead_ws)

def cleanup():
    """Cleanup function to terminate all bot processes."""
    logger.info(f"Attempting to terminate {len(bot_processes)} bot processes.")
    for pid, (proc, room_url) in list(bot_processes.items()):
        try:
            if proc.poll() is None:
                logger.info(f"Terminating process {pid} for room {room_url}...")
                proc.terminate()
                proc.wait()
                logger.info(f"Process {pid} terminated successfully.")
            else:
                logger.info(f"Process {pid} for room {room_url} has already terminated.")
        except Exception as e:
            logger.error(f"Error terminating process {pid}: {e}")
        finally:
            bot_processes.pop(pid, None)
    logger.info("All bot processes have been handled.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager that handles startup and shutdown tasks."""
    logger.info("Application startup...")
    
    # Initialize aiohttp session only if Daily.co is configured
    aiohttp_session = None
    if DAILY_API_KEY and DAILY_API_KEY.strip():
        aiohttp_session = aiohttp.ClientSession()
        daily_helpers["rest"] = DailyRESTHelper(
            daily_api_key=DAILY_API_KEY,
            daily_api_url=DAILY_API_URL,
            aiohttp_session=aiohttp_session,
        )
        logger.info("Daily REST helper initialized.")
    else:
        logger.info("Running in Gemini Live mode only")
    
    yield
    
    logger.info("Application shutdown event triggered...")
    # Cleanup bot processes
    cleanup()
    # Close aiohttp session if it exists
    if aiohttp_session:
        await aiohttp_session.close()
    logger.info("Application shutdown complete.")

# Create FastAPI app
app = FastAPI(
    title="Simple Voice Agent",
    version=__version__,
    description="A simple voice agent with STT, LLM, and TTS capabilities",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount React app build directory  
app.mount("/react", StaticFiles(directory="static/voice-chat/build", html=True), name="react")

@app.post("/voice/connect", response_model=VoiceSessionResponse)
async def create_voice_session(request: VoiceConnectRequest) -> VoiceSessionResponse:
    """Create a new voice session."""
    logger.info(f"Received voice session request: {request.model_dump()}")
    
    try:
        # Create Daily.co room
        MAX_DURATION = request.session_timeout or 1800  # 30 minutes default
        room = await daily_helpers["rest"].create_room(
            params=DailyRoomParams(
                properties=DailyRoomProperties(
                    exp=time.time() + MAX_DURATION,
                    eject_at_room_exp=True,
                )
            )
        )

        # Create room token
        token = await daily_helpers["rest"].get_token(
            room.url,
            expiry_time=MAX_DURATION,
            owner=True,
        )

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Generated session ID: {session_id}")

        # Build command to launch voice agent subprocess
        bot_file = "app.agents.voice.simple"
        cmd = [
            "python3", "-m", bot_file,
            "-u", room.url,
            "-t", token,
            "--session-id", session_id,
        ]

        # Add optional parameters
        if request.user_name:
            cmd += ["--user-name", request.user_name]
        if request.tts_provider:
            cmd += ["--tts-provider", request.tts_provider.value]
        if request.voice_name:
            cmd += ["--voice-name", request.voice_name]

        # Launch subprocess
        logger.info(f"Launching subprocess with command: {' '.join(cmd)}")
        proc = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent.parent,
            bufsize=1,
        )
        bot_processes[proc.pid] = (proc, room.url)
        logger.info(f"Subprocess started with PID: {proc.pid}")

        return VoiceSessionResponse(
            room_url=room.url,
            token=token,
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create voice session: {str(e)}")

@app.get("/")
async def get_client():
    """Serve the test client HTML."""
    return FileResponse("static/client.html")

@app.get("/websocket")
async def get_websocket_client():
    """Serve the WebSocket audio client HTML."""
    return FileResponse("static/websocket_client.html")

@app.get("/app")
async def get_react_app():
    """Redirect to React voice chat app."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/react/")

@app.get("/react/")
async def get_react_app_index():
    """Serve the React voice chat app."""
    return FileResponse("static/voice-chat/build/index.html")

@app.get("/react")
async def get_react_app_redirect():
    """Redirect to React app with trailing slash."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/react/")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    return JSONResponse({"status": "healthy", "version": __version__})

@app.get("/version")
async def get_version():
    """Get application version."""
    return JSONResponse({"version": __version__})

@app.post("/api/transcript/{session_id}")
async def receive_transcript(session_id: str, message_data: dict):
    """Receive transcript message from voice agent and broadcast to WebSocket clients."""
    speaker = message_data.get("speaker", "unknown")
    message = message_data.get("message", "")
    
    logger.info(f"📝 Transcript [{session_id}] {speaker}: {message}")
    
    # Broadcast to WebSocket clients
    await TranscriptManager.broadcast_message(session_id, speaker, message)
    
    return {"status": "received"}

@app.post("/api/audio/{session_id}")
async def receive_audio(session_id: str, request: Request):
    """Receive TTS audio data from voice agent and stream to WebSocket clients."""
    try:
        audio_data = await request.body()
        
        logger.info(f"🔊 Audio [{session_id}] Received {len(audio_data)} bytes")
        
        # Stream to audio WebSocket clients
        await AudioStreamManager.send_audio(session_id, audio_data)
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing audio data: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/visualization/{session_id}")
async def receive_visualization(session_id: str, visualization_data: dict):
    """Receive visualization data from voice agent and stream to WebSocket clients."""
    try:
        logger.info(f"📊 Visualization [{session_id}] Received {len(visualization_data.get('visualizations', []))} charts")
        
        # Stream to visualization WebSocket clients
        await VisualizationStreamManager.send_visualization(session_id, visualization_data)
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing visualization data: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/transcript/{session_id}")
async def websocket_transcript(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time transcript streaming."""
    await websocket.accept()
    TranscriptManager.add_connection(session_id, websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Transcript stream connected",
            "session_id": session_id
        })
        
        # Keep connection alive
        while True:
            # Wait for messages (keepalive)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
            
    except WebSocketDisconnect:
        TranscriptManager.remove_connection(session_id, websocket)
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        TranscriptManager.remove_connection(session_id, websocket)

@app.websocket("/ws/live")
async def websocket_live_audio(websocket: WebSocket):
    """WebSocket endpoint for Gemini Live audio processing."""
    logger.info(f"🎤 New Gemini Live WebSocket connection")
    await handle_gemini_websocket_session(websocket)

@app.websocket("/ws/audio/{session_id}")
async def websocket_audio_output(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for TTS audio output streaming."""
    await websocket.accept()
    logger.info(f"🔊 Audio output WebSocket connected for session {session_id}")
    
    # Store the connection for the session in audio_connections
    if session_id not in audio_connections:
        audio_connections[session_id] = []
    audio_connections[session_id].append(websocket)
    
    try:
        # Keep connection alive and handle messages
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text('{"type": "ping"}')
    except WebSocketDisconnect:
        logger.info(f"🔊 Audio output WebSocket disconnected for session {session_id}")
        if websocket in audio_connections.get(session_id, []):
            audio_connections[session_id].remove(websocket)
    except Exception as e:
        logger.error(f"Audio WebSocket error for session {session_id}: {e}")
        if websocket in audio_connections.get(session_id, []):
            audio_connections[session_id].remove(websocket)

@app.websocket("/ws/visualization/{session_id}")
async def websocket_visualization_output(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for visualization data streaming."""
    await websocket.accept()
    logger.info(f"📊 Visualization WebSocket connected for session {session_id}")
    
    # Store the connection for the session
    if session_id not in visualization_connections:
        visualization_connections[session_id] = []
    visualization_connections[session_id].append(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Visualization stream connected",
            "session_id": session_id
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info(f"📊 Visualization WebSocket disconnected for session {session_id}")
        if websocket in visualization_connections.get(session_id, []):
            visualization_connections[session_id].remove(websocket)
    except Exception as e:
        logger.error(f"Visualization WebSocket error for session {session_id}: {e}")
        if websocket in visualization_connections.get(session_id, []):
            visualization_connections[session_id].remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")