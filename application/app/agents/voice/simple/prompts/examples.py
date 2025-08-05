"""
Example Prompts and Expected Responses for Voice-Synchronized Visualizations
"""

EXAMPLE_PROMPTS = {
    "sales_analysis": {
        "user_query": "Show me our monthly sales performance for the last 6 months and highlight the trends",
        "context_data": {
            "sales_data": [
                {"month": "July", "revenue": 85000, "units": 340, "growth": 12.5},
                {"month": "August", "revenue": 92000, "units": 380, "growth": 8.2},
                {"month": "September", "revenue": 78000, "units": 310, "growth": -15.2},
                {"month": "October", "revenue": 95000, "units": 400, "growth": 21.8},
                {"month": "November", "revenue": 103000, "units": 425, "growth": 8.4},
                {"month": "December", "revenue": 118000, "units": 480, "growth": 14.6}
            ],
            "period": "July - December 2024",
            "target": 100000
        },
        "expected_response": {
            "speechText": "Let me walk you through our sales performance over the last six months. We started July strong with $85,000 in revenue, showing solid momentum. August continued this upward trend, reaching $92,000. However, September presented a challenge, dipping to $78,000, which was our lowest point in this period. The good news is that October marked a remarkable recovery with $95,000, followed by November's impressive $103,000. December was our absolute best month, closing the year with $118,000 in revenue.",
            "speechMarkers": {
                "July": 4.2,
                "August": 8.1,
                "September": 11.8,
                "lowest point": 14.2,
                "October": 17.5,
                "November": 21.3,
                "December": 24.1,
                "absolute best": 25.8
            },
            "highlight_strategy": "Use green for growth months, red for September decline, blue pulse for December peak"
        }
    },
    
    "financial_dashboard": {
        "user_query": "Create a financial dashboard showing our key metrics and explain what they mean",
        "context_data": {
            "kpis": [
                {"name": "Revenue", "value": 2450000, "change": 18.5, "target": 2500000},
                {"name": "Gross Profit", "value": 1470000, "change": 22.1, "target": 1500000},
                {"name": "Operating Expenses", "value": 890000, "change": 12.3, "target": 850000},
                {"name": "Net Profit", "value": 580000, "change": 35.2, "target": 600000},
                {"name": "Cash Flow", "value": 720000, "change": 28.7, "target": 700000}
            ],
            "period": "Q4 2024",
            "comparison": "vs Q4 2023"
        },
        "expected_response": {
            "speechText": "Here's our comprehensive financial dashboard for Q4 2024. Our total revenue reached $2.45 million, representing an impressive 18.5% growth year-over-year. Gross profit margins improved significantly to $1.47 million, up 22.1%. While operating expenses increased to $890,000, this was a strategic investment in growth. The real highlight is our net profit of $580,000, showing remarkable 35% growth. Our cash flow position is particularly strong at $720,000, giving us excellent financial flexibility.",
            "speechMarkers": {
                "total revenue": 3.8,
                "impressive": 6.2,
                "gross profit": 9.1,
                "operating expenses": 13.4,
                "real highlight": 17.2,
                "net profit": 18.5,
                "cash flow": 22.8,
                "excellent financial flexibility": 26.1
            },
            "highlight_strategy": "Use metrics cards with zoom action for key achievements, pulse for standout performance"
        }
    },
    
    "market_share": {
        "user_query": "Analyze our market position compared to competitors",
        "context_data": {
            "market_share": [
                {"company": "Our Company", "share": 28.5, "growth": 5.2},
                {"company": "Competitor A", "share": 35.1, "growth": 2.1},
                {"company": "Competitor B", "share": 18.7, "growth": -1.8},
                {"company": "Competitor C", "share": 12.4, "growth": 3.5},
                {"company": "Others", "share": 5.3, "growth": -2.1}
            ],
            "total_market_size": "1.2B",
            "growth_rate": 8.3
        },
        "expected_response": {
            "speechText": "Let me show you our competitive position in the market. Currently, we hold 28.5% market share, making us the strong second player. The market leader, Competitor A, has 35.1% share, but here's what's exciting - our growth rate is 5.2% compared to their 2.1%. Competitor B holds 18.7% but is actually declining. Competitor C has 12.4% and is growing steadily. The remaining 5.3% is fragmented among smaller players. With the overall market growing at 8.3%, we're well-positioned to continue gaining ground.",
            "speechMarkers": {
                "28.5% market share": 4.1,
                "strong second": 6.8,
                "market leader": 8.9,
                "here's what's exciting": 12.3,
                "our growth rate": 13.8,
                "Competitor B": 17.2,
                "declining": 19.1,
                "well-positioned": 27.4
            },
            "highlight_strategy": "Use blue for our company, different colors for competitors, pulse for growth rates"
        }
    },
    
    "customer_satisfaction": {
        "user_query": "Show me customer satisfaction trends and what's driving the changes",
        "context_data": {
            "satisfaction_scores": [
                {"month": "Jan", "score": 7.2, "responses": 450},
                {"month": "Feb", "score": 7.5, "responses": 520},
                {"month": "Mar", "score": 7.1, "responses": 480},
                {"month": "Apr", "score": 7.8, "responses": 610},
                {"month": "May", "score": 8.1, "responses": 580},
                {"month": "Jun", "score": 8.4, "responses": 650}
            ],
            "key_drivers": [
                {"factor": "Product Quality", "impact": 32},
                {"factor": "Customer Service", "impact": 28},
                {"factor": "Delivery Time", "impact": 25},
                {"factor": "Pricing", "impact": 15}
            ]
        },
        "expected_response": {
            "speechText": "Our customer satisfaction journey shows a compelling upward trend. Starting at 7.2 in January, we saw improvement to 7.5 in February. March had a slight dip to 7.1, but then we began our strongest growth phase. April jumped to 7.8, May reached 8.1, and June achieved our highest score of 8.4. Looking at the key drivers, product quality accounts for 32% of satisfaction, customer service contributes 28%, delivery time impacts 25%, and pricing affects 15%.",
            "speechMarkers": {
                "7.2 in January": 4.5,
                "improvement": 6.8,
                "slight dip": 9.2,
                "strongest growth": 12.1,
                "April jumped": 13.8,
                "May reached": 15.6,
                "highest score": 17.2,
                "product quality": 20.8,
                "customer service": 23.1,
                "delivery time": 25.4
            },
            "highlight_strategy": "Use green gradient for trend improvement, focus action for the dip, zoom for peak"
        }
    }
}

