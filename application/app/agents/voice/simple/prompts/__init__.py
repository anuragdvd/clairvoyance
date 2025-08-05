"""
Voice-Synchronized Visualization Prompts Module

This module provides comprehensive prompt templates and processing utilities
for generating LLM responses with synchronized chart highlighting.
"""

from typing import Optional

from .visualization_processor import (
    VisualizationPromptProcessor,
    LLMVisualizationResponse,
    VisualizationData,
    HighlightAction
)

from .business_analytics_prompts import (
    generate_prompt,
    get_example_context,
    EXAMPLE_CONTEXTS
)

from .examples import (
    get_example_by_type,
    get_all_example_types,
    generate_enhanced_prompt,
    EXAMPLE_PROMPTS,
    PROMPT_ENHANCEMENT_GUIDELINES
)

def get_system_prompt(user_name: Optional[str] = None) -> str:
    """Generate enhanced system prompt for the voice agent with visualization capabilities."""
    
    base_prompt = """You are an advanced voice assistant with data visualization capabilities. You can have natural conversations with users and create interactive charts, graphs, and dashboards that synchronize with your speech.

Key behaviors:
- Be conversational and friendly
- Keep responses concise but helpful
- When users request data analysis or charts, respond with structured JSON format for voice-synchronized visualizations
- Always be polite and professional
- If you don't understand something, ask for clarification

Available capabilities:
- Answer questions and have conversations
- Get current time and date
- Perform calculations
- Create interactive visualizations (charts, graphs, tables, metrics)
- Generate voice-synchronized data presentations
- Analyze trends and provide insights

Visualization Features:
- Bar charts, line charts, pie charts, area charts, scatter plots
- Interactive tables with highlighting
- Metrics dashboards with KPI cards
- Real-time highlighting synchronized with speech
- Color-coded insights (green=positive, red=negative, blue=neutral)

When creating visualizations, use this JSON format:
```json
{
  "speechText": "Your natural speaking response...",
  "speechMarkers": {"key phrase": timestamp},
  "visualizations": [{
    "type": "bar|line|pie|area|scatter|table|metric",
    "title": "Chart Title", 
    "data": [...],
    "highlights": [{"timestamp": 2.5, "target": 0, "action": "highlight", "duration": 2000, "color": "#667eea"}],
    "config": {"xKey": "name", "yKey": "value", "colors": ["#667eea"]}
  }],
  "presentationMode": false
}
```

Remember: You are speaking, so keep responses natural and time highlights to sync with your speech (155 words/minute rate)."""

    if user_name:
        personalized_prompt = f"""You are an advanced voice assistant with data visualization capabilities speaking with {user_name}. You can have natural conversations and create interactive charts that synchronize with your speech.

Key behaviors:
- Be conversational and friendly, addressing {user_name} by name when appropriate
- Keep responses concise but helpful
- When {user_name} requests data analysis or charts, respond with structured JSON format for voice-synchronized visualizations
- Always be polite and professional
- If you don't understand something, ask for clarification

Available capabilities:
- Answer questions and have conversations with {user_name}
- Get current time and date
- Perform calculations
- Create interactive visualizations (charts, graphs, tables, metrics)
- Generate voice-synchronized data presentations
- Analyze trends and provide insights

Visualization Features:
- Bar charts, line charts, pie charts, area charts, scatter plots
- Interactive tables with highlighting
- Metrics dashboards with KPI cards
- Real-time highlighting synchronized with speech
- Color-coded insights (green=positive, red=negative, blue=neutral)

When {user_name} requests visualizations, use the structured JSON format with speechText, speechMarkers, visualizations array, and proper timing for highlight synchronization.

Remember: You are speaking with {user_name}, so keep responses natural and conversational while creating engaging data stories."""
        return personalized_prompt
    
    return base_prompt

__all__ = [
    # Core system prompt
    'get_system_prompt',
    
    # Core processor
    'VisualizationPromptProcessor',
    'LLMVisualizationResponse', 
    'VisualizationData',
    'HighlightAction',
    
    # Business prompts
    'generate_prompt',
    'get_example_context',
    'EXAMPLE_CONTEXTS',
    
    # Examples and guidelines
    'get_example_by_type',
    'get_all_example_types', 
    'generate_enhanced_prompt',
    'EXAMPLE_PROMPTS',
    'PROMPT_ENHANCEMENT_GUIDELINES'
]

# Quick access functions
def create_sales_visualization_prompt(user_query: str, sales_data: dict) -> str:
    """Quick function to create sales visualization prompt."""
    processor = VisualizationPromptProcessor()
    return processor.create_visualization_prompt(user_query, sales_data)

def create_financial_dashboard_prompt(user_query: str, financial_data: dict) -> str:
    """Quick function to create financial dashboard prompt."""
    processor = VisualizationPromptProcessor()
    return processor.create_visualization_prompt(user_query, financial_data)

def process_llm_visualization_response(llm_response: str) -> LLMVisualizationResponse:
    """Quick function to process LLM response into visualization data."""
    processor = VisualizationPromptProcessor()
    result = processor.parse_llm_response(llm_response)
    
    if result:
        # Validate and optimize
        is_valid, issues = processor.validate_response(result)
        if not is_valid:
            print(f"Validation issues: {issues}")
        
        return processor.optimize_highlights(result)
    else:
        # Return fallback
        return processor.create_fallback_response("data visualization", "Failed to parse response")

# Demo data for testing
DEMO_DATA = {
    "sales_performance": {
        "monthly_sales": [
            {"month": "Jan", "revenue": 85000, "units": 340, "growth": 12.5},
            {"month": "Feb", "revenue": 92000, "units": 380, "growth": 8.2},
            {"month": "Mar", "revenue": 78000, "units": 310, "growth": -15.2},
            {"month": "Apr", "revenue": 95000, "units": 400, "growth": 21.8},
            {"month": "May", "revenue": 103000, "units": 425, "growth": 8.4},
            {"month": "Jun", "revenue": 118000, "units": 480, "growth": 14.6}
        ]
    },
    
    "financial_metrics": {
        "kpis": [
            {"name": "Revenue", "value": 2450000, "change": 18.5, "unit": "USD"},
            {"name": "Profit", "value": 580000, "change": 35.2, "unit": "USD"},
            {"name": "Expenses", "value": 890000, "change": 12.3, "unit": "USD"},
            {"name": "Cash Flow", "value": 720000, "change": 28.7, "unit": "USD"}
        ]
    },
    
    "market_analysis": {
        "market_share": [
            {"company": "Our Company", "share": 28.5, "growth": 5.2},
            {"company": "Competitor A", "share": 35.1, "growth": 2.1},
            {"company": "Competitor B", "share": 18.7, "growth": -1.8},
            {"company": "Competitor C", "share": 12.4, "growth": 3.5},
            {"company": "Others", "share": 5.3, "growth": -2.1}
        ]
    }
}