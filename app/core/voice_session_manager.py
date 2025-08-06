import asyncio
import uuid
import time
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.logger import logger
from app.agents.voice.automatic.types import TTSProvider, VoiceName, Mode


@dataclass
class SessionConfig:
    """Configuration for a voice session"""
    room_url: str
    token: str
    mode: Optional[str] = None
    session_id: Optional[str] = None
    euler_token: Optional[str] = None
    breeze_token: Optional[str] = None
    shop_url: Optional[str] = None
    shop_id: Optional[str] = None
    shop_type: Optional[str] = None
    user_name: Optional[str] = None
    tts_provider: Optional[str] = None
    voice_name: Optional[str] = None
    merchant_id: Optional[str] = None
    platform_integrations: Optional[list] = None


@dataclass
class SessionInfo:
    """Information about an active session"""
    session_id: str
    task: asyncio.Task
    config: SessionConfig
    created_at: datetime
    status: str = "active"


class VoiceSessionManager:
    """Manages voice sessions as async tasks instead of subprocesses"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionInfo] = {}
        self._shutdown_event = asyncio.Event()
    
    async def create_session(self, config: SessionConfig) -> str:
        """Create a new voice session and return session ID"""
        session_start_time = time.time()
        
        if not config.session_id:
            config.session_id = str(uuid.uuid4())
        
        session_id = config.session_id
        
        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already exists, terminating existing session")
            await self.terminate_session(session_id)
        
        logger.info(f"🚀 Creating new voice session: {session_id}")
        logger.info(f"⏱️  Session creation started at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        # Create async task for the voice session
        task_creation_start = time.time()
        task = asyncio.create_task(
            self._run_voice_session(session_id, config),
            name=f"voice_session_{session_id}"
        )
        task_creation_time = time.time() - task_creation_start
        logger.info(f"⏱️  Async task created in {task_creation_time*1000:.1f}ms")
        
        # Store session info
        session_info = SessionInfo(
            session_id=session_id,
            task=task,
            config=config,
            created_at=datetime.now(ZoneInfo("Asia/Kolkata"))
        )
        self.active_sessions[session_id] = session_info
        
        # Add cleanup callback
        task.add_done_callback(lambda t: self._cleanup_session(session_id, t))
        
        total_session_creation_time = time.time() - session_start_time
        logger.info(f"🎯 SESSION MANAGER: Voice session {session_id} created in {total_session_creation_time*1000:.1f}ms")
        return session_id
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a specific session"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            logger.warning(f"Session {session_id} not found for termination")
            return False
        
        logger.info(f"Terminating voice session: {session_id}")
        session_info.status = "terminating"
        
        if not session_info.task.done():
            session_info.task.cancel()
            try:
                await asyncio.wait_for(session_info.task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Session {session_id} termination timed out")
            except asyncio.CancelledError:
                logger.info(f"Session {session_id} cancelled successfully")
        
        return True
    
    async def terminate_all_sessions(self):
        """Terminate all active sessions"""
        logger.info(f"Terminating all {len(self.active_sessions)} voice sessions")
        self._shutdown_event.set()
        
        # Cancel all tasks
        tasks = []
        for session_id, session_info in self.active_sessions.items():
            if not session_info.task.done():
                session_info.task.cancel()
                tasks.append(session_info.task)
        
        # Wait for all tasks to complete
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some sessions did not terminate within timeout")
        
        self.active_sessions.clear()
        logger.info("All voice sessions terminated")
    
    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Get information about a specific session"""
        return self.active_sessions.get(session_id)
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions"""
        return len(self.active_sessions)
    
    def list_sessions(self) -> Dict[str, SessionInfo]:
        """Get all active sessions"""
        return self.active_sessions.copy()
    
    def _cleanup_session(self, session_id: str, task: asyncio.Task):
        """Cleanup callback when a session task completes"""
        session_info = self.active_sessions.pop(session_id, None)
        if session_info:
            session_info.status = "completed"
            if task.cancelled():
                logger.info(f"Voice session {session_id} was cancelled")
                session_info.status = "cancelled"
            elif task.exception():
                logger.error(f"Voice session {session_id} failed with exception: {task.exception()}")
                session_info.status = "failed"
                # Log additional context for debugging
                logger.error(f"Session config: user={session_info.config.user_name}, "
                           f"mode={session_info.config.mode}, shop_id={session_info.config.shop_id}")
            else:
                logger.info(f"Voice session {session_id} completed successfully")
                session_info.status = "completed"
        else:
            logger.warning(f"Session {session_id} not found during cleanup")
    
    async def _run_voice_session(self, session_id: str, config: SessionConfig):
        """Run the voice session pipeline as an async task"""
        logger.info(f"Starting voice session pipeline for {session_id}")
        
        try:
            # Import here to avoid circular imports
            from app.agents.voice.automatic.session_runner import run_voice_pipeline
            
            # Run the voice pipeline
            await run_voice_pipeline(
                url=config.room_url,
                token=config.token,
                mode=config.mode,
                session_id=session_id,
                euler_token=config.euler_token,
                breeze_token=config.breeze_token,
                shop_url=config.shop_url,
                shop_id=config.shop_id,
                shop_type=config.shop_type,
                user_name=config.user_name,
                tts_provider=config.tts_provider,
                voice_name=config.voice_name,
                merchant_id=config.merchant_id,
                platform_integrations=config.platform_integrations,
                shutdown_event=self._shutdown_event
            )
            
        except asyncio.CancelledError:
            logger.info(f"Voice session {session_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Voice session {session_id} failed: {e}", exc_info=True)
            raise
        finally:
            logger.info(f"Voice session {session_id} pipeline ended")


# Global session manager instance
voice_session_manager = VoiceSessionManager()