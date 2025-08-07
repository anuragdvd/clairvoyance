import httpx
import json
from datetime import datetime
import pytz
import uuid
import time

from app.core.logger import logger
from pipecat.services.llm_service import FunctionCallParams
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

# Import UI tools for automatic visualization generation
from app.agents.voice.automatic.tools.system.ui_tools import ui_component_registry

# These will be set by the initializer
breeze_token: str | None = None
shop_id: str | None = None
shop_url: str | None = None
shop_type: str | None = None


def _should_generate_visualization(data: dict, operational_tab: str) -> bool:
    """Determine if the analytics data should generate a visualization"""
    try:
        # Check if data is suitable for visualization
        if not data or "error" in data:
            return False
        
        # Look for categorical data that can be charted
        has_categories = False
        has_numerical_data = False
        
        # Check for common data structures that indicate chartable data
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 2:
                # Check if list contains objects with categorical data
                if all(isinstance(item, dict) for item in value):
                    has_categories = True
                    # Check for numerical values
                    for item in value:
                        if any(isinstance(v, (int, float)) for v in item.values()):
                            has_numerical_data = True
                            break
        
        return has_categories and has_numerical_data
        
    except Exception as e:
        logger.error(f"Error checking visualization suitability: {e}")
        return False


def _extract_chart_data_from_response(data: dict, operational_tab: str) -> dict:
    """Extract and format chart data from Breeze API response"""
    try:
        chart_data = {
            "categories": [],
            "series": [],
            "changePercentages": [],
            "title": _get_chart_title(operational_tab),
            "subtitle": _get_chart_subtitle(data),
            "componentType": "bar-chart"  # Default to bar chart
        }
        
        # Extract data based on operational tab type
        if operational_tab == "SALES":
            chart_data = _extract_sales_chart_data(data, chart_data)
        elif operational_tab == "ORDERS":
            chart_data = _extract_orders_chart_data(data, chart_data)
        elif operational_tab == "CHECKOUT":
            chart_data = _extract_checkout_chart_data(data, chart_data)
        elif operational_tab == "CONVERSIONS":
            chart_data = _extract_conversion_chart_data(data, chart_data)
        elif operational_tab == "MARKETING":
            chart_data = _extract_marketing_chart_data(data, chart_data)
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error extracting chart data: {e}")
        return {}


def _extract_sales_chart_data(data: dict, chart_data: dict) -> dict:
    """Extract sales-specific chart data"""
    try:
        # Look for common sales data patterns
        categories = []
        values = []
        
        # Check for different possible data structures
        if "categories" in data and "values" in data:
            categories = data["categories"]
            values = data["values"]
        elif isinstance(data, list):
            # List of objects with category and value
            for item in data:
                if isinstance(item, dict):
                    # Try common field names
                    category = item.get("category") or item.get("name") or item.get("product") or item.get("type")
                    value = item.get("sales") or item.get("amount") or item.get("value") or item.get("total")
                    
                    if category and isinstance(value, (int, float)):
                        categories.append(str(category))
                        values.append(value)
        
        if categories and values:
            chart_data["categories"] = categories
            chart_data["series"] = [{
                "name": "Sales",
                "data": values,
                "color": "#1f77b4"
            }]
            
        return chart_data
        
    except Exception as e:
        logger.error(f"Error extracting sales chart data: {e}")
        return chart_data


def _extract_orders_chart_data(data: dict, chart_data: dict) -> dict:
    """Extract orders-specific chart data"""
    try:
        categories = []
        values = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    category = item.get("category") or item.get("product") or item.get("type") or item.get("status")
                    value = item.get("orders") or item.get("count") or item.get("quantity") or item.get("total")
                    
                    if category and isinstance(value, (int, float)):
                        categories.append(str(category))
                        values.append(value)
        
        if categories and values:
            chart_data["categories"] = categories
            chart_data["series"] = [{
                "name": "Orders",
                "data": values,
                "color": "#ff7f0e"
            }]
            
        return chart_data
        
    except Exception as e:
        logger.error(f"Error extracting orders chart data: {e}")
        return chart_data


