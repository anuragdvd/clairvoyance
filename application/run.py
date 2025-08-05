import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.logger import logger
from app.core.config import PORT, HOST

if __name__ == "__main__":
    logger.info(f"Starting Simple Voice Agent server on {HOST}:{PORT}")
    logger.info("Make sure you have set the required environment variables:")
    logger.info("- DAILY_API_KEY")
    logger.info("- AZURE_OPENAI_API_KEY") 
    logger.info("- AZURE_OPENAI_ENDPOINT")
    logger.info("- GOOGLE_CREDENTIALS_JSON")
    
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )