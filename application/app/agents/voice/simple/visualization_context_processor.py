"""
Enhanced LLM Context Processor for Voice-Synchronized Visualizations
"""

import json
import re
import asyncio
from typing import Optional, Dict, Any, List
from pipecat.frames.frames import (
    Frame, 
    LLMMessagesFrame, 
    LLMFullResponseEndFrame,
    SystemFrame
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

from .prompts import (
    VisualizationPromptProcessor,
    process_llm_visualization_response,
    LLMVisualizationResponse,
    DEMO_DATA
)
from app.core.logger import logger

class VisualizationContextProcessor(FrameProcessor):
    """
    Enhanced context processor that detects visualization requests and 
    enhances LLM prompts for voice-synchronized chart generation.
    """
    
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self.processor = VisualizationPromptProcessor()
        self.visualization_keywords = [
            'chart', 'graph', 'visualize', 'plot', 'dashboard', 'metrics',
            'show me', 'display', 'analyze', 'breakdown', 'trends', 'performance',
            'sales data', 'financial', 'revenue', 'growth', 'comparison'
        ]
        
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames and enhance visualization requests."""
        
        # Handle LLM message frames to enhance prompts
        if isinstance(frame, LLMMessagesFrame):
            enhanced_frame = await self._enhance_llm_messages(frame)
            await self.push_frame(enhanced_frame, direction)
            return
            
        # Handle LLM response frames to extract visualization data
        if isinstance(frame, LLMFullResponseEndFrame):
            await self._process_llm_response(frame)
            
        await self.push_frame(frame, direction)
    
    async def _enhance_llm_messages(self, frame: LLMMessagesFrame) -> LLMMessagesFrame:
        """Enhance LLM messages with visualization context."""
        
        try:
            messages = frame.messages.copy()
            last_message = messages[-1] if messages else None
            
            if not last_message or last_message.get('role') != 'user':
                return frame
                
            user_content = last_message.get('content', '')
            
            # Check if this is a visualization request
            if self._is_visualization_request(user_content):
                logger.info(f"📊 Detected visualization request: {user_content[:100]}...")
                
                # Enhance the prompt with visualization instructions
                enhanced_content = self._create_enhanced_prompt(user_content)
                
                # Update the user message
                messages[-1] = {
                    'role': 'user',
                    'content': enhanced_content
                }
                
                # Add visualization system message if not present
                system_message = self._get_visualization_system_message()
                if not any(msg.get('role') == 'system' and 'visualization' in msg.get('content', '').lower() for msg in messages):
                    messages.insert(0, system_message)
                
                logger.info("✅ Enhanced prompt with visualization instructions")
                
            return LLMMessagesFrame(messages)
            
        except Exception as e:
            logger.error(f"Error enhancing LLM messages: {e}")
            return frame
    
    def _is_visualization_request(self, content: str) -> bool:
        """Check if the user content is requesting a visualization."""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.visualization_keywords)
    
    def _create_enhanced_prompt(self, user_content: str) -> str:
        """Create an enhanced prompt with visualization context."""
        
        # Detect the type of data request
        context_data = self._get_relevant_demo_data(user_content)
        
        enhanced_prompt = f"""
{user_content}

VISUALIZATION RESPONSE REQUIRED:
Please respond with a voice-synchronized visualization using the following JSON format:

```json
{{
  "speechText": "Your natural speaking response that mentions specific data points...",
  "speechMarkers": {{
    "first quarter": 2.5,
    "peak value": 8.1
  }},
  "visualizations": [
    {{
      "type": "bar|line|pie|area|scatter|table|metric",
      "title": "Chart Title",
      "data": [...],
      "highlights": [
        {{
          "timestamp": 2.5,
          "target": 0,
          "action": "highlight|pulse|zoom|focus|reveal",
          "duration": 2000,
          "color": "#667eea"
        }}
      ],
      "config": {{
        "xKey": "name",
        "yKey": "value",
        "colors": ["#667eea"],
        "animated": true
      }}
    }}
  ],
  "presentationMode": false
}}
```

TIMING GUIDELINES:
- Calculate timestamps based on 155 words per minute speaking rate
- Space highlights at least 1.5 seconds apart
- Align highlights with natural speech mentions of data points

COLOR GUIDELINES:
- Green (#51cf66): Positive trends, growth, success
- Red (#ff6b6b): Negative trends, problems, alerts  
- Blue (#339af0): Neutral information, comparisons
- Orange (#ff922b): Warnings, attention points

Available demo data context:
{json.dumps(context_data, indent=2) if context_data else "Create realistic example data"}

Create an engaging data story with perfectly timed visual highlights!
"""
        
        return enhanced_prompt.strip()
    
    def _get_relevant_demo_data(self, content: str) -> Optional[Dict]:
        """Get relevant demo data based on user request."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['sales', 'revenue', 'monthly', 'quarterly']):
            return DEMO_DATA.get('sales_performance')
        elif any(word in content_lower for word in ['financial', 'profit', 'kpi', 'dashboard']):
            return DEMO_DATA.get('financial_metrics')
        elif any(word in content_lower for word in ['market', 'competition', 'share', 'competitor']):
            return DEMO_DATA.get('market_analysis')
        
        return None
    
    def _get_visualization_system_message(self) -> Dict[str, str]:
        """Get the system message for visualization enhancement."""
        return {
            'role': 'system',
            'content': '''You are an AI assistant with advanced data visualization capabilities. When users request data analysis, charts, or visualizations, you must respond with a structured JSON format that enables voice-synchronized highlighting.

Key requirements:
1. Always include speechText with natural, engaging narration
2. Add speechMarkers for key data point mentions
3. Create appropriate visualizations with highlight timing
4. Use colors that match the data story (green=good, red=problems, blue=neutral)
5. Time highlights to sync with speech mentions (155 words/minute rate)

Your goal is to create compelling data stories where visuals come alive through perfectly synchronized voice narration.'''
        }
    
    async def _process_llm_response(self, frame: LLMFullResponseEndFrame) -> None:
        """Process LLM response to extract and send visualization data."""
        
        try:
            response_text = getattr(frame, 'text', '') or getattr(frame, 'content', '')
            
            if not response_text:
                logger.warning("No response text found in LLMFullResponseEndFrame")
                return
            
            # Try to parse visualization response
            viz_response = process_llm_visualization_response(response_text)
            
            if viz_response and viz_response.visualizations:
                logger.info(f"📊 Extracted {len(viz_response.visualizations)} visualizations from LLM response")
                
                # Send visualization data to client
                await self._send_visualization_data(viz_response)
            else:
                logger.debug("No visualization data found in LLM response")
                
        except Exception as e:
            logger.error(f"Error processing LLM response for visualizations: {e}")
    
    async def _send_visualization_data(self, viz_response: LLMVisualizationResponse) -> None:
        """Send visualization data to the client via HTTP."""
        
        try:
            # Convert to dict for JSON serialization
            viz_data = {
                'speechText': viz_response.speech_text,
                'speechMarkers': viz_response.speech_markers,
                'visualizations': [
                    {
                        'type': viz.type,
                        'title': viz.title,
                        'data': viz.data,
                        'highlights': [
                            {
                                'timestamp': h.timestamp,
                                'target': h.target,
                                'action': h.action,
                                'duration': h.duration,
                                'color': h.color
                            }
                            for h in viz.highlights
                        ],
                        'config': viz.config
                    }
                    for viz in viz_response.visualizations
                ],
                'presentationMode': viz_response.presentation_mode
            }
            
            # Send via HTTP to client (same pattern as transcript)
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8000/api/visualization/{self.session_id}"
                async with session.post(url, json=viz_data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Sent visualization data to client for session {self.session_id}")
                    else:
                        logger.warning(f"Failed to send visualization data: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending visualization data: {e}")

class EnhancedLLMResponseAggregator(LLMFullResponseEndFrame):
    """Enhanced aggregator that captures full response for visualization processing."""
    
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self._accumulated_text = ""
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Accumulate LLM response text and process when complete."""
        
        # Accumulate text from LLM response frames
        if hasattr(frame, 'text') and frame.text:
            self._accumulated_text += frame.text
        
        # When response is complete, create enhanced frame
        if isinstance(frame, LLMFullResponseEndFrame):
            enhanced_frame = LLMFullResponseEndFrame()
            enhanced_frame.text = self._accumulated_text
            enhanced_frame.content = self._accumulated_text
            
            await self.push_frame(enhanced_frame, direction)
            self._accumulated_text = ""  # Reset for next response
            return
        
        await self.push_frame(frame, direction)