def _extract_checkout_chart_data(data: dict, chart_data: dict) -> dict:
    """Extract checkout-specific chart data"""
    try:
        categories = []
        values = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    category = item.get("step") or item.get("stage") or item.get("type")
                    value = item.get("conversions") or item.get("count") or item.get("rate")
                    
                    if category and isinstance(value, (int, float)):
                        categories.append(str(category))
                        values.append(value)
        
        if categories and values:
            chart_data["categories"] = categories
            chart_data["series"] = [{
                "name": "Checkout Rate",
                "data": values,
                "color": "#2ca02c"
            }]
            
        return chart_data
        
    except Exception as e:
        logger.error(f"Error extracting checkout chart data: {e}")
        return chart_data


def _extract_conversion_chart_data(data: dict, chart_data: dict) -> dict:
    """Extract conversion-specific chart data"""
    return _extract_checkout_chart_data(data, chart_data)  # Similar structure


def _extract_marketing_chart_data(data: dict, chart_data: dict) -> dict:
    """Extract marketing-specific chart data"""
    try:
        categories = []
        values = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    category = item.get("channel") or item.get("campaign") or item.get("source") or item.get("type")
                    value = item.get("clicks") or item.get("impressions") or item.get("conversions") or item.get("spend")
                    
                    if category and isinstance(value, (int, float)):
                        categories.append(str(category))
                        values.append(value)
        
        if categories and values:
            chart_data["categories"] = categories
            chart_data["series"] = [{
                "name": "Marketing Performance",
                "data": values,
                "color": "#d62728"
            }]
            
        return chart_data
        
    except Exception as e:
        logger.error(f"Error extracting marketing chart data: {e}")
        return chart_data


def _get_chart_title(operational_tab: str) -> str:
    """Get appropriate chart title based on operational tab"""
    titles = {
        "SALES": "Sales Performance",
        "ORDERS": "Order Analysis", 
        "CHECKOUT": "Checkout Funnel",
        "CONVERSIONS": "Conversion Metrics",
        "MARKETING": "Marketing Performance"
    }
    return titles.get(operational_tab, "Analytics Data")


def _get_chart_subtitle(data: dict) -> str:
    """Generate chart subtitle from data context"""
    # Could extract time period, comparison info, etc.
    return "Breeze Analytics Data"


def _generate_voice_description(chart_data: dict, operational_tab: str) -> str:
    """Generate voice description for the chart"""
    try:
        title = chart_data.get("title", "Chart")
        categories = chart_data.get("categories", [])
        series = chart_data.get("series", [])
        
        if not categories or not series:
            return f"This chart shows {title.lower()} data."
        
        description = f"This chart shows {title.lower()} with {len(categories)} categories: "
        description += ", ".join(categories[:5])  # Limit to first 5 categories
        
        if len(categories) > 5:
            description += f" and {len(categories) - 5} more"
        
        if series and len(series[0].get("data", [])) > 0:
            values = series[0]["data"]
            max_value = max(values)
            max_index = values.index(max_value)
            
            description += f". The highest value is {max_value} for {categories[max_index]}."
            
        return description
        
    except Exception as e:
        logger.error(f"Error generating voice description: {e}")
        return "Chart showing analytics data."


def _create_ui_component_spec(chart_data: dict, operational_tab: str) -> dict:
    """Create complete UI component specification"""
    component_id = f"chart_{operational_tab.lower()}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    return {
        "status": "completed",
        "message": f"Generated {chart_data.get('componentType', 'chart')} for {operational_tab.lower()} data",
        "componentType": chart_data.get("componentType", "bar-chart"),
        "data": {
            "title": chart_data["title"],
            "subtitle": chart_data.get("subtitle"),
            "categories": chart_data["categories"],
            "series": chart_data["series"],
            "changePercentages": chart_data.get("changePercentages"),
            "autoNarrate": True,
            "interactive": True,
            "metadata": {
                "chartType": "analytics",
                "period": "recent",
                "dataSource": operational_tab.lower()
            }
        },
        "voiceDescription": _generate_voice_description(chart_data, operational_tab),
        "renderOrder": 0,
        "componentData": {
            "id": component_id,
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "dataSource": "breeze_analytics",
                "confidence": 0.85,
                "operationalTab": operational_tab
            }
        }
    }

