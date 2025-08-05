import logging
import sys
from typing import Optional

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger instance
logger = logging.getLogger("voice_app")

def configure_session_logger(session_id: Optional[str] = None):
    """Configure logger with session-specific context."""
    if session_id:
        # Create a session-specific logger
        session_logger = logging.getLogger(f"voice_app.session.{session_id}")
        session_logger.setLevel(logging.INFO)
        return session_logger
    return logger

def set_log_level(level: str):
    """Set the logging level."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    logger.setLevel(numeric_level)