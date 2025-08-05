"""
Simple HTTP client for sending transcript messages from voice agent to server.
"""
import asyncio
import aiohttp
import os
from typing import Optional

class TranscriptClient:
    """Client for sending transcript messages to the server."""
    
    def __init__(self, session_id: str, server_url: str = "http://localhost:8000"):
        self.session_id = session_id
        self.server_url = server_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Initialize the HTTP session."""
        self.session = aiohttp.ClientSession()
    
    async def stop(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
    
    async def send_message(self, speaker: str, message: str):
        """Send a transcript message to the server."""
        if not self.session:
            await self.start()
        
        try:
            async with self.session.post(
                f"{self.server_url}/api/transcript/{self.session_id}",
                json={
                    "speaker": speaker,
                    "message": message
                },
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    print(f"✅ Transcript sent: {speaker}: {message}")
                else:
                    print(f"❌ Failed to send transcript: {response.status}")
        except Exception as e:
            print(f"❌ Error sending transcript: {e}")

# Global transcript client instance
transcript_client: Optional[TranscriptClient] = None

def get_transcript_client(session_id: str) -> TranscriptClient:
    """Get or create transcript client for a session."""
    global transcript_client
    if not transcript_client:
        transcript_client = TranscriptClient(session_id)
    return transcript_client