async def _make_breeze_request(params: FunctionCallParams, operational_tab: str):
    """Generic helper to make requests to the Breeze analytics API."""
    if not all([breeze_token, shop_id, shop_url, shop_type]):
        logger.error("Breeze tool called without required context (token, shopId, shopUrl, shopType).")
        await params.result_callback({"error": "Breeze tool is not configured."})
        return

    start_time_ist_str = params.arguments.get("startTime")
    end_time_ist_str = params.arguments.get("endTime")

    if not start_time_ist_str:
        await params.result_callback({"error": "startTime is a required parameter."})
        return

    try:
        ist = pytz.timezone("Asia/Kolkata")
        utc = pytz.utc

        # Convert start time from IST string to UTC datetime object
        start_time_ist = ist.localize(datetime.strptime(start_time_ist_str, '%Y-%m-%d %H:%M:%S'))
        start_time_utc = start_time_ist.astimezone(utc)

        # Handle end time
        if end_time_ist_str:
            end_time_ist = ist.localize(datetime.strptime(end_time_ist_str, '%Y-%m-%d %H:%M:%S'))
        else:
            end_time_ist = datetime.now(ist)
        end_time_utc = end_time_ist.astimezone(utc)

        # Format to ISO string required by the API
        start_time_iso = start_time_utc.isoformat().replace('+00:00', 'Z')
        end_time_iso = end_time_utc.isoformat().replace('+00:00', 'Z')

    except Exception as e:
        logger.error(f"Error converting time: {e}")
        await params.result_callback({"error": f"Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'. Error: {e}"})
        return

    api_url = "https://portal.breeze.in/analytics"
    payload = {
        "shopIds": [shop_id],
        "shops": [shop_url],
        "startTime": start_time_iso,
        "endTime": end_time_iso,
        "operationalTab": operational_tab,
        "granularityFilter": {"timeGranularity": "DAILY", "paymentMethods": "ALL"},
        "shopType": shop_type
    }
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "x-auth-token": breeze_token
    }

    logger.info(f"Requesting Breeze {operational_tab} data with payload: {json.dumps(payload)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            response_json = response.json()
            logger.info(f"Received Breeze API response status: {response_json.get('statusCode')}")
            
            data = response_json.get("data", {"error": "No data field in response"})
            
            # Check if data is suitable for visualization and generate UI component
            if _should_generate_visualization(data, operational_tab):
                logger.info(f"Generating visualization for {operational_tab} data")
                
                chart_data = _extract_chart_data_from_response(data, operational_tab)
                if chart_data and chart_data.get("categories") and chart_data.get("series"):
                    ui_component_spec = _create_ui_component_spec(chart_data, operational_tab)
                    
                    # Store in registry for emission by LLMSpyProcessor
                    component_id = ui_component_spec["componentData"]["id"]
                    ui_component_registry[component_id] = ui_component_spec
                    
                    logger.info(f"Created UI component: {component_id}")
                    logger.info(f"Chart title: {chart_data['title']}")
                    logger.info(f"Categories: {len(chart_data['categories'])}, Series: {len(chart_data['series'])}")
            
            await params.result_callback(data)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Breeze API: {e.response.status_code} - {e.response.text}")
        await params.result_callback({"error": f"Breeze API error: {e.response.status_code}", "details": e.response.text})
    except Exception as e:
        logger.error(f"Unexpected error calling Breeze API: {e}")
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})


async def get_breeze_sales_data(params: FunctionCallParams):
    """Fetches sales data from the Breeze analytics API."""
    await _make_breeze_request(params, "SALES")


async def get_breeze_orders_data(params: FunctionCallParams):
    """Fetches order data from the Breeze analytics API."""
    await _make_breeze_request(params, "ORDERS")


async def get_breeze_checkout_data(params: FunctionCallParams):
    """Fetches checkout data from the Breeze analytics API."""
    await _make_breeze_request(params, "CHECKOUT")


async def get_breeze_conversion_data(params: FunctionCallParams):
    """Fetches conversion data from the Breeze analytics API."""
    await _make_breeze_request(params, "CONVERSIONS")