PROMPT_ENHANCEMENT_GUIDELINES = {
    "timing_precision": {
        "rules": [
            "Space highlights at least 1.5 seconds apart",
            "Align timestamps with natural speech pauses",
            "Account for emphasis and inflection time",
            "Use speech markers for complex data mentions"
        ]
    },
    
    "color_strategy": {
        "performance": {
            "positive": "#51cf66",  # Green
            "negative": "#ff6b6b",  # Red
            "neutral": "#339af0",   # Blue
            "warning": "#ff922b"    # Orange
        },
        "categories": {
            "primary": "#667eea",   # Purple
            "secondary": "#20c997", # Teal
            "accent": "#845ef7",    # Deep purple
            "highlight": "#ffd43b"  # Yellow
        }
    },
    
    "action_guidelines": {
        "highlight": "For key data points and important values",
        "pulse": "For exceptional performance or attention-grabbing metrics",
        "zoom": "For peak values and record achievements", 
        "focus": "For problems, outliers, or areas needing attention",
        "reveal": "For progressive disclosure and storytelling"
    },
    
    "speech_patterns": {
        "opening": [
            "Let me show you...",
            "Here's what the data tells us...",
            "Looking at our performance...",
            "The numbers reveal..."
        ],
        "transitions": [
            "What's particularly interesting is...",
            "Notice how...",
            "Here's where it gets exciting...",
            "The real story is..."
        ],
        "emphasis": [
            "This is remarkable because...",
            "Pay attention to this...",
            "Here's the key insight...",
            "What stands out is..."
        ],
        "conclusions": [
            "In summary...",
            "The takeaway is...",
            "This suggests...",
            "Moving forward..."
        ]
    }
}

def get_example_by_type(example_type: str) -> dict:
    """Get example prompt and response by type."""
    return EXAMPLE_PROMPTS.get(example_type, {})

def get_all_example_types() -> list:
    """Get list of all available example types."""
    return list(EXAMPLE_PROMPTS.keys())

def generate_enhanced_prompt(base_query: str, context: dict, style: str = "conversational") -> str:
    """
    Generate an enhanced prompt using guidelines and examples.
    
    Args:
        base_query: User's base question
        context: Data context
        style: Presentation style (conversational, executive, technical)
    
    Returns:
        Enhanced prompt with style and timing guidance
    """
    
    style_instructions = {
        "conversational": "Use friendly, engaging language with natural transitions",
        "executive": "Use professional, concise language focusing on key insights",
        "technical": "Use precise terminology with detailed explanations"
    }
    
    enhanced_prompt = f"""
Create a voice-synchronized visualization response for the following request:

User Query: {base_query}
Data Context: {context}
Style: {style} - {style_instructions.get(style, "")}

Requirements:
1. Create engaging speech that naturally mentions data points
2. Use precise timing for highlights (minimum 1.5s spacing)
3. Choose appropriate colors based on data story
4. Include speech markers for complex references
5. Follow the established JSON response format

Color Guidelines:
- Positive trends/growth: #51cf66 (green)
- Negative trends/decline: #ff6b6b (red)  
- Neutral information: #339af0 (blue)
- Attention/warnings: #ff922b (orange)

Action Guidelines:
- highlight: Key data points and important values
- pulse: Exceptional performance or attention-grabbing metrics
- zoom: Peak values and record achievements
- focus: Problems, outliers, or areas needing attention
- reveal: Progressive disclosure and storytelling

Remember: Create a compelling narrative that brings data to life through synchronized visuals.
"""
    
    return enhanced_prompt.strip()