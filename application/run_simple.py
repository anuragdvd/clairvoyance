import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.logger import logger
from app.core.config import PORT, HOST

if __name__ == "__main__":
    logger.info(f"Starting Simple Voice Agent server (Basic Mode) on {HOST}:{PORT}")
    logger.info("This is a basic version without Pipecat dependencies for testing")
    
    uvicorn.run(
        "app.main_simple:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )