from datetime import datetime
import pytz
import math
from typing import Dict, Any, Callable, Tuple, List

from app.core.logger import logger

def get_current_time() -> str:
    """Get the current time in a readable format."""
    try:
        # Get current time in different timezones
        utc_now = datetime.now(pytz.UTC)
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        
        return f"Current time: {ist_now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return "Sorry, I couldn't get the current time."

def calculate(expression: str) -> str:
    """Perform basic mathematical calculations."""
    try:
        # Safe evaluation of mathematical expressions
        # Only allow basic math operations
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        allowed_names.update({"__builtins__": {}})
        
        result = eval(expression, allowed_names)
        return f"The result of {expression} is: {result}"
    except Exception as e:
        logger.error(f"Error calculating {expression}: {e}")
        return f"Sorry, I couldn't calculate that. Please check your expression: {expression}"

def get_weather_info(location: str = "general") -> str:
    """Get general weather information."""
    # This is a dummy implementation since we don't have external APIs
    return f"I don't have access to real-time weather data for {location}. You might want to check a weather app or website for current conditions."

def initialize_tools() -> Tuple[List[Dict[str, Any]], Dict[str, Callable]]:
    """Initialize the tool system for the voice agent."""
    
    # Define function schemas for the LLM
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get the current date and time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(3.14159/2)')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather_info", 
                "description": "Get weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    # Map function names to actual functions
    tool_functions = {
        "get_current_time": get_current_time,
        "calculate": calculate,
        "get_weather_info": get_weather_info,
    }
    
    logger.info(f"Initialized {len(tools)} tools: {list(tool_functions.keys())}")
    
    return tools, tool_functions