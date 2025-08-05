"""
Visualization Response Processor for Voice-Synchronized Charts
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class HighlightAction:
    timestamp: float
    target: str | int
    action: str
    duration: int = 2000
    color: str = "#667eea"

@dataclass
class VisualizationData:
    type: str
    title: str
    data: List[Dict[str, Any]]
    highlights: List[HighlightAction]
    config: Dict[str, Any]

@dataclass
class LLMVisualizationResponse:
    speech_text: str
    speech_markers: Dict[str, float]
    visualizations: List[VisualizationData]
    presentation_mode: bool = False

class VisualizationPromptProcessor:
    """Processes LLM responses and creates visualization data structures."""
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.speech_rate_wpm = 155  # Average words per minute
        
    def _load_system_prompt(self) -> str:
        """Load the system prompt for visualization generation."""
        prompt_path = Path(__file__).parent / "visualization_system_prompt.md"
        if prompt_path.exists():
            return prompt_path.read_text()
        return ""
    
    def create_visualization_prompt(self, user_query: str, context_data: Optional[Dict] = None) -> str:
        """
        Create a complete prompt for generating visualization responses.
        
        Args:
            user_query: User's question or request
            context_data: Optional data context to include
            
        Returns:
            Complete prompt for the LLM
        """
        
        base_prompt = f"""
{self.system_prompt}

## User Query
{user_query}

## Available Data Context
{json.dumps(context_data, indent=2) if context_data else "No specific data provided - create relevant example data"}

## Instructions
1. Analyze the user's request and determine the most appropriate visualization type(s)
2. Create realistic, relevant data that addresses their query
3. Write engaging speech text that naturally mentions specific data points
4. Calculate precise timestamps for when each data point should be highlighted
5. Choose appropriate highlight actions and colors based on the data story
6. Return a properly formatted JSON response

Remember: The goal is to create a compelling, voice-synchronized data story that brings the information to life through perfectly timed visual emphasis.
"""
        
        return base_prompt.strip()
    
    def estimate_speech_timing(self, text: str) -> float:
        """
        Estimate speech duration based on text length and speaking rate.
        
        Args:
            text: Speech text to analyze
            
        Returns:
            Estimated duration in seconds
        """
        words = len(text.split())
        minutes = words / self.speech_rate_wpm
        return minutes * 60
    
    def extract_data_mentions(self, speech_text: str) -> Dict[str, float]:
        """
        Extract data point mentions from speech text and estimate their timing.
        
        Args:
            speech_text: The speech text to analyze
            
        Returns:
            Dictionary mapping data mentions to estimated timestamps
        """
        
        # Common patterns for data mentions
        patterns = [
            r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b',
            r'\b(Q[1-4]|quarter [1-4])\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b(\d+%|\d+\.\d+%)\b',
            r'\b(\$\d+|\d+ dollars)\b',
            r'\b(highest|lowest|peak|valley|maximum|minimum)\b',
            r'\b(revenue|sales|profit|growth|decline|increase|decrease)\b'
        ]
        
        mentions = {}
        words = speech_text.split()
        total_words = len(words)
        
        for i, word in enumerate(words):
            # Calculate position-based timestamp
            position_ratio = i / total_words if total_words > 0 else 0
            total_duration = self.estimate_speech_timing(speech_text)
            timestamp = position_ratio * total_duration
            
            # Check if word matches any data mention patterns
            for pattern in patterns:
                if re.search(pattern, word, re.IGNORECASE):
                    # Create a key from surrounding context
                    start_idx = max(0, i - 1)
                    end_idx = min(len(words), i + 2)
                    context = " ".join(words[start_idx:end_idx]).lower()
                    mentions[context] = round(timestamp, 1)
        
        return mentions
    
    def parse_llm_response(self, llm_response: str) -> Optional[LLMVisualizationResponse]:
        """
        Parse LLM response into structured visualization data.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            Parsed visualization response or None if parsing fails
        """
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for direct JSON in response
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                else:
                    return None
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Convert to structured objects
            visualizations = []
            for viz_data in data.get('visualizations', []):
                highlights = [
                    HighlightAction(
                        timestamp=h['timestamp'],
                        target=h['target'],
                        action=h['action'],
                        duration=h.get('duration', 2000),
                        color=h.get('color', '#667eea')
                    )
                    for h in viz_data.get('highlights', [])
                ]
                
                visualization = VisualizationData(
                    type=viz_data['type'],
                    title=viz_data.get('title', ''),
                    data=viz_data.get('data', []),
                    highlights=highlights,
                    config=viz_data.get('config', {})
                )
                visualizations.append(visualization)
            
            return LLMVisualizationResponse(
                speech_text=data.get('speechText', ''),
                speech_markers=data.get('speechMarkers', {}),
                visualizations=visualizations,
                presentation_mode=data.get('presentationMode', False)
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            return None
    
    def create_fallback_response(self, user_query: str, error_msg: str = "") -> LLMVisualizationResponse:
        """
        Create a fallback response when LLM parsing fails.
        
        Args:
            user_query: Original user query
            error_msg: Optional error message
            
        Returns:
            Basic visualization response
        """
        
        speech_text = f"I understand you're asking about {user_query}. "
        if error_msg:
            speech_text += f"I encountered an issue generating the visualization: {error_msg}. "
        speech_text += "Let me provide a simple data overview instead."
        
        # Create basic sample data
        sample_data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200},
            {"name": "Item 3", "value": 150}
        ]
        
        visualization = VisualizationData(
            type="bar",
            title="Sample Data Overview",
            data=sample_data,
            highlights=[
                HighlightAction(
                    timestamp=2.0,
                    target=1,
                    action="highlight",
                    duration=2000,
                    color="#667eea"
                )
            ],
            config={
                "xKey": "name",
                "yKey": "value",
                "colors": ["#667eea"],
                "animated": True
            }
        )
        
        return LLMVisualizationResponse(
            speech_text=speech_text,
            speech_markers={"Item 2": 2.0},
            visualizations=[visualization],
            presentation_mode=False
        )
    
    def validate_response(self, response: LLMVisualizationResponse) -> Tuple[bool, List[str]]:
        """
        Validate a visualization response for completeness and correctness.
        
        Args:
            response: Visualization response to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        
        issues = []
        
        # Check speech text
        if not response.speech_text or len(response.speech_text.strip()) < 10:
            issues.append("Speech text is too short or missing")
        
        # Check visualizations
        if not response.visualizations:
            issues.append("No visualizations provided")
        
        for i, viz in enumerate(response.visualizations):
            if not viz.data:
                issues.append(f"Visualization {i} has no data")
            
            if not viz.type in ['bar', 'line', 'pie', 'area', 'scatter', 'table', 'metric']:
                issues.append(f"Visualization {i} has invalid type: {viz.type}")
            
            # Check highlights timing
            speech_duration = self.estimate_speech_timing(response.speech_text)
            for j, highlight in enumerate(viz.highlights):
                if highlight.timestamp > speech_duration + 1:  # Allow 1 second buffer
                    issues.append(f"Highlight {j} in visualization {i} timestamp ({highlight.timestamp}s) exceeds speech duration ({speech_duration:.1f}s)")
        
        return len(issues) == 0, issues
    
    def optimize_highlights(self, response: LLMVisualizationResponse) -> LLMVisualizationResponse:
        """
        Optimize highlight timing and actions for better user experience.
        
        Args:
            response: Original visualization response
            
        Returns:
            Optimized visualization response
        """
        
        speech_duration = self.estimate_speech_timing(response.speech_text)
        
        for viz in response.visualizations:
            # Sort highlights by timestamp
            viz.highlights.sort(key=lambda h: h.timestamp)
            
            # Ensure minimum spacing between highlights
            min_spacing = 1.5  # seconds
            for i in range(1, len(viz.highlights)):
                if viz.highlights[i].timestamp - viz.highlights[i-1].timestamp < min_spacing:
                    viz.highlights[i].timestamp = viz.highlights[i-1].timestamp + min_spacing
            
            # Cap highlights at speech duration
            for highlight in viz.highlights:
                if highlight.timestamp > speech_duration:
                    highlight.timestamp = speech_duration - 0.5
        
        return response

