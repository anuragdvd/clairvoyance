import time

from app.core.logger import logger
from pipecat.frames.frames import Frame, FunctionCallInProgressFrame, FunctionCallResultFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIServerMessageFrame

# Import UI tools for component emission
from app.agents.voice.automatic.tools.system.ui_tools import (
    get_pending_ui_components, 
    clear_ui_component
)


# Custom LLMSpyProcessor for streaming function call events
class LLMSpyProcessor(FrameProcessor):
    """Intercepts function call frames to emit RTVI server messages for start and result."""

    def __init__(self, rtvi: RTVIProcessor, name: str = "LLMSpyProcessor"):
        super().__init__(name=name)
        self._rtvi = rtvi

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Emit RTVI server messages for function call frames."""
        await super().process_frame(frame, direction)

        if isinstance(frame, FunctionCallInProgressFrame):
            logger.info(f"Function call started: {frame.function_name} with args: {frame.arguments}")
            await self._rtvi.push_frame(
                RTVIServerMessageFrame(
                    data={
                        "type": "tool-call-start",
                        "payload": {
                            "toolCallId": frame.tool_call_id,
                            "functionName": frame.function_name,
                            "arguments": frame.arguments,
                            "timestamp": int(time.time() * 1000)
                        }
                    }
                )
            )
        elif isinstance(frame, FunctionCallResultFrame):
            logger.info(f"Function call result: {frame.function_name} with result: {frame.result}")
            await self._rtvi.push_frame(
                RTVIServerMessageFrame(
                    data={
                        "type": "tool-call-result",
                        "payload": {
                            "toolCallId": frame.tool_call_id,
                            "functionName": frame.function_name,
                            "arguments": frame.arguments,
                            "result": frame.result,
                            "timestamp": int(time.time() * 1000)
                        }
                    }
                )
            )
            
            # Check for UI component generation and emit ui-component events
            await self._check_and_emit_ui_components(frame.function_name)
            
            # Also check for analytics tools that may have generated visualizations
            await self._check_analytics_visualizations(frame.function_name)

        await self.push_frame(frame, direction)
    
    async def _check_and_emit_ui_components(self, function_name: str):
        """Check for pending UI components and emit them via SSE"""
        try:
            # Check if this was a UI component generation function
            ui_functions = [
                "generate_ui_component", 
                "generate_bar_chart", 
                "generate_line_chart", 
                "generate_donut_chart"
            ]
            
            if function_name in ui_functions:
                # Get all pending UI components
                pending_components = get_pending_ui_components()
                
                for component_id, component_spec in pending_components.items():
                    logger.info(f"Emitting UI component via SSE: {component_id}")
                    logger.info(f"Component type: {component_spec.get('componentType')}")
                    logger.info(f"Component title: {component_spec.get('data', {}).get('title')}")
                    
                    # Emit the ui-component SSE event in exact format expected by frontend
                    await self._rtvi.push_frame(
                        RTVIServerMessageFrame(
                            data={
                                "type": "ui-component",
                                "payload": component_spec
                            }
                        )
                    )
                    
                    # Clear the component from registry after emission
                    clear_ui_component(component_id)
                    
        except Exception as e:
            logger.error(f"Error emitting UI components: {e}")
    
    async def _emit_ui_component_directly(self, component_spec: dict):
        """Directly emit a UI component (for use by analytics tools)"""
        try:
            logger.info(f"Directly emitting UI component: {component_spec.get('componentData', {}).get('id')}")
            
            await self._rtvi.push_frame(
                RTVIServerMessageFrame(
                    data={
                        "type": "ui-component", 
                        "payload": component_spec
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Error directly emitting UI component: {e}")
    
    async def _check_analytics_visualizations(self, function_name: str):
        """Check if analytics tools generated visualizations and emit them"""
        try:
            # List of analytics functions that may generate visualizations
            analytics_functions = [
                "get_breeze_sales_data",
                "get_breeze_orders_data", 
                "get_breeze_checkout_data",
                "get_breeze_conversion_data",
                "get_breeze_marketing_data",
                "get_juspay_analytics",  # Add Juspay functions as they're enhanced
                # Add more analytics functions here as they're enhanced
            ]
            
            if function_name in analytics_functions:
                # Get any pending UI components from analytics tools
                pending_components = get_pending_ui_components()
                
                for component_id, component_spec in pending_components.items():
                    # Check if this component was generated by an analytics tool
                    data_source = component_spec.get("componentData", {}).get("metadata", {}).get("dataSource")
                    
                    if data_source in ["breeze_analytics", "juspay_analytics"]:
                        logger.info(f"Emitting analytics visualization: {component_id}")
                        logger.info(f"Data source: {data_source}")
                        
                        await self._rtvi.push_frame(
                            RTVIServerMessageFrame(
                                data={
                                    "type": "ui-component",
                                    "payload": component_spec
                                }
                            )
                        )
                        
                        # Clear after emission
                        clear_ui_component(component_id)
                        
        except Exception as e:
            logger.error(f"Error checking analytics visualizations: {e}")