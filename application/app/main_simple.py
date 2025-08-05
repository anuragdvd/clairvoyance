import uvicorn
import uuid
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.logger import logger
from app.core.config import PORT, HOST
from app import __version__
from app.schemas import VoiceConnectRequest, VoiceSessionResponse

# Create FastAPI app
app = FastAPI(
    title="Simple Voice Agent (Basic)",
    version=__version__,
    description="A basic version of the voice agent without Pipecat dependencies",
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

@app.post("/voice/connect", response_model=VoiceSessionResponse)
async def create_voice_session(request: VoiceConnectRequest) -> VoiceSessionResponse:
    """Create a new voice session (basic version)."""
    logger.info(f"Received voice session request: {request.model_dump()}")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    logger.info(f"Generated session ID: {session_id}")

    # Return mock response for now
    return VoiceSessionResponse(
        room_url=f"https://example.daily.co/room-{session_id}",
        token="mock-token-for-testing",
        session_id=session_id
    )

@app.get("/")
async def get_client():
    """Serve the test client HTML."""
    return FileResponse("static/client.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    return JSONResponse({"status": "healthy", "version": __version__, "mode": "basic"})

@app.get("/version")
async def get_version():
    """Get application version."""
    return JSONResponse({"version": __version__, "mode": "basic"})

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")