# Example usage functions
def create_sample_sales_prompt():
    """Create a sample sales analysis prompt."""
    processor = VisualizationPromptProcessor()
    
    sample_data = {
        "sales_data": [
            {"month": "Jan", "revenue": 45000, "units": 120},
            {"month": "Feb", "revenue": 52000, "units": 140},
            {"month": "Mar", "revenue": 48000, "units": 130}
        ],
        "context": "Q1 2024 sales performance review"
    }
    
    user_query = "Show me our Q1 sales performance and highlight the best performing month"
    
    return processor.create_visualization_prompt(user_query, sample_data)

def test_response_parsing():
    """Test the response parsing functionality."""
    processor = VisualizationPromptProcessor()
    
    sample_response = '''
    ```json
    {
      "speechText": "Let me show you our Q1 sales data. January started strong with $45,000, February was our peak month at $52,000, and March finished steady at $48,000.",
      "speechMarkers": {
        "January": 3.2,
        "February": 6.8,
        "peak month": 7.5,
        "March": 10.1
      },
      "visualizations": [
        {
          "type": "bar",
          "title": "Q1 2024 Sales Revenue",
          "data": [
            {"month": "Jan", "revenue": 45000},
            {"month": "Feb", "revenue": 52000},
            {"month": "Mar", "revenue": 48000}
          ],
          "highlights": [
            {"timestamp": 3.2, "target": 0, "action": "highlight", "duration": 2000, "color": "#51cf66"},
            {"timestamp": 7.5, "target": 1, "action": "pulse", "duration": 3000, "color": "#339af0"},
            {"timestamp": 10.1, "target": 2, "action": "highlight", "duration": 2000, "color": "#51cf66"}
          ],
          "config": {
            "xKey": "month",
            "yKey": "revenue",
            "colors": ["#667eea"],
            "animated": true
          }
        }
      ],
      "presentationMode": false
    }
    ```
    '''
    
    result = processor.parse_llm_response(sample_response)
    is_valid, issues = processor.validate_response(result) if result else (False, ["Failed to parse"])
    
    print(f"Parsing successful: {result is not None}")
    print(f"Validation passed: {is_valid}")
    if issues:
        print(f"Issues found: {issues}")
    
    return result