async def get_breeze_marketing_data(params: FunctionCallParams):
    """Fetches marketing attribution data from the Breeze analytics API."""
    if not all([breeze_token, shop_id, shop_url, shop_type]):
        logger.error("Breeze tool called without required context (token, shopId, shopUrl, shopType).")
        await params.result_callback({"error": "Breeze tool is not configured."})
        return

    start_time_ist_str = params.arguments.get("startTime")
    end_time_ist_str = params.arguments.get("endTime")

    if not start_time_ist_str:
        await params.result_callback({"error": "startTime is a required parameter."})
        return

    try:
        ist = pytz.timezone("Asia/Kolkata")
        utc = pytz.utc

        start_time_ist = ist.localize(datetime.strptime(start_time_ist_str, '%Y-%m-%d %H:%M:%S'))
        start_time_utc = start_time_ist.astimezone(utc)

        if end_time_ist_str:
            end_time_ist = ist.localize(datetime.strptime(end_time_ist_str, '%Y-%m-%d %H:%M:%S'))
        else:
            end_time_ist = datetime.now(ist)
        end_time_utc = end_time_ist.astimezone(utc)

        start_time_iso = start_time_utc.isoformat().replace('+00:00', 'Z')
        end_time_iso = end_time_utc.isoformat().replace('+00:00', 'Z')

    except Exception as e:
        logger.error(f"Error converting time: {e}")
        await params.result_callback({"error": f"Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'. Error: {e}"})
        return

    api_url = "https://portal.breeze.in/analytics/marketing"
    payload = {
        "shopIds": [shop_id],
        "shops": [shop_url],
        "startTime": start_time_iso,
        "endTime": end_time_iso,
        "shopType": shop_type
    }
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "x-auth-token": breeze_token
    }

    logger.info(f"Requesting Breeze marketing data with payload: {json.dumps(payload)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            logger.info(f"Received Breeze API response status: {response_json.get('statusCode')}")
            await params.result_callback(response_json.get("data", {"error": "No data field in response"}))

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Breeze Marketing API: {e.response.status_code} - {e.response.text}")
        await params.result_callback({"error": f"Breeze API error: {e.response.status_code}", "details": e.response.text})
    except Exception as e:
        logger.error(f"Unexpected error calling Breeze Marketing API: {e}")
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})


async def get_breeze_address_data(params: FunctionCallParams):
    """Fetches address-related analytics from the Breeze API."""
    if not all([breeze_token, shop_id, shop_url, shop_type]):
        logger.error("Breeze tool called without required context (token, shopId, shopUrl, shopType).")
        await params.result_callback({"error": "Breeze tool is not configured."})
        return

    start_time_ist_str = params.arguments.get("startTime")
    end_time_ist_str = params.arguments.get("endTime")

    if not start_time_ist_str:
        await params.result_callback({"error": "startTime is a required parameter."})
        return

    try:
        ist = pytz.timezone("Asia/Kolkata")
        utc = pytz.utc

        start_time_ist = ist.localize(datetime.strptime(start_time_ist_str, '%Y-%m-%d %H:%M:%S'))
        start_time_utc = start_time_ist.astimezone(utc)

        if end_time_ist_str:
            end_time_ist = ist.localize(datetime.strptime(end_time_ist_str, '%Y-%m-%d %H:%M:%S'))
        else:
            end_time_ist = datetime.now(ist)
        end_time_utc = end_time_ist.astimezone(utc)

        start_time_iso = start_time_utc.isoformat().replace('+00:00', 'Z')
        end_time_iso = end_time_utc.isoformat().replace('+00:00', 'Z')

    except Exception as e:
        logger.error(f"Error converting time: {e}")
        await params.result_callback({"error": f"Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'. Error: {e}"})
        return

    api_url = "https://portal.breeze.in/analytics/address"
    payload = {
        "shopIds": [shop_id],
        "shops": [shop_url],
        "startTime": start_time_iso,
        "endTime": end_time_iso,
    }
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "x-auth-token": breeze_token
    }

    logger.info(f"Requesting Breeze address data with payload: {json.dumps(payload)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            logger.info(f"Received Breeze API response status: {response_json.get('statusCode')}")
            await params.result_callback(response_json.get("data", {"error": "No data field in response"}))

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Breeze Address API: {e.response.status_code} - {e.response.text}")
        await params.result_callback({"error": f"Breeze API error: {e.response.status_code}", "details": e.response.text})
    except Exception as e:
        logger.error(f"Unexpected error calling Breeze Address API: {e}")
        await params.result_callback({"error": f"An unexpected error occurred: {e}"})


get_breeze_sales_data_function = FunctionSchema(
    name="get_breeze_sales_data",
    description="Fetches sales data (gross sales, net sales, discounts, shipping, tax, total sales) from Breeze analytics for a given shop and time range. Time should be provided in IST (e.g., '2025-06-20 00:00:00').",
    properties={
        "startTime": {
            "type": "string",
            "description": "The start time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. This is mandatory.",
        },
        "endTime": {
            "type": "string",
            "description": "The end time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. Defaults to the current time if not provided.",
        },
    },
    required=["startTime"],
)

get_breeze_orders_data_function = FunctionSchema(
    name="get_breeze_orders_data",
    description="Fetches order data (total orders, average order value, total sales) from Breeze analytics for a given shop and time range. Time should be provided in IST (e.g., '2025-06-20 00:00:00').",
    properties={
        "startTime": {
            "type": "string",
            "description": "The start time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. This is mandatory.",
        },
        "endTime": {
            "type": "string",
            "description": "The end time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. Defaults to the current time if not provided.",
        },
    },
    required=["startTime"],
)

get_breeze_checkout_data_function = FunctionSchema(
    name="get_breeze_checkout_data",
    description="Fetches checkout conversion funnel data (e.g., clicked checkout, logged in, placed order) from Breeze analytics for a given shop and time range. Time should be provided in IST (e.g., '2025-06-20 00:00:00').",
    properties={
        "startTime": {
            "type": "string",
            "description": "The start time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. This is mandatory.",
        },
        "endTime": {
            "type": "string",
            "description": "The end time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. Defaults to the current time if not provided.",
        },
    },
    required=["startTime"],
)

get_breeze_conversion_data_function = FunctionSchema(
    name="get_breeze_conversion_data",
    description="Fetches conversion rate data (total sessions, orders placed, conversion rate) from Breeze analytics for a given shop and time range. Time should be provided in IST (e.g., '2025-06-20 00:00:00').",
    properties={
        "startTime": {
            "type": "string",
            "description": "The start time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. This is mandatory.",
        },
        "endTime": {
            "type": "string",
            "description": "The end time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. Defaults to the current time if not provided.",
        },
    },
    required=["startTime"],
)

get_breeze_marketing_data_function = FunctionSchema(
    name="get_breeze_marketing_data",
    description="Fetches marketing attribution data (UTM source, medium, campaign, etc.) from Breeze analytics for a given shop and time range. Time should be provided in IST (e.g., '2025-06-20 00:00:00').",
    properties={
        "startTime": {
            "type": "string",
            "description": "The start time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. This is mandatory.",
        },
        "endTime": {
            "type": "string",
            "description": "The end time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. Defaults to the current time if not provided.",
        },
    },
    required=["startTime"],
)

get_breeze_address_data_function = FunctionSchema(
    name="get_breeze_address_data",
    description="Fetches address-related analytics (e.g., total logged-in users, users with prefilled addresses, address validation metrics) from Breeze analytics for a given shop and time range. Time should be provided in IST (e.g., '2025-06-20 00:00:00').",
    properties={
        "startTime": {
            "type": "string",
            "description": "The start time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. This is mandatory.",
        },
        "endTime": {
            "type": "string",
            "description": "The end time for the analysis in IST format 'YYYY-MM-DD HH:MM:SS'. Defaults to the current time if not provided.",
        },
    },
    required=["startTime"],
)


tools = ToolsSchema(
    standard_tools=[
        get_breeze_sales_data_function,
        get_breeze_orders_data_function,
        get_breeze_checkout_data_function,
        get_breeze_conversion_data_function,
        get_breeze_marketing_data_function,
        get_breeze_address_data_function,
    ]
)

tool_functions = {
    "get_breeze_sales_data": get_breeze_sales_data,
    "get_breeze_orders_data": get_breeze_orders_data,
    "get_breeze_checkout_data": get_breeze_checkout_data,
    "get_breeze_conversion_data": get_breeze_conversion_data,
    "get_breeze_marketing_data": get_breeze_marketing_data,
    "get_breeze_address_data": get_breeze_address_data,
}