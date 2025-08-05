import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.logger import logger
from app.core.config import PORT, HOST

if __name__ == "__main__":
    logger.info(f"Starting Full Voice Agent server on {HOST}:{PORT}")
    logger.info("This version uses Python 3.11 with full Pipecat capabilities")
    
    # Test if we can import key components
    try:
        from pipecat.services.azure import AzureLLMService
        logger.info("✅ Azure LLM service available")
    except ImportError as e:
        logger.error(f"❌ Azure LLM service import failed: {e}")
    
    try:
        from pipecat.transports.services.daily import DailyTransport  
        logger.info("✅ Daily transport available")
    except ImportError as e:
        logger.error(f"❌ Daily transport import failed: {e}")
        
    try:
        from pipecat.pipeline.pipeline import Pipeline
        logger.info("✅ Pipeline available")
    except ImportError as e:
        logger.error(f"❌ Pipeline import failed: {e}")
    
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=8001,  # Use different port to avoid conflicts
        reload=True,
        log_level="info",
    )