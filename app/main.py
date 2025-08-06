import uvicorn
import json
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import aiohttp
from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper, DailyRoomParams, DailyRoomProperties, DailyMeetingTokenParams, DailyMeetingTokenProperties

# Import necessary components from the new structure
from app.ws.live_session import handle_websocket_session, get_active_connections, get_shutdown_event
from app.core.logger import logger
from app.core.config import DAILY_API_KEY, DAILY_API_URL, PORT, HOST
from app.core.voice_session_manager import voice_session_manager, SessionConfig
from app import __version__
from app.schemas import AutomaticVoiceUserConnectRequest

# Store Daily API helpers
daily_helpers = {}


async def cleanup():
    """Cleanup function to terminate all voice sessions.

    Called during server shutdown.
    """
    logger.info("Attempting to terminate all voice sessions.")
    await voice_session_manager.terminate_all_sessions()
    logger.info("All voice sessions have been handled.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager that handles startup and shutdown tasks."""
    logger.info("Application startup...")
    # Initialize aiohttp session
    aiohttp_session = aiohttp.ClientSession()
    daily_helpers["rest"] = DailyRESTHelper(
        daily_api_key=DAILY_API_KEY,
        daily_api_url=DAILY_API_URL,
        aiohttp_session=aiohttp_session,
    )
    logger.info("Daily REST helper initialized.")
    
    yield
    
    logger.info("Application shutdown event triggered...")
    # Cleanup voice sessions
    await cleanup()
    # Close aiohttp session
    await aiohttp_session.close()
    logger.info("Aiohttp session closed.")
    # Gracefully shutdown websocket connections
    await shutdown_server()


app = FastAPI(title="Breeze Automatic Server", version=__version__, lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# WebSocket endpoint for Gemini Live
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket_session(websocket)

# Pipecat bot endpoint
@app.post("/agent/voice/automatic")
async def bot_connect(request: AutomaticVoiceUserConnectRequest) -> Dict[str, Any]:
    endpoint_start_time = time.time()
    logger.info(f"🚀 NEW VOICE SESSION REQUEST at {time.strftime('%H:%M:%S.%f')[:-3]}")
    logger.info(f"Request payload: {request.model_dump_json(exclude_none=True)}")
    
    # 1. Validate request
    raw_mode = request.mode
    euler_tok = request.eulerToken
    breeze_tok = request.breezeToken
    shop_url = request.shopUrl
    shop_id = request.shopId
    shop_type = request.shopType
    user_name = request.userName
    tts_provider = request.ttsService.ttsProvider.value if request.ttsService else None
    voice_name = request.ttsService.voiceName.value if request.ttsService else None
    merchant_id = request.merchantId
    platform_integrations = request.platformIntegrations

    # 2. Create room + token
    room_creation_start = time.time()
    MAX_DURATION = 30 * 60
    room = await daily_helpers["rest"].create_room(
        params=DailyRoomParams(
            properties=DailyRoomProperties(
                exp=time.time() + MAX_DURATION,
                eject_at_room_exp=True,
            )
        )
    )

    token_params = DailyMeetingTokenParams(
        properties=DailyMeetingTokenProperties(
            eject_after_elapsed=MAX_DURATION,
        )
    )
    
    token = await daily_helpers["rest"].get_token(
        room.url,
        expiry_time=MAX_DURATION,
        eject_at_token_exp=True,
        owner=True,
        params=token_params,
    )
    
    room_creation_time = time.time() - room_creation_start
    logger.info(f"⏱️  Daily room + token created in {room_creation_time*1000:.1f}ms")

    # 3. Create session configuration
    session_config = SessionConfig(
        room_url=room.url,
        token=token,
        mode=raw_mode.upper() if raw_mode else None,
        euler_token=euler_tok,
        breeze_token=breeze_tok,
        shop_url=shop_url,
        shop_id=shop_id,
        shop_type=shop_type,
        user_name=user_name,
        tts_provider=tts_provider,
        voice_name=voice_name,
        merchant_id=merchant_id,
        platform_integrations=platform_integrations
    )

    # 4. Create voice session as async task instead of subprocess
    try:
        session_creation_start = time.time()
        session_id = await voice_session_manager.create_session(session_config)
        session_creation_time = time.time() - session_creation_start
        
        total_endpoint_time = time.time() - endpoint_start_time
        
        logger.info(f"✅ Voice session created successfully with ID: {session_id}")
        logger.info(f"⏱️  Session creation took {session_creation_time*1000:.1f}ms")
        logger.info(f"🎯 TOTAL ENDPOINT RESPONSE TIME: {total_endpoint_time*1000:.1f}ms")
        
        return {
            "room_url": room.url, 
            "token": token,
            "session_id": session_id
        }
    except Exception as e:
        total_endpoint_time = time.time() - endpoint_start_time
        logger.error(f"Failed to create voice session after {total_endpoint_time*1000:.1f}ms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create voice session: {str(e)}")


# Serve client.html at the root
@app.get("/")
async def get_client_html():
    return FileResponse("static/client.html")

# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return JSONResponse({"status": "healthy"})

# Version endpoint
@app.get("/version")
async def get_version():
    """Get application version."""
    return JSONResponse({"version": __version__})

# Session management endpoints
@app.get("/sessions")
async def list_sessions():
    """List all active voice sessions."""
    sessions = voice_session_manager.list_sessions()
    session_info = []
    for session_id, info in sessions.items():
        session_info.append({
            "session_id": session_id,
            "status": info.status,
            "created_at": info.created_at.isoformat(),
            "user_name": info.config.user_name,
            "room_url": info.config.room_url
        })
    return {
        "active_sessions": len(sessions),
        "sessions": session_info
    }

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get information about a specific session."""
    session_info = voice_session_manager.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session_info.status,
        "created_at": session_info.created_at.isoformat(),
        "config": {
            "user_name": session_info.config.user_name,
            "mode": session_info.config.mode,
            "shop_id": session_info.config.shop_id,
            "tts_provider": session_info.config.tts_provider,
            "voice_name": session_info.config.voice_name
        }
    }

@app.delete("/sessions/{session_id}")
async def terminate_session(session_id: str):
    """Terminate a specific voice session."""
    success = await voice_session_manager.terminate_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": f"Session {session_id} terminated successfully"}

# Voice locking control endpoints
@app.get("/voice-locking/status")
async def get_voice_locking_status():
    """Get voice locking configuration and status."""
    from app.core import config
    
    return {
        "enabled": config.ENABLE_VOICE_LOCKING,
        "enrollment_duration": config.SPEAKER_ENROLLMENT_DURATION,
        "similarity_threshold": config.SPEAKER_SIMILARITY_THRESHOLD,
        "chunk_size": config.DIARIZATION_CHUNK_SIZE,
        "sensitivity": config.VOICE_LOCK_SENSITIVITY,
        "quality_threshold": config.AUDIO_QUALITY_THRESHOLD
    }

@app.post("/sessions/{session_id}/voice-locking/enable")
async def enable_voice_locking(session_id: str):
    """Enable voice locking for a specific session."""
    # Note: This would require extending session manager to support
    # dynamic voice locking control per session
    return {"message": "Voice locking control per session not yet implemented"}

@app.post("/sessions/{session_id}/voice-locking/enroll")
async def start_enrollment(session_id: str):
    """Start speaker enrollment for voice locking."""
    # Note: This would require extending session manager to support
    # enrollment control
    return {"message": "Manual enrollment control not yet implemented"}

@app.get("/sessions/{session_id}/voice-locking/status")
async def get_session_voice_locking_status(session_id: str):
    """Get voice locking status for a specific session."""
    # Note: This would require extending session manager to support
    # per-session voice locking status
    return {"message": "Per-session voice locking status not yet implemented"}

# Graceful shutdown handling for WebSocket connections
async def shutdown_server():
    logger.info("Shutdown initiated, closing all WebSocket connections...")
    shutdown_event = get_shutdown_event()
    shutdown_event.set()
    
    active_connections = get_active_connections()
    # Close all active WebSockets
    for ws in list(active_connections): # Iterate over a copy
        try:
            await ws.close(code=1001, reason="Server shutting down")
            if ws in active_connections:
                active_connections.remove(ws)
            logger.info(f"Closed WebSocket connection: {ws.client}")
        except Exception as e:
            logger.error(f"Error closing websocket during shutdown: {e}")
    
    logger.info("All WebSocket connections closed.")

# The main block is now only for direct execution, which is not the recommended way.
# Uvicorn running from run.py is the standard.
if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")