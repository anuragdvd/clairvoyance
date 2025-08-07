"""
UI Component Generation Tools

Tools for generating visual UI components like charts, tables, and metrics
that can be rendered by the frontend with voice narration.
"""

import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.logger import logger
from pipecat.services.llm_service import FunctionCallParams
from pipecat.adapters.schemas.function_schema import FunctionSchema


# Global registry to store generated components for SSE emission
ui_component_registry: Dict[str, Dict[str, Any]] = {}


async def generate_ui_component(params: FunctionCallParams) -> None:
    """
    Generate a UI component specification for frontend rendering.
    
    This tool creates structured data for charts, tables, or other visual components
    that the frontend can render with automatic voice narration.
    """
    try:
        # Extract parameters
        component_type = params.arguments.get("componentType", "bar-chart")
        title = params.arguments.get("title", "Data Visualization")
        subtitle = params.arguments.get("subtitle")
        categories = params.arguments.get("categories", [])
        series = params.arguments.get("series", [])
        change_percentages = params.arguments.get("changePercentages")
        voice_description = params.arguments.get("voiceDescription", "")
        auto_narrate = params.arguments.get("autoNarrate", True)
        interactive = params.arguments.get("interactive", True)
        
        # Validate required fields
        if not categories:
            await params.result_callback({"error": "Categories are required for UI component generation"})
            return
            
        if not series:
            await params.result_callback({"error": "Series data is required for UI component generation"})
            return
            
        if not voice_description:
            await params.result_callback({"error": "Voice description is required for accessibility"})
            return
        
        # Generate unique component ID
        component_id = f"chart_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Create component specification in exact format expected by frontend
        component_spec = {
            "status": "completed",
            "message": f"Generated {component_type} visualization",
            "componentType": component_type,
            "data": {
                "title": title,
                "subtitle": subtitle,
                "categories": categories,
                "series": series,
                "changePercentages": change_percentages,
                "autoNarrate": auto_narrate,
                "interactive": interactive,
                "metadata": {
                    "chartType": _detect_chart_type(series, categories),
                    "period": _extract_time_period(title, subtitle)
                }
            },
            "voiceDescription": voice_description,
            "renderOrder": 0,
            "componentData": {
                "id": component_id,
                "metadata": {
                    "generatedAt": datetime.now().isoformat(),
                    "dataSource": "analytics",
                    "confidence": _calculate_confidence(series, categories)
                }
            }
        }
        
        # Store in registry for SSE emission
        ui_component_registry[component_id] = component_spec
        
        logger.info(f"Generated UI component: {component_id} of type {component_type}")
        logger.info(f"Component title: {title}")
        logger.info(f"Voice description: {voice_description[:100]}...")
        
        # Return success response to LLM
        await params.result_callback({
            "success": True,
            "componentId": component_id,
            "componentType": component_type,
            "message": f"Successfully generated {component_type} with {len(categories)} categories and {len(series)} data series"
        })
        
    except Exception as e:
        logger.error(f"Error generating UI component: {e}")
        await params.result_callback({
            "error": f"Failed to generate UI component: {str(e)}"
        })


async def generate_bar_chart(params: FunctionCallParams) -> None:
    """
    Generate a bar chart component for categorical data comparison.
    
    Optimized for comparing values across different categories with optional
    percentage changes and time-based comparisons.
    """
    # Set component type and delegate to main function
    params.arguments["componentType"] = "bar-chart"
    await generate_ui_component(params)


async def generate_line_chart(params: FunctionCallParams) -> None:
    """
    Generate a line chart component for time-series or trend data.
    
    Best for showing changes over time, growth patterns, and trend analysis.
    """
    # Set component type and delegate to main function
    params.arguments["componentType"] = "line-chart"
    await generate_ui_component(params)


async def generate_donut_chart(params: FunctionCallParams) -> None:
    """
    Generate a donut chart component for part-to-whole relationships.
    
    Ideal for showing percentage breakdowns and proportion analysis.
    """
    # Set component type and delegate to main function
    params.arguments["componentType"] = "donut-chart"
    await generate_ui_component(params)


def _detect_chart_type(series: List[Dict], categories: List[str]) -> str:
    """Detect the most appropriate chart type based on data characteristics"""
    if not series or not categories:
        return "unknown"
    
    # Check for time-based categories
    time_indicators = ["jan", "feb", "mar", "apr", "may", "jun", 
                      "jul", "aug", "sep", "oct", "nov", "dec",
                      "monday", "tuesday", "wednesday", "thursday", "friday",
                      "week", "month", "quarter", "day"]
    
    has_time_data = any(any(indicator in cat.lower() for indicator in time_indicators) 
                       for cat in categories)
    
    if has_time_data:
        return "temporal"
    elif len(series) == 1 and len(categories) <= 6:
        return "distribution"
    elif len(series) > 1:
        return "comparison"
    else:
        return "categorical"


def _extract_time_period(title: str, subtitle: str) -> str:
    """Extract time period information from title and subtitle"""
    text = f"{title} {subtitle or ''}".lower()
    
    if "month" in text:
        return "monthly"
    elif "week" in text:
        return "weekly"
    elif "quarter" in text:
        return "quarterly"
    elif "year" in text:
        return "yearly"
    elif "day" in text:
        return "daily"
    else:
        return "custom"


def _calculate_confidence(series: List[Dict], categories: List[str]) -> float:
    """Calculate confidence score for the visualization based on data quality"""
    try:
        if not series or not categories:
            return 0.5
        
        # Base confidence
        confidence = 0.8
        
        # Adjust based on data completeness
        total_data_points = sum(len(s.get("data", [])) for s in series)
        expected_points = len(categories) * len(series)
        
        if expected_points > 0:
            completeness = total_data_points / expected_points
            confidence *= completeness
        
        # Adjust based on data variety
        if len(categories) >= 3:
            confidence += 0.1
        if len(series) >= 2:
            confidence += 0.05
            
        return min(confidence, 1.0)
        
    except Exception:
        return 0.7


def get_pending_ui_components() -> Dict[str, Dict[str, Any]]:
    """Get all pending UI components for SSE emission"""
    return ui_component_registry.copy()


def clear_ui_component(component_id: str) -> bool:
    """Remove a component from the registry after successful emission"""
    if component_id in ui_component_registry:
        del ui_component_registry[component_id]
        return True
    return False


def clear_all_ui_components() -> None:
    """Clear all components from the registry"""
    ui_component_registry.clear()


# Tool schemas for LLM function calling
ui_component_schema = FunctionSchema(
    name="generate_ui_component",
    description="Generate visual UI component for analytics data with voice narration support",
    properties={
        "componentType": {
            "type": "string",
            "enum": ["bar-chart", "line-chart", "donut-chart"],
            "description": "Type of chart to generate"
        },
        "title": {
            "type": "string",
            "description": "Main title for the chart"
        },
        "subtitle": {
            "type": "string",
            "description": "Optional subtitle for additional context"
        },
        "categories": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of category names (x-axis labels)"
        },
        "series": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Series name"},
                    "data": {"type": "array", "items": {"type": "number"}, "description": "Data values"},
                    "color": {"type": "string", "description": "Hex color code (optional)"}
                },
                "required": ["name", "data"]
            },
            "description": "Array of data series with values"
        },
        "changePercentages": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Optional percentage changes for each category"
        },
        "voiceDescription": {
            "type": "string",
            "description": "Text description optimized for text-to-speech narration"
        },
        "autoNarrate": {
            "type": "boolean",
            "description": "Whether to automatically start narration when chart renders"
        },
        "interactive": {
            "type": "boolean", 
            "description": "Whether the chart should be interactive"
        }
    },
    required=["componentType", "title", "categories", "series", "voiceDescription"]
)

bar_chart_schema = FunctionSchema(
    name="generate_bar_chart",
    description="Generate bar chart for categorical data comparison with voice narration",
    properties=ui_component_schema.properties,
    required=ui_component_schema.required
)

line_chart_schema = FunctionSchema(
    name="generate_line_chart", 
    description="Generate line chart for time-series trends with voice narration",
    properties=ui_component_schema.properties,
    required=ui_component_schema.required
)

donut_chart_schema = FunctionSchema(
    name="generate_donut_chart",
    description="Generate donut chart for part-to-whole relationships with voice narration", 
    properties=ui_component_schema.properties,
    required=ui_component_schema